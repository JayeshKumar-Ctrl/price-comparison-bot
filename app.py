from flask import Flask, render_template, request
import requests
import os
import traceback

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html", results=[])


@app.route("/search", methods=["GET", "POST"])
def search():

    try:

        # Get query
        if request.method == "POST":
            query = request.form.get("query")
        else:
            query = request.args.get("item")

        print("SEARCH:", query)

        if not query:
            return render_template(
                "index.html",
                results=[],
                error="Empty search"
            )

        API_KEY = os.environ.get("RAPIDAPI_KEY")

        print("API KEY:", API_KEY)

        if not API_KEY:
            return render_template(
                "index.html",
                results=[],
                error="API key missing"
            )

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

        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=20
        )

        print("STATUS:", response.status_code)
        print("TEXT:", response.text[:500])

        if response.status_code != 200:
            return render_template(
                "index.html",
                results=[],
                error="API failed"
            )

        data = response.json()

        print("JSON OK")

        products = data.get("data", {}).get("products", [])

        print("PRODUCT COUNT:", len(products))

        results = []

        for item in products:

            title = item.get("product_title")
            price_text = item.get("product_price")
            link = item.get("product_url")

            if not title or not price_text or not link:
                continue

            # Clean price
            price_text = price_text.replace("₹", "").replace(",", "").strip()

            try:
                price = int(price_text)
            except:
                continue

            results.append({
                "name": title,
                "price": price,
                "link": link,
                "site": "Amazon"
            })

            if len(results) >= 15:
                break

        print("FINAL RESULTS:", len(results))

        if not results:
            return render_template(
                "index.html",
                results=[],
                error="No products found"
            )

        results = sorted(results, key=lambda x: x["price"])

        return render_template(
            "index.html",
            results=results
        )

    except Exception as e:

        print("🔥 FULL ERROR 🔥")
        traceback.print_exc()

        return render_template(
            "index.html",
            results=[],
            error="Server error"
        )


if __name__ == "__main__":
    app.run(debug=True)

