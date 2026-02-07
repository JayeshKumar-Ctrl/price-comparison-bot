from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import requests
from datetime import datetime
from spellchecker import SpellChecker
import os
app = Flask(__name__)
spell = SpellChecker()
app.secret_key = "my_super_secret_key_123"

# PUT YOUR RAPIDAPI KEY HERE

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
API_KEY = ""
PRICER_API_KEY = ""
PRODUCT_SEARCH_KEY = ""
FLIPKART_API_KEY = ""



# ---------------- LOG SYSTEM ----------------

def save_log(message):

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open("logs.txt", "a") as file:
        file.write(f"[{time}] {message}\n")

#-----------------SPELL CHECK----------------------
def fix_spelling(text):

    words = text.split()

    corrected_words = []

    for word in words:

        corrected = spell.correction(word)

        if corrected:
            corrected_words.append(corrected)
        else:
            corrected_words.append(word)

    return " ".join(corrected_words)

# ---------------- AMAZON SEARCH ----------------

def search_amazon(product):

    url = "https://real-time-amazon-data.p.rapidapi.com/search"

    headers = {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
    }

    params = {
        "query": product,
        "page": "1",
        "country": "IN"
    }

    response = requests.get(url, headers=headers, params=params)

    return response.json()
#--------flipkart--------------------------
def search_flipkart(product):

    url = "https://real-time-flipkart-data2.p.rapidapi.com/product-search"

    headers = {
        "X-RapidAPI-Key": FLIPKART_API_KEY,
        "X-RapidAPI-Host": "real-time-flipkart-data2.p.rapidapi.com"
    }

    params = {
        "q": product,
        "page": "1",
        "sort_by": "RELEVANCE"
    }

    response = requests.get(url, headers=headers, params=params)

    return response.json()

#------------------TIMEPASS------------------

#-----------------PRICER------------------------

# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")

#---------------save_relevant-------------
def is_relevant(search, title):

    search = search.lower()
    title = title.lower()

    search_words = search.split()

    score = 0

    for word in search_words:

        if len(word) < 2:
            continue

        if word in title:
            score += 2

    if search in title:
        score += 3

    if score >= 2:
        return True

    return False

# ---------------- SEARCH ----------------
@app.route("/search", methods=["POST"])
def search():
    query = request.form.get("query")

    url = "https://real-time-product-search.p.rapidapi.com/search"

    headers = {
        "X-RapidAPI-Key": os.environ.get("RAPIDAPI_KEY"),
        "X-RapidAPI-Host": "real-time-product-search.p.rapidapi.com"
    }

    params = {
        "q": query,
        "country": "us",
        "language": "en"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
        data = response.json()

        print("FULL API RESPONSE:", data)

        # ✅ Correct path
        products = data.get("data", {}).get("products", [])

        results = []

        for item in products[:10]:

            title = item.get("product_title", "No Title")

            offer = item.get("offer", {})

            price = offer.get("price", "N/A")
            link = offer.get("offer_page_url", "#")
            store = offer.get("store_name", "Unknown")

            results.append({
                "title": title,
                "price": price,
                "link": link,
                "store": store
            })

        return render_template("index.html", results=results)

    except Exception as e:
        print("ERROR:", e)
        return render_template("index.html", results=[], error=str(e))

#------------admin panel------------------

@app.route("/admin")
def admin():

    if not session.get("logged_in"):
        return redirect(url_for("login"))

    try:
        with open("logs.txt", "r") as file:
            logs = file.read()
    except:
        logs = "No logs found"

    return f"""
    <h2>Admin Panel</h2>
    <a href='/logout'>Logout</a>
    <pre>{logs}</pre>
    """
#--------------LOGIN PAGE--------------
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
#---------------LOGOUT------------------
@app.route("/logout")
def logout():

    session.pop("logged_in", None)
    save_log("Admin logged out")

    return redirect(url_for("login"))


# ---------------- RUN ----------------

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port,debug=False)

