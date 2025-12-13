import os
import requests

from cs50 import SQL
from flask import Flask, jsonify, render_template, request, session

from datetime import datetime

from helpers import ICON, build_current_weather, build_hourly_forecast, build_daily_forecast

# Configure application
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Openweathermap API key (https://openweathermap.org/api)
# TODO: Move to environment variable for production, this is just for demo purposes will use my free tier
api_key = "0ef451aa617998b929aa1e094b1f157d"

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///cities.db")

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Context processors
@app.context_processor
def inject_globals():
    return {
        'ICON': ICON,           # Inject ICON mapping into templates
        'datetime': datetime    # Inject datetime module into templates
    }

# MAIN ROUTES
# Home page
@app.route("/")
def index():
    city = request.args.get("city")
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    
    # Validate coordinates if provided
    if lat and lon:
        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            return render_template("apology.html", message="Invalid coordinates")
    else:
        lat = None
        lon = None
    
    if not (lat and lon):
        if not city:
            city = session.get("city", "Bulawayo") # Nothing provided, use last or default
        
        coordinates, error = get_coordinates(city)
        if error:
            return render_template("apology.html", message=error)
        lat = coordinates[0]["lat"]
        lon = coordinates[0]["lon"]
    
    # Get current weather data
    weather_raw, error = get_current_weather(lat, lon)
    if error:
        return render_template("apology.html", message=error)
    
    weather = build_current_weather(weather_raw)
    
    if not city:
        city = weather.get("name", "Unknown Location") # Get city name from weather response if we don't have it
    
    session["city"] = city

    # Get daily forecast data
    daily_forecast_raw, error = get_daily_forecast(lat, lon)
    if error:
        return render_template("apology.html", message=error)
    
    daily_forecast = build_daily_forecast(daily_forecast_raw)

    # Get hourly forecast data 
    hourly_forecast_raw, error = get_hourly_forecast(lat, lon)
    if error:
        return render_template("apology.html", message=error)
    
    hourly_forecast = build_hourly_forecast(hourly_forecast_raw, daily_forecast_raw)  # Use daily forecast for sunrise/sunset times

    return render_template("index.html", city=city, weather=weather, hourly_forecast=hourly_forecast, daily_forecast=daily_forecast, active="weather")

# Cities page
@app.route("/cities")
def cities():
    return render_template("cities.html", active="cities")

# Settings page
@app.route("/settings")
def settings():
    return render_template("settings.html", active="settings")

# Get weather data
def get_current_weather(lat, lon, units="metric"):
    if not lat or not lon:
        return None, "City required"
    
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": api_key, "units": units}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None, "Unable to fetch weather data"

    data = response.json()
    if data.get("cod") != 200:
        return None, "City not found"
    
    return data, None

# Get hourly forecast data
def get_hourly_forecast(lat, lon, units="metric"):
    if not lat or not lon:
        return None, "Coordinates required"
    
    cnt = 24    # Number of hours to fetch
    url = "http://api.openweathermap.org/data/2.5/forecast/hourly"
    params = {"lat": lat, "lon": lon, "appid": api_key, "cnt": cnt, "units": units}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None, "Unable to fetch forecast data"
    
    data = response.json()
    if data.get("cod") != "200":
        return None, "City not found"
    
    return data, None

# Get daily forecast data
def get_daily_forecast(lat, lon, units="metric"):
    if not lat or not lon:
        return None, "Coordinates required"
    
    cnt = 7    # Number of days to fetch
    url = "http://api.openweathermap.org/data/2.5/forecast/daily"
    params = {"lat": lat, "lon": lon, "appid": api_key, "cnt": cnt, "units": units}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None, "Unable to fetch forecast data"
    
    data = response.json()
    if data.get("cod") != "200":
        return None, "City not found"
    
    return data, None

# Get coordinates from city name
def get_coordinates(city):
    if not city or city.strip() == "":
        return None, "City required"
    
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {"q": city, "limit": 1, "appid": api_key}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None, "Unable to fetch location data"
    
    data = response.json()
    if not data or len(data) == 0:
        return None, f"Coordinates for {city} not found"

    return data, None

# API ROUTES
# Search for city name from the database
@app.route("/api/cities")
def city_search():
    city = request.args.get("city", "").strip()
    limit = 10

    if not city:
        return jsonify([])

    results = db.execute("""
        SELECT cities.name, cities.lat, cities.lon, countries.name as country
        FROM cities
        JOIN countries ON cities.country = countries.code
        WHERE cities.name LIKE ?
        LIMIT ?
    """, f"{city}%", limit)

    return jsonify([{"name": row["name"], "lat": row["lat"], "lon": row["lon"], "country": row["country"]} for row in results])
