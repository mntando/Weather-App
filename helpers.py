# helpers.py
from datetime import datetime, timezone, timedelta
from flask import session

# Mapping OpenWeather icons to Basmilius icons
ICON = {
    "01d": "clear-day.svg",
    "01n": "clear-night.svg",
    
    "02d": "partly-cloudy-day.svg",
    "02n": "partly-cloudy-night.svg",
    
    "03d": "cloudy.svg",
    "03n": "cloudy.svg",
    
    "04d": "overcast.svg",
    "04n": "overcast.svg",
    
    "09d": "rain.svg",
    "09n": "rain.svg",
    
    "10d": "partly-cloudy-day-rain.svg",
    "10n": "partly-cloudy-night-rain.svg",
    
    "11d": "thunderstorms-day.svg",
    "11n": "thunderstorms-night.svg",
    
    "13d": "snow.svg",
    "13n": "snow.svg",
    
    "50d": "mist.svg",
    "50n": "mist.svg",
}

def update_session(city=None, units=None):
    """Update session with city info and units preferences.

    Args:
        city: dict with "name", "lat", "lon" keys, or None
        units: "metric" or "imperial", or None
    """
    # Update units if provided
    if units in ("metric", "imperial"):
        session["units"] = units

    # Update recent cities if city provided
    if city:
        if "cities" not in session:
            session["cities"] = []

        # Remove city if already in list (match by coordinates, not just name)
        session["cities"] = [
            c for c in session["cities"]
            if not (
                c.get("lat") == city.get("lat")
                and c.get("lon") == city.get("lon")
            )
        ]

        # Add to front of list
        session["cities"].insert(0, {
            "name": city.get("name"),
            "lat": city.get("lat"),
            "lon": city.get("lon")
        })

        # Keep only 5 most recent
        session["cities"] = session["cities"][:4]

        session.modified = True

# Build current weather data structure
def build_current_weather(weather_current, units="metric"):
    icon_file = ICON.get(weather_current["weather"][0]["icon"], "default.webp")

    local_time = datetime.fromtimestamp(
        weather_current["dt"] + weather_current["timezone"],
        tz=timezone.utc
    )

    wind_speed = weather_current["wind"]["speed"]
    if units == "metric":
        wind = f"{wind_speed * 3.6:.1f} km/h"
    else:
        wind = f"{wind_speed:.1f} mph"

    visibility = f"{weather_current['visibility'] / 1000:.0f} km"

    precip = weather_current.get("rain", {}).get("1h", 0)
    precip_unit = "mm/h" if units == "metric" else "in/h"

    return {
        "name": weather_current["name"],
        "local_time": local_time.strftime("%H:%M"),

        "temp": round(weather_current["main"]["temp"]),
        "temp_min": round(weather_current["main"]["temp_min"]),
        "temp_max": round(weather_current["main"]["temp_max"]),
        "feels_like": round(weather_current["main"]["feels_like"]),
        "description": weather_current["weather"][0]["description"].title(),

        "wind": wind,
        "humidity": f"{weather_current['main']['humidity']}%",
        "clouds": f"{weather_current['clouds']['all']}%",
        "precipitation": f"{precip} {precip_unit}",
        "visibility": visibility,

        "icon": f"/static/icons/svg-static/{icon_file}",
    }

# Build hourly forecast data structure
def build_hourly_forecast(forecast_hourly, forecast_daily=None):
    """Transforms raw forecast data into a structured hourly format.
    Sunrise/sunset markers are added only if daily_forecast is provided.
    """

    timezone_offset = forecast_hourly["city"]["timezone"]  # seconds from UTC
    local_timezone = timezone(timedelta(seconds=timezone_offset))

    items = []

    # ---------- OPTIONAL sunrise/sunset prep ----------
    sunrise_sunset_by_date = {}
    inserted_sunrise_dates = set()
    inserted_sunset_dates = set()

    if forecast_daily:
        for day in forecast_daily["list"]:
            day_date = datetime.fromtimestamp(
                day["dt"], tz=local_timezone
            ).date()
            sunrise_sunset_by_date[day_date] = {
                "sunrise": day["sunrise"],
                "sunset": day["sunset"]
            }

        first_hour = forecast_hourly["list"][0]["dt"]
    # --------------------------------------------------

    for f in forecast_hourly["list"]:
        hour = f["dt"]
        hour_datetime = datetime.fromtimestamp(hour, tz=local_timezone)
        hour_date = hour_datetime.date()

        # ---------- OPTIONAL sunrise/sunset insertion ----------
        if sunrise_sunset_by_date and hour_date in sunrise_sunset_by_date:
            sunrise = sunrise_sunset_by_date[hour_date]["sunrise"]
            sunset = sunrise_sunset_by_date[hour_date]["sunset"]

            if (
                hour_date not in inserted_sunrise_dates
                and hour >= sunrise
                and sunrise >= first_hour
            ):
                items.append({
                    "type": "sunrise",
                    "time": datetime.fromtimestamp(
                        sunrise, tz=local_timezone
                    ).strftime("%H:%M"),
                    "dt": sunrise
                })
                inserted_sunrise_dates.add(hour_date)

            if (
                hour_date not in inserted_sunset_dates
                and hour >= sunset
                and sunset >= first_hour
            ):
                items.append({
                    "type": "sunset",
                    "time": datetime.fromtimestamp(
                        sunset, tz=local_timezone
                    ).strftime("%H:%M"),
                    "dt": sunset
                })
                inserted_sunset_dates.add(hour_date)
        # ------------------------------------------------------

        # Normal forecast hour
        icon_file = ICON.get(f["weather"][0]["icon"], "default.webp")
        items.append({
            "type": "hour",
            "time": hour_datetime.strftime("%H:%M"),
            "icon": f"/static/icons/svg-static/{icon_file}",
            "feels_like": f"{round(f['main']['feels_like'])}°",
            "dt": hour
        })

    return items

# Build daily forecast data structure
def build_daily_forecast(forecast_daily):
    """Transforms raw daily forecast data into structured format.
    
    Example output:
    items = [
        {
            "day": "Today",           # or "Tomorrow", "Monday", etc.
            "icon": "01d",            # OpenWeatherMap icon code
            "description": "Sunny",   # Weather description
            "temp_max": 36,           # Max temp (rounded)
            "temp_min": 22,           # Min temp (rounded)
            "dt": 1702450800          # Unix timestamp
        },
        ...
    ]
    """
    timezone_offset = forecast_daily["city"]["timezone"]  # seconds from UTC
    local_timezone = timezone(timedelta(seconds=timezone_offset))
    
    items = []
    today = datetime.now(tz=local_timezone).date()
    
    for f in forecast_daily["list"]:
        forecast_date = datetime.fromtimestamp(f["dt"], tz=local_timezone).date()
        
        # Determine day label
        day_diff = (forecast_date - today).days
        if day_diff == 0:
            day_label = "Today"
        elif day_diff == 1:
            day_label = "Tomorrow"
        else:
            day_label = forecast_date.strftime("%A")  # Monday, Tuesday, etc.
        
        icon_file = ICON.get(f["weather"][0]["icon"], "default.webp")
        items.append({
            "day": day_label,
            "icon": f"/static/icons/svg-static/{icon_file}",
            "main": f["weather"][0]["main"],  # "Sunny", "Cloudy", etc.
            "description": f["weather"][0]["description"].title(),
            "temp_max": round(f["temp"]["max"]),
            "temp_min": round(f["temp"]["min"]),
            "dt": f["dt"]
        })
    
    return items
