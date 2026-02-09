import os
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# ==========================
# Config
# ==========================

RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")

API_URL = "https://real-time-amazon-data.p.rapidapi.com/search"


# ==========================
# Home Page
# ==========================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================
# Helper: Clean Title
# ==========================

def clean_title(title, max_len=80):
    """
    Shorten very long titles for UI
    """
    if len(title) > max_len:
        return title[:max_len] + "..."
    return title


# ==========================
# Helper: Relevance Check
# ==========================

def is_relevant(search, title):
    """
    Check if product matches search
    """
    search = search.lower()
    title = title.lower()

    words = search.split()

    score = 0

    for w in words:
        if w in title:
            score += 1

    return score >= 1


# ==========================
# Search Route
# ==========================

@app.route("/search")
def search():

    item = request.args.get("item")

    if not item:
        return jsonify({"error": "No item provided"}), 400

    print("SEARCH:", item)

    if not RAPIDAPI_KEY:
        print("ERROR: API KEY MISSING")
        return jsonify({"error": "Server config error"}), 500


    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
    }

    params = {
        "query": item,
        "country": "IN",
        "sort_by": "RELEVANCE",
        "page": 1
    }


    # ==========================
    # Call API
    # ==========================

    try:

        response = requests.get(
            API_URL,
            headers=headers,
            params=params,
            timeout=20
        )

    except Exception as e:

        print("REQUEST ERROR:", e)

        return jsonify({"error": "API request failed"}), 500


    print("STATUS:", response.status_code)


    if response.status_code != 200:

        print("BAD RESPONSE:", response.text)

        return jsonify({"error": "API failed"}), 500


    # ==========================
    # Parse JSON
    # ==========================

    try:
        data = response.json()

    except Exception as e:

        print("JSON ERROR:", e)

        return jsonify({"error": "Invalid API response"}), 500


    products = data.get("data", {}).get("products", [])


    if not products:
        return jsonify([])


    # ==========================
    # Build Results
    # ==========================

    results = []


    for p in products:

        title = p.get("product_title")
        price_text = p.get("product_price")
        link = p.get("product_url")

        if not title or not price_text:
            continue


        # Relevance filter
        if not is_relevant(item, title):
            continue


        # Clean price
        clean = price_text.replace("₹", "").replace(",", "").strip()

        try:
            price = int(clean)

        except:
            continue


        short_title = clean_title(title)


        results.append({
            "name": short_title,
            "price": price,
            "link": link,
            "site": "Amazon"
        })


        # Limit results
        if len(results) >= 20:
            break


    # ==========================
    # Sort by Cheapest
    # ==========================

    results.sort(key=lambda x: x["price"])


    print("FINAL RESULTS:", len(results))


    return jsonify(results)


# ==========================
# Run App (Render Ready)
# ==========================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )

