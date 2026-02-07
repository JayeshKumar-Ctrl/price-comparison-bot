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

    search = search.lower().strip()
    title = title.lower().strip()

    search_words = search.split()
    title_words = title.split()

    score = 0

    # Direct word match
    for word in search_words:

        if len(word) < 2:
            continue

        if word in title:
            score += 3


    # Partial match (iphone → ipho, lap → lapt)
    for s_word in search_words:

        for t_word in title_words:

            if len(s_word) >= 3 and len(t_word) >= 3:
                if s_word[:3] == t_word[:3]:
                    score += 1


    # Brand / category match
    common_words = [
        "iphone", "samsung", "oneplus", "nokia", "redmi",
        "laptop", "notebook", "hp", "dell", "lenovo", "asus",
        "mobile", "phone", "smartphone",
        "nike", "adidas", "puma", "shoes"
    ]

    for word in common_words:

        if word in search and word in title:
            score += 2


    # Final decision
    if score >= 2:
        return True

    return False

# ---------------- SEARCH ----------------
@app.route("/search")
def search():

    item = request.args.get("item")

    if not item:
        return jsonify({"error": "No item provided"})


    url = "https://real-time-product-search.p.rapidapi.com/search-v2"

    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "https://real-time-product-search.p.rapidapi.com/search-v2"
    }


    try:
        response = requests.get(url, headers=headers, params={"q": item}, timeout=15)
        data = response.json()

    except Exception as e:
        return jsonify({"error": str(e)})


    # DEBUG (very important)
    print("FULL API RESPONSE:", data)


    # Try to extract products safely (works with most APIs)

    products = []

    if isinstance(data, dict):

        if "products" in data:
            products = data["products"]

        elif "data" in data and "products" in data["data"]:
            products = data["data"]["products"]

        elif "results" in data:
            products = data["results"]

        elif "items" in data:
            products = data["items"]


    if not products:
        return jsonify({"error": "No products from API"})


    results = []


    for product in products:

        title = (
            product.get("title")
            or product.get("name")
            or product.get("product_title")
            or ""
        )


        if not title:
            continue


        # Relevance filter
        if not is_relevant(item, title):
            continue


        # Price handling
        price_text = (
            product.get("price")
            or product.get("price_value")
            or product.get("sale_price")
        )


        if not price_text:
            continue


        try:
            clean = str(price_text).replace("₹", "").replace(",", "").strip()
            price = int(float(clean))

        except:
            continue


        link = (
            product.get("url")
            or product.get("link")
            or product.get("product_url")
            or ""
        )


        site = product.get("source") or "Online Store"


        results.append({
            "name": title,
            "price": price,
            "link": link,
            "site": site
        })


    # Final check
    if not results:
        return jsonify({"error": "No relevant product found"})


    # Sort by cheapest
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

