from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key_123"


# ================== ENV VARIABLES ==================

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")


# ================== LOG SYSTEM ==================

def save_log(msg):

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("logs.txt", "a") as f:
        f.write(f"[{time}] {msg}\n")


# ================== HOME ==================

@app.route("/")
def home():
    return render_template("index.html")


# ================== SIMPLE RELEVANCE ==================

def is_relevant(search, title):

    search = search.lower()
    title = title.lower()

    return search in title


# ================== SEARCH ==================

@app.route("/search", methods=["GET", "POST"])
def search():

    try:

        # Get query
        if request.method == "POST":
            query = request.form.get("query")
        else:
            query = request.args.get("item")

        if not query:
            return jsonify({"error": "Empty search"})

        print("QUERY:", query)

        # Check API key
        if not RAPIDAPI_KEY:
            return jsonify({"error": "API key missing"})

        # API URL
        url = "https://real-time-amazon-data.p.rapidapi.com/search"

        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
        }

        params = {
            "query": query,
            "page": "1",
            "country": "IN"
        }

        # Call API
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=20
        )

        print("STATUS:", response.status_code)

        if response.status_code != 200:
            print("RAW:", response.text)
            return jsonify({"error": "API failed"})

        data = response.json()

        products = data.get("data", {}).get("products", [])

        print("PRODUCT COUNT:", len(products))

        results = []

        # Process products
        for item in products[:20]:

            title = item.get("product_title", "")

            if not is_relevant(query, title):
                continue

            price = item.get("product_price")

            if not price:
                continue

            link = item.get("product_url", "#")

            results.append({
                "title": title,
                "price": price,
                "link": link,
                "store": "Amazon"
            })

        print("RESULTS:", results)

        if len(results) == 0:
            return jsonify({"error": "No products found"})

        save_log(f"Search: {query} ({len(results)} results)")

        return render_template("index.html", results=results)

    except Exception as e:

        print("ERROR:", e)

        return jsonify({
            "error": "Server error",
            "details": str(e)
        })


# ================== ADMIN ==================

@app.route("/admin")
def admin():

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    try:
        with open("logs.txt", "r") as f:
            logs = f.read()
    except:
        logs = "No logs found"

    return f"""
    <h2>Admin Panel</h2>
    <a href="/logout">Logout</a>
    <pre>{logs}</pre>
    """


# ================== LOGIN ==================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:

            session["logged_in"] = True
            save_log("Admin logged in")

            return redirect(url_for("admin"))

        else:
            return "Invalid credentials"

    return """
    <h2>Admin Login</h2>

    <form method="post">

        <input type="text" name="username" placeholder="Username" required><br><br>

        <input type="password" name="password" placeholder="Password" required><br><br>

        <button type="submit">Login</button>

    </form>
    """


# ================== LOGOUT ==================

@app.route("/logout")
def logout():

    session.pop("logged_in", None)

    save_log("Admin logged out")

    return redirect(url_for("login"))


# ================== RUN ==================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port, debug=False)

