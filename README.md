# Vacation Helper

A small Flask web app that helps you compare trip destinations against a budget and a trip length. You enter an origin airport, a budget, and a number of nights. It ranks the destinations that fit and shows the math for each one, so you can check the reasoning instead of trusting a ranking.

Built as an individual project for HCDE 310 at the University of Washington.

## What is real and what is an estimate

- Flight and hotel prices are **estimates** stored in `destinations.csv`. They are not live prices.
- Current weather on each destination page comes from the **OpenWeatherMap API**. If no API key is set, the page still works and shows "Weather unavailable right now".

## Features

- Enter origin airport, budget, and number of nights
- See destinations that fit the budget, with the flight, hotel, and total cost for each
- Each result explains why it fits (for example, "estimated flight cost is $180 and hotel cost is $700")
- Click a destination for what it is best for, a short description, and current weather

Example: origin SEA, budget $1,200, 5 nights. Las Vegas shows a $180 flight plus a $700 hotel (5 nights at $140), for a total of $880, which fits.

## Run it locally

You need Python 3.9 or newer.

```bash
git clone https://github.com/Dev-0206/Vacation-Helper.git
cd Vacation-Helper

python -m venv venv
source venv/bin/activate        # on Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # then open .env and paste your OpenWeatherMap key
python app.py
```

Open http://127.0.0.1:5000 in your browser.

To get a free API key, make an account at openweathermap.org and copy a key from your account page. The key goes in `.env`, which is listed in `.gitignore` so it is never committed.

## Files

- `app.py`: routes, cost logic, and the weather request
- `destinations.csv`: destinations with estimated hotel and flight prices
- `templates/`: `index.html` (form), `results.html` (ranked options), `destination.html` (details and weather)
- `.env.example`: shows the one setting the app needs
- `requirements.txt`: Python dependencies

## Known limits and what I would do next

- Prices are estimates, so a real version needs live flight and hotel data.
- There is no preferences input yet (for example beach versus city).
- It runs locally only. It is not deployed.
