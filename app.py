"""Vacation Helper (v2 redesign).

Flights and hotels come from destinations.csv. They are ESTIMATES, not live prices.
Weather is the only live data (OpenWeatherMap). The class-submission version is preserved
in the git tag `class-submission`.
"""
import csv
import os
import time

import requests
from dotenv import load_dotenv
from urllib.parse import quote

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for

load_dotenv()

app = Flask(__name__)
BASE = os.path.dirname(os.path.abspath(__file__))

VIBES = [
    ("beach", "Beach"), ("city", "City"), ("outdoors", "Outdoors"), ("nightlife", "Nightlife"),
    ("food", "Food"), ("culture", "Culture"), ("warm", "Warm weather"), ("family", "Family"),
]
VIBE_LABEL = dict(VIBES)
MAX_BUDGET, MAX_NIGHTS = 20000, 30


def slugify(name):
    return name.lower().replace(" ", "-")


def load_destinations():
    with open(os.path.join(BASE, "destinations.csv"), newline="", encoding="utf-8") as fh:
        out = []
        for r in csv.DictReader(fh):
            out.append({
                "name": r["destination"],
                "slug": slugify(r["destination"]),
                "airport": r["airport"].upper(),
                "hotel": int(r["hotel_price"]),
                "flight": int(r["sample_flight_price"]),
                "best_for": r["best_for"],
                "notes": r["notes"],
                "vibes": [v for v in r["vibes"].split(",") if v],
            })
        return out


DESTINATIONS = load_destinations()
BY_SLUG = {d["slug"]: d for d in DESTINATIONS}


def parse_int(value, default, lo, hi):
    try:
        n = int(str(value).strip())
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, n))


def parse_trip(args):
    """Read and clamp the trip inputs so bad input never breaks a page."""
    origin = "".join(c for c in (args.get("origin") or "") if c.isalpha()).upper()[:3]
    return {
        "origin": origin,
        "budget": parse_int(args.get("budget"), 1500, 100, MAX_BUDGET),
        "nights": parse_int(args.get("nights"), 4, 1, MAX_NIGHTS),
        "vibes": [v for v in args.getlist("vibe") if v in VIBE_LABEL],
    }


def booking_links(d, origin):
    """Links to Google's own search pages, where real prices live. Nothing is booked here."""
    q = f"Flights from {origin} to {d['airport']}" if origin else f"Flights to {d['airport']}"
    return {
        "flights": "https://www.google.com/travel/flights?q=" + quote(q),
        "hotels": "https://www.google.com/travel/hotels/" + quote(d["name"]),
    }


def price(d, nights):
    total = d["flight"] + d["hotel"] * nights
    return {"total": total, "flight": d["flight"], "hotel_total": d["hotel"] * nights}


def build_results(trip):
    items = []
    for d in DESTINATIONS:
        if trip["origin"] and d["airport"] == trip["origin"]:
            continue  # you are already there
        p = price(d, trip["nights"])
        fits = p["total"] <= trip["budget"]
        items.append({**d, **p, "fits": fits,
                      "left": trip["budget"] - p["total"],
                      "pct": min(100, round(p["total"] / trip["budget"] * 100)),
                      "flight_pct": round(p["flight"] / p["total"] * 100)})
    items.sort(key=lambda x: (not x["fits"], x["total"]))
    return items


@app.context_processor
def inject():
    return {"VIBES": VIBES, "VIBE_LABEL": VIBE_LABEL, "MAX_BUDGET": MAX_BUDGET, "MAX_NIGHTS": MAX_NIGHTS}


@app.route("/")
def index():
    trip = parse_trip(request.args)
    data = [{"slug": d["slug"], "total1": d["flight"], "hotel": d["hotel"], "vibes": d["vibes"],
             "airport": d["airport"]} for d in DESTINATIONS]
    return render_template("index.html", trip=trip, data=data, scenes=[d["slug"] for d in DESTINATIONS])


@app.route("/results", methods=["GET", "POST"])
def results():
    args = request.form if request.method == "POST" else request.args
    trip = parse_trip(args)
    if request.method == "POST":  # keep the old form working, but give results a shareable URL
        params = {"origin": trip["origin"], "budget": trip["budget"], "nights": trip["nights"], "vibe": trip["vibes"]}
        return redirect(url_for("results", **params), code=303)
    items = build_results(trip)
    return render_template("results.html", trip=trip, items=items, fit_count=sum(i["fits"] for i in items))


@app.route("/destination/<slug>")
def destination(slug):
    d = BY_SLUG.get(slugify(slug.replace("%20", " ")))
    if not d:
        abort(404)
    trip = parse_trip(request.args)
    return render_template("destination.html", d=d, trip=trip, p=price(d, trip["nights"]), links=booking_links(d, trip["origin"]))


_weather_cache = {}


@app.route("/api/weather/<slug>")
def weather(slug):
    d = BY_SLUG.get(slug)
    if not d:
        abort(404)
    key = os.getenv("OPENWEATHER_API_KEY")
    if not key:
        return jsonify(error="no_key"), 200
    hit = _weather_cache.get(slug)
    if hit and time.time() - hit[0] < 600:
        return jsonify(hit[1])
    try:
        r = requests.get("https://api.openweathermap.org/data/2.5/weather",
                         params={"q": f"{d['name']},US", "appid": key, "units": "imperial"}, timeout=5)
        r.raise_for_status()
        j = r.json()
        out = {"temp": round(j["main"]["temp"]), "feels": round(j["main"]["feels_like"]),
               "desc": j["weather"][0]["description"].capitalize(), "humidity": j["main"]["humidity"],
               "wind": round(j["wind"]["speed"])}
    except (requests.RequestException, KeyError, ValueError):
        return jsonify(error="unavailable"), 200
    _weather_cache[slug] = (time.time(), out)
    return jsonify(out)


@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
