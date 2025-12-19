import os
import requests
from cs50 import SQL
from flask import Flask, jsonify, render_template, request, session
from flask_caching import Cache

from helpers import update_session, build_current_weather, build_hourly_forecast, build_daily_forecast

# Configure application
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Openweathermap API key (https://openweathermap.org/api)
api_key = "0ef451aa617998b929aa1e094b1f157d"

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///cities.db")

# Cache handling
cache = Cache(app, config={'CACHE_TYPE': 'simple'})  # Use 'redis' for production

# Browser cache
@app.after_request
def after_request(response):
    """Set appropriate cache headers"""
    if request.method == 'GET':
        if request.path in ['/weather', '/cities']:
            response.headers["Cache-Control"] = "public, max-age=300"
        elif request.path == '/settings':
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    else:
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    
    return response


# MAIN ROUTES
# Home page
@app.route("/")
def index():
    city = request.args.get("city")
    lat = request.args.get("lat")
    lon = request.args.get("lon")

    units = request.args.get("units")
    if units not in ("metric", "imperial"):
        units = session.get("units", "metric")

    # Validate coordinates if provided
    if lat and lon:
        try:
            lat = float(lat)
            lon = float(lon)
        except (ValueError, TypeError):
            return render_template("apology.html", message="Invalid coordinates")
    else:
        lat = lon = None

    # Resolve location
    if not (lat and lon):
        if not city:
            cities = session.get("cities", [])
            if cities:
                city = cities[0]["name"]
                lat = cities[0]["lat"]
                lon = cities[0]["lon"]
            else:
                city = "Bulawayo"

        if not (lat and lon):
            coordinates, error = get_coordinates(city)
            if error:
                return render_template("apology.html", message=error)
            lat = coordinates[0]["lat"]
            lon = coordinates[0]["lon"]

    # Fetch weather
    weather_current_raw, error = get_current_weather(lat, lon, units=units)
    if error:
        return render_template("apology.html", message=error)

    weather_current = build_current_weather(weather_current_raw, units=units)

    # Get daily forecast data
    forecast_daily_raw, error = get_daily_forecast(lat, lon, units=units)
    if error:
        return render_template("apology.html", message=error)
    
    forecast_daily = build_daily_forecast(forecast_daily_raw)

    # Get hourly forecast data 
    forecast_hourly_raw, error = get_hourly_forecast(lat, lon, units=units)
    if error:
        return render_template("apology.html", message=error)
    
    forecast_hourly = build_hourly_forecast(forecast_hourly_raw, forecast_daily=forecast_daily_raw)  # Use daily forecast for sunrise/sunset times

    # City name fallback
    if not city:
        city = weather_current.get("name", "Unknown Location")

    # Update session (single source of truth)
    update_session(
        city={"name": city, "lat": lat, "lon": lon},
    )

    return render_template(
        "index.html",
        city=city,
        weather_current=weather_current,
        forecast_hourly=forecast_hourly,
        forecast_daily=forecast_daily,
        active="weather"
    )


# Cities page
@app.route("/cities")
def cities():
    units = request.args.get("units")
    if units not in ("metric", "imperial"):
        units = session.get("units", "metric")

    recent = session.get("cities", [])
    weather_cards = []

    for city in recent:
        weather_current_raw, error = get_current_weather(city["lat"], city["lon"], units=units)
        if error:
            continue

        forecast_3hour_raw, error = get_3hour_forecast(city["lat"], city["lon"], units=units, blocks=5)
        if error:
            continue

        forecast_daily_raw, error = get_daily_forecast(city["lat"], city["lon"], units=units, days=3)
        if error:
            continue

        weather_cards.append({
            "city": city,
            "weather_current": build_current_weather(weather_current_raw),
            "forecast_3hour": build_hourly_forecast(forecast_3hour_raw),
            "forecast_daily": build_daily_forecast(forecast_daily_raw)
        })

    return render_template(
        "cities.html",
        cities=weather_cards,
        active="cities"
    )


# Settings page
@app.route("/settings")
def settings():
    units = request.args.get("units")
    if units not in ("metric", "imperial"):
        units = session.get("units", "metric")

    update_session(units=units)

    return render_template("settings.html", units=units, active="settings")


# HELPER FUNCTIONS
# Get weather data
def get_current_weather(lat, lon, units="metric"):
    if lat is None or lon is None:
        return None, "City required"
    
    cache_key = f'weather:current:{lat}:{lon}:{units}'
    # Try to get from cache first
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data, None
    
    # Cache miss - fetch from API
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"lat": lat, "lon": lon, "appid": api_key, "units": units}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None, "Unable to fetch weather data"

    data = response.json()
    if data.get("cod") != 200:
        return None, "City not found"
    
    # Store in cache for 5 minutes
    cache.set(cache_key, data, timeout=300)
    
    return data, None

