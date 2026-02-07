from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import requests
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key_123"


# ================= ENV VARIABLES =================

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


# ================= LOG SYSTEM =================

def save_log(msg):
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("logs.txt", "a") as f:
        f.write(f"[{time}] {msg}\n")


# ================= RELEVANCE CHECK =================

def is_relevant(search, title):

    search = search.lower().strip()
    title = title.lower().strip()

    search_words = search.split()

    score = 0

    for word in search_words:

        if len(word) < 2:
            continue

        if word in title:
            score += 2

    if search in title:
        score += 3

    return score >= 2


# ================= AMAZON SEARCH =================

def search_products(query):

    url = "https://real-time-product-search.p.rapidapi.com/search"

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "real-time-product-search.p.rapidapi.com"
    }

    params = {
        "q": query,
        "country": "in",
        "language": "en"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=20
    )

    print("STATUS:", response.status_code)
    print("RAW:", response.text)

    return response.json()


# ================= HOME =================

@app.route("/")
def home():
    return render_template("index.html", results=[])


# ================= SEARCH =================

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

        print("SEARCH:", query)

        # API URL
        url = "https://real-time-product-search.p.rapidapi.com/search"

        headers = {
            "X-RapidAPI-Key": os.environ.get("RAPIDAPI_KEY"),
            "X-RapidAPI-Host": "real-time-product-search.p.rapidapi.com"
        }

        params = {
            "q": query,
            "country": "in",
            "language": "en"
        }

        # Call API
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=20
        )

        print("STATUS:", response.status_code)
        print("TEXT:", response.text)

        # Check response
        if response.status_code != 200:
            return jsonify({"error": "API failed"})

        data = response.json()

        print("FULL RESPONSE:", data)

        # Get products safely
        products = []

        if "data" in data and "products" in data["data"]:
            products = data["data"]["products"]

        elif "products" in data:
            products = data["products"]

        elif "results" in data:
            products = data["results"]

        print("TOTAL PRODUCTS:", len(products))

        results = []

        for item in products[:20]:

            title = item.get("product_title") or item.get("title") or "No title"

            offer = item.get("offer", {})

            price = offer.get("price") or item.get("price")

            if not price:
                continue

            link = offer.get("offer_page_url") or item.get("link", "#")

            store = offer.get("store_name") or item.get("source", "Unknown")

            # Relevance filter
            if not is_relevant(query, title):
                continue

            results.append({
                "title": title,
                "price": price,
                "link": link,
                "store": store
            })

        print("FINAL:", results)

        if len(results) == 0:
            return jsonify({"error": "No relevant products found"})

        return render_template("index.html", results=results)

    except Exception as e:

        print("ERROR:", str(e))

        return jsonify({
            "error": "Backend crash",
            "details": str(e)
        })


# ================= ADMIN =================

@app.route("/admin")
def admin():

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    try:
        with open("logs.txt") as f:
            logs = f.read()
    except:
        logs = "No logs found"

    return f"""
    <h2>Admin Panel</h2>
    <a href="/logout">Logout</a>
    <pre>{logs}</pre>
    """


# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        user = request.form.get("username")
        pwd = request.form.get("password")

        if user == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:

            session["logged_in"] = True
            save_log("Admin login")

            return redirect(url_for("admin"))

        return "Invalid credentials"


    return """
    <h2>Login</h2>

    <form method="post">

    <input name="username" required><br><br>

    <input type="password" name="password" required><br><br>

    <button>Login</button>

    </form>
    """


# ================= LOGOUT =================

@app.route("/logout")
def logout():

    session.pop("logged_in", None)

    save_log("Admin logout")

    return redirect(url_for("login"))


# ================= RUN =================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )

