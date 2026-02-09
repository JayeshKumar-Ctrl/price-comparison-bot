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

    if request.method == "POST":
        query = request.form.get("query")
    else:
        query = request.args.get("item")

    if not query:
        return render_template("index.html", results=[], error="Empty search")

    API_KEY = os.environ.get("RAPIDAPI_KEY")

    url = "https://real-time-amazon-data.p.rapidapi.com/search"

    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
    }

    params = {
        "query": query,
        "page": "1",
        "country": "IN"
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=20
        )

        if response.status_code != 200:
            return render_template(
                "index.html",
                results=[],
                error="API Failed"
            )

        data = response.json()

        products = data.get("data", {}).get("products", [])

        results = []

        for item in products[:15]:

            title = item.get("product_title", "No title")
            price_text = item.get("product_price")
            link = item.get("product_url", "#")

            if not price_text:
                continue

            # Clean price: ₹1,23,456 → 123456
            price = price_text.replace("₹", "").replace(",", "").strip()

            try:
                price = int(price)
            except:
                continue

            results.append({
                "name": title,
                "price": price,
                "link": link,
                "site": "Amazon"
            })

        if not results:
            return render_template(
                "index.html",
                results=[],
                error="No products found"
            )

        # Sort by cheapest
        results = sorted(results, key=lambda x: x["price"])

        return render_template(
            "index.html",
            results=results
        )

    except Exception as e:

        print("SEARCH ERROR:", e)

        return render_template(
            "index.html",
            results=[],
            error="Server error"
        )


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