# Get hourly forecast data
def get_hourly_forecast(lat, lon, units="metric", hours=24):
    """
    Fetches hourly weather forecast data from OpenWeatherMap.

    Args:
        lat (float): Latitude of the location
        lon (float): Longitude of the location
        units (str): Unit system ("metric" or "imperial")
        hours (int): Number of forecast hours to return
    """
    if lat is None or lon is None:
        return None, "Coordinates required"
    
    cache_key = f'forecast:hourly:{lat}:{lon}:{units}:{hours}'
    # Try to get from cache first
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data, None
    
    # Cache miss - fetch from API
    url = "http://api.openweathermap.org/data/2.5/forecast/hourly"
    params = {"lat": lat, "lon": lon, "appid": api_key, "cnt": hours, "units": units}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None, "Unable to fetch forecast data"
    
    data = response.json()
    if data.get("cod") != "200":
        return None, "City not found"
    
    # Store in cache for 30 minutes
    cache.set(cache_key, data, timeout=1800)
    
    return data, None

# Get daily forecast data
def get_daily_forecast(lat, lon, units="metric", days=7):
    """
    Fetches daily weather forecast data from OpenWeatherMap.

    Args:
        lat (float): Latitude of the location
        lon (float): Longitude of the location
        units (str): Unit system ("metric" or "imperial")
        days (int): Number of forecast days to return
    """
    if lat is None or lon is None:
        return None, "Coordinates required"
    
    cache_key = f'forecast:daily:{lat}:{lon}:{units}:{days}'
    # Try to get from cache first
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data, None
    
    # Cache miss - fetch from API
    url = "http://api.openweathermap.org/data/2.5/forecast/daily"
    params = {"lat": lat, "lon": lon, "appid": api_key, "cnt": days, "units": units}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None, "Unable to fetch forecast data"
    
    data = response.json()
    if data.get("cod") != "200":
        return None, "City not found"
    
    # Store in cache for 3 hours
    cache.set(cache_key, data, timeout=10800)
    
    return data, None

# Get 3-hour forecast data
def get_3hour_forecast(lat, lon, units="metric", blocks=5):
    """
    Fetches 3-hour weather forecast data from OpenWeatherMap.

    Args:
        lat (float): Latitude of the location
        lon (float): Longitude of the location
        units (str): Unit system ("metric" or "imperial")
        blocks (int): Number of forecast blocks to return
    """

    if lat is None or lon is None:
        return None, "Coordinates required"
    
    cache_key = f'forecast:3hour:{lat}:{lon}:{units}:{blocks}'
    # Try to get from cache first
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data, None
    
    # Cache miss - fetch from API    
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {"lat": lat, "lon": lon, "appid": api_key, "cnt": blocks, "units": units}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        return None, "Unable to fetch forecast data"
    
    data = response.json()
    if data.get("cod") != "200":
        return None, "City not found"
    
    # Store in cache for 1 hours
    cache.set(cache_key, data, timeout=3600)
    
    return data, None

# Get coordinates using city name
def get_coordinates(city):
    if not city or city.strip() == "":
        return None, "City required"
    
    city = city.strip().lower()
    cache_key = f'geo:coordinates:{city}'
    
    # Try cache first
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data, None
    
    # Cache miss - fetch from API
    url = "http://api.openweathermap.org/geo/1.0/direct"
    params = {"q": city, "limit": 1, "appid": api_key}
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        return None, "Unable to fetch location data"
    
    data = response.json()
    if not data or len(data) == 0:
        return None, f"Coordinates for {city} not found"
    
    # Cache for 30 days
    cache.set(cache_key, data, timeout=2592000)
    return data, None


# API ROUTES
# Search for city name from the database
@app.route("/api/cities")
def city_search():
    city = request.args.get("city", "").strip()
    if not city:
        return jsonify([])
    
    limit = 10
    results = db.execute("""
        SELECT
            cities.name,
            cities.lat,
            cities.lon,
            cities.state,
            countries.name AS country
        FROM cities
        JOIN countries ON cities.country = countries.code
        WHERE cities.name LIKE ?
        ORDER BY
            LENGTH(cities.name) ASC,
            cities.name ASC
        LIMIT ?
    """, f"{city}%", limit)

    return jsonify([
        {
            "name": row["name"],
            "lat": row["lat"],
            "lon": row["lon"],
            "state": row["state"],
            "country": row["country"]
        }
        for row in results
    ])
