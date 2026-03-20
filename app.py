from flask import Flask, render_template, request
import csv
import requests

app = Flask(__name__)

API_KEY = "YOUR_OPENWEATHER_API_KEY_HERE"


def get_weather_for_city(city):
    try:
        url = "https://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": city,
            "appid": API_KEY,
            "units": "imperial"
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        print("WEATHER STATUS:", response.status_code)
        print("WEATHER DATA:", data)

        if response.status_code != 200:
            return None

        return {
            "temp": round(data["main"]["temp"]),
            "description": data["weather"][0]["description"].title()
        }

    except Exception as e:
        print("WEATHER ERROR:", e)
        return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/results", methods=["POST"])
def results():
    origin = request.form["origin"]
    budget = int(request.form["budget"])
    nights = int(request.form["nights"])

    results_list = []

    with open("destinations.csv", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            hotel_nightly = int(row["hotel_price"])
            hotel_total = hotel_nightly * nights
            flight_cost = int(row["sample_flight_price"])
            total_cost = flight_cost + hotel_total

            if total_cost <= budget:
                fit_label = "Fits budget"
            else:
                fit_label = "Over budget"

            reason = f"{fit_label} because estimated flight cost is ${flight_cost} and hotel cost is ${hotel_total}."

            results_list.append({
                "city": row["destination"],
                "airport": row["airport"],
                "flight": flight_cost,
                "hotel": hotel_total,
                "total": total_cost,
                "fit_label": fit_label,
                "reason": reason,
                "best_for": row["best_for"],
                "notes": row["notes"]
            })

    results_list.sort(key=lambda x: (x["total"] > budget, x["total"]))
    top_results = results_list[:5]

    return render_template(
        "results.html",
        results=top_results,
        origin=origin,
        budget=budget,
        nights=nights
    )


@app.route("/destination/<city>")
def destination_detail(city):
    with open("destinations.csv", newline="") as f:
        reader = csv.DictReader(f)

        for row in reader:
            if row["destination"] == city:
                weather = get_weather_for_city(city)
                return render_template(
                    "destination.html",
                    destination=row,
                    weather=weather
                )

    return "Destination not found"


if __name__ == "__main__":
    app.run(debug=True)