import os
import requests

from cs50 import SQL
from flask import Flask, jsonify, render_template, request, session

# Configure application
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Openweathermap API key (https://openweathermap.org/api)
api_key = "0ef451aa617998b929aa1e094b1f157d"

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///cities.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# MAIN ROUTES
@app.route("/")
def index():
    # TODO: Handle lat and lon parameters
    # TODO: error handling for geocoding
    
    # Resolve city parameter
    city = request.args.get("city")
    if city:
        session["city"] = city
    elif "city" in session:
        city = session["city"]
    else:
        city = "Bulawayo"
    
    coordinate = geocode(city)
    lat = coordinate[0]["lat"] if coordinate else None
    lon = coordinate[0]["lon"] if coordinate else None

    data, error = get_weather(lat, lon)
    if error:
        return render_template("apology.html", message=error)
    
    return render_template("index.html", city=city, weather=data, active="weather")


@app.route("/cities")
def cities():
    return render_template("cities.html", active="cities")


@app.route("/settings")
def settings():
    return render_template("settings.html", active="settings")


# Get weather data
def get_weather(lat, lon, units="metric"):
    if not lat or not lon:
        return None, "Please enter a city"
    
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": api_key, "units": units}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None, "Unable to fetch weather data"
    
    data = response.json()
    if data.get("cod") != 200:
        return None, "City not found"
    
    return data, None

# Get forecast data
def get_forecast(city, units="metric"):
    if not city or city.strip() == "":
        return None, "Please enter a city"
    
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {"q": city, "appid": api_key, "units": units}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None, "Unable to fetch forecast data"
    
    data = response.json()
    if data.get("cod") != "200":
        return None, f"City '{city}' not found"
    
    return data, None

# Get coordinates from city name
def geocode(city):
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {"q": city, "limit": 1, "appid": api_key}
    response = requests.get(url, params=params)
    data = response.json()

    return data

# Get city name from coordinates
def reverse_geocode(lat, lon):
    url = "http://api.openweathermap.org/geo/1.0/reverse"
    params = {"lat": lat, "lon": lon, "limit": 1, "appid": api_key}
    response = requests.get(url, params=params)
    data = response.json()

    return data


# OLD API ROUTES
# Get city name from coordinates
@app.route("/api/locate")
def locate():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if lat and lon:
        url = "http://api.openweathermap.org/geo/1.0/reverse?lat=" + lat + "&lon=" + lon + "&limit=1&appid=" + api_key
        response = requests.get(url)
        data = response.json()
    else:
        data = []
    return jsonify(data)


# API ROUTES
# Search for city name from the database
@app.route("/api/cities")
def city_search():
    city = request.args.get("city", "").strip()
    limit = request.args.get("limit", default=10, type=int)

    limit = min(max(limit, 1), 20)

    if not city:
        return jsonify([])

    results = db.execute("SELECT name FROM cities WHERE name LIKE ? LIMIT ?", f"%{city}%", limit)

    return jsonify([row["name"] for row in results])
