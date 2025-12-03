import requests

from cs50 import SQL
from flask import Flask, jsonify, render_template, request

# Configure application
app = Flask(__name__)

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


@app.route("/")
def index():
    q = request.args.get("q")

    if q is None:
        return render_template("welcome.html")

    if q == "error":
        return render_template("apology.html", top=404), 404

    if q == "":
        return render_template("index.html", location="")

    return render_template("index.html", location=q)


# Search for city name from the database
@app.route("/search")
def search():
    q = request.args.get("q")
    if q:
        city = db.execute("SELECT * FROM cities WHERE name LIKE ? LIMIT 6", "%" + q + "%")
    else:
        city = []
    return jsonify(city)


# Get weather data
@app.route("/weather")
def weather():
    city = request.args.get("q")
    if city:
        city = city.replace(" ", "%20")
        url = "http://api.openweathermap.org/data/2.5/weather?q=" + city + "&appid=" + api_key + "&units=metric"
        response = requests.get(url)
        data = response.json()
    else:
        data = []
    return jsonify(data)


# Get weather forecast
@app.route("/forecast")
def forecast():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    if lat and lon:
        url = "http://api.openweathermap.org/data/2.5/forecast?lat=" + lat + "&lon=" + lon + "&appid=" + api_key + "&units=metric&cnt=8"
        response = requests.get(url)
        data = response.json()
    else:
        data = []
    return jsonify(data)


# Get city name from coordinates
@app.route("/locate")
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
