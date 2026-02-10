import os
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# Get API key from environment
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/search")
def search():

    item = request.args.get("item")

    if not item:
        return jsonify({"error": "No item provided"}), 400

    print("SEARCH:", item)
    print("API KEY:", RAPIDAPI_KEY)

    url = "https://real-time-amazon-data.p.rapidapi.com/search"

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

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=20
        )
    except Exception as e:
        print("REQUEST ERROR:", e)
        return jsonify({"error": "API request failed"}), 500

    print("STATUS:", response.status_code)

    if response.status_code != 200:
        return jsonify({"error": "API failed"}), 500

    try:
        data = response.json()
    except Exception as e:
        print("JSON ERROR:", e)
        return jsonify({"error": "Invalid API response"}), 500

    print("FULL JSON:", data)

    products = data.get("data", {}).get("products", [])

    results = []

    for p in products[:20]:

        title = p.get("product_title")
        price_text = p.get("product_price")
        link = p.get("product_url")

        if not title or not price_text:
            continue

        # Clean price
        clean = price_text.replace("₹", "").replace(",", "").strip()

        try:
            price = int(clean)
        except:
            continue

        results.append({
            "name": title,
            "price": price,
            "link": link,
            "site": "Amazon"
        })

    print("RESULT COUNT:", len(results))

    return jsonify(results)


# ======================
# Render Port Binding
# ======================

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )

