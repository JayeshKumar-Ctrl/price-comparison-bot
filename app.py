import os
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# API Key
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY")

if not RAPIDAPI_KEY:
    print("WARNING: API Key not found!")


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/search")
def search():

    item = request.args.get("item")

    if not item:
        return jsonify({"error": "Please enter product name"}), 400

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
            timeout=15
        )

    except requests.exceptions.RequestException as e:
        print("API ERROR:", e)
        return jsonify({"error": "Network problem"}), 500


    if response.status_code != 200:
        print("STATUS ERROR:", response.status_code)
        return jsonify({"error": "API service unavailable"}), 500


    try:
        data = response.json()
    except:
        return jsonify({"error": "Invalid response format"}), 500


    products = data.get("data", {}).get("products", [])

    if not products:
        return jsonify({"error": "No products found"}), 404


    results = []

    for p in products[:15]:

        title = p.get("product_title")
        price_text = p.get("product_price")
        link = p.get("product_url")

        if not title or not price_text:
            continue


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


    return jsonify(results)



if __name__ == "__main__":

    port = int(os.environ.get("PORT", 10000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )

