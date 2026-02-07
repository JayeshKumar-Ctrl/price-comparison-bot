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

    if not search or not title:
        return False

    search = search.lower().strip()
    title = title.lower().strip()

    search_words = search.split()
    title_words = title.split()

    score = 0

    # Direct match
    for word in search_words:

        if len(word) < 3:
            continue

        if word in title:
            score += 3   # Strong match


    # Partial match (prefix)
    for s_word in search_words:

        for t_word in title_words:

            if len(s_word) >= 3 and t_word.startswith(s_word[:3]):
                score += 1


    # Fallback: whole search in title
    if search in title:
        score += 3


    # Accept if score >= 2
    return score >= 2

# ---------------- SEARCH ----------------
@app.route("/search")
def search():

    raw_item = request.args.get("item")

    save_log(f"Search: {raw_item}")

    if not raw_item or len(raw_item.strip()) < 2:
        return jsonify({"error": "Please enter valid product name"})


    # AI Spell Correction
    item = fix_spelling(raw_item)

    save_log(f"Corrected: {raw_item} -> {item}")

    results = []


    # ---------------- AMAZON ----------------
    try:
        amazon_data = search_amazon(item)
    except:
        amazon_data = {}


    if "data" in amazon_data and "products" in amazon_data["data"]:

        for product in amazon_data["data"]["products"][:10]:

            title = product.get("product_title", "")

            if not title:
                continue


            # Relevance filter
            if not is_relevant(item, title):
                continue


            price_text = product.get("product_price")

            if not price_text:
                continue


            clean = price_text.replace("₹", "").replace(",", "").strip()

            try:
                price = int(clean)
            except:
                continue


            results.append({
                "name": title,
                "price": price,
                "link": product.get("product_url", ""),
                "site": "Amazon"
            })


    # ---------------- FLIPKART (Optional) ----------------
    try:
        flip_data = search_flipkart(item)
    except:
        flip_data = {}


    if "data" in flip_data and "products" in flip_data["data"]:

        for product in flip_data["data"]["products"][:10]:

            title = product.get("title", "")

            if not title:
                continue


            # Relevance filter
            if not is_relevant(item, title):
                continue


            price_text = product.get("price")

            if not price_text:
                continue


            clean = price_text.replace("₹", "").replace(",", "").strip()

            try:
                price = int(clean)
            except:
                continue


            results.append({
                "name": title,
                "price": price,
                "link": product.get("url", ""),
                "site": "Flipkart"
            })


    # ---------------- FINAL ----------------
    if len(results) == 0:
        return jsonify({"error": "No relevant product found"})


    # Sort cheapest first
    results = sorted(results, key=lambda x: x["price"])


    save_log(f"Search success: {item} ({len(results)} results)")


    return jsonify(results)


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

