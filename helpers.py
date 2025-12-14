# helpers.py
from datetime import datetime, timezone, timedelta

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

# Build current weather data structure
def build_current_weather(weather):
    """Transforms raw current weather data into a structured format for templates."""
    return weather

# Build hourly forecast data structure
def build_hourly_forecast(hourly_forecast, daily_forecast):
    """Transforms raw hourly forecast data into a structured format with sunrise/sunset markers.
    
    Uses daily forecast data to get accurate sunrise/sunset times for each day.
    Example output structure
    items = [
        {
            "type": "hour",
            "time": "06:00",  # Local time (HH:MM format)
            "icon": "01d",    # OpenWeatherMap icon code
            "feels_like": 18, # Temperature rounded to integer
            "dt": 1702450800  # Unix timestamp (for reference/sorting)
        },
        {
            "type": "sunrise",
            "time": "06:42",  # Local sunrise time
            "dt": 1702453320  # Unix timestamp of sunrise
        },
        ... more hourly forecasts ...
        {
            "type": "sunset",
            "time": "17:23",  # Local sunset time
            "dt": 1702491780  # Unix timestamp of sunset
        },
        ... more hourly forecasts ...
    ]
    """
    timezone_offset = hourly_forecast["city"]["timezone"]  # seconds from UTC
    local_timezone = timezone(timedelta(seconds=timezone_offset))
    
    # Build lookup of sunrise/sunset times by date from daily forecast
    sunrise_sunset_by_date = {}
    for day in daily_forecast["list"]:
        day_date = datetime.fromtimestamp(day["dt"], tz=local_timezone).date()
        sunrise_sunset_by_date[day_date] = {
            "sunrise": day["sunrise"],
            "sunset": day["sunset"]
        }
    
    # Track which sunrise/sunset we've inserted for each date
    inserted_sunrise_dates = set()
    inserted_sunset_dates = set()
    
    # Get first hour to check if sunrise/sunset already passed
    first_hour = hourly_forecast["list"][0]["dt"]
    
    items = []
    
    for f in hourly_forecast["list"]:
        hour = f["dt"]
        hour_datetime = datetime.fromtimestamp(hour, tz=local_timezone)
        hour_date = hour_datetime.date()
        
        # Get sunrise/sunset for this date if available
        if hour_date in sunrise_sunset_by_date:
            sunrise = sunrise_sunset_by_date[hour_date]["sunrise"]
            sunset = sunrise_sunset_by_date[hour_date]["sunset"]
            
            # Insert sunrise if: not inserted yet, current hour passed it, and it's after forecast start
            if (hour_date not in inserted_sunrise_dates and 
                hour >= sunrise and 
                sunrise >= first_hour):
                items.append({
                    "type": "sunrise",
                    "time": datetime.fromtimestamp(sunrise, tz=local_timezone).strftime("%H:%M"),
                    "dt": sunrise
                })
                inserted_sunrise_dates.add(hour_date)
            
            # Insert sunset if: not inserted yet, current hour passed it, and it's after forecast start
            if (hour_date not in inserted_sunset_dates and 
                hour >= sunset and 
                sunset >= first_hour):
                items.append({
                    "type": "sunset",
                    "time": datetime.fromtimestamp(sunset, tz=local_timezone).strftime("%H:%M"),
                    "dt": sunset
                })
                inserted_sunset_dates.add(hour_date)
        
        # Add normal forecast hour
        items.append({
            "type": "hour",
            "time": hour_datetime.strftime("%H:%M"),
            "icon": f["weather"][0]["icon"],
            "feels_like": round(f["main"]["feels_like"]),
            "dt": hour
        })

    return items

# Build daily forecast data structure
def build_daily_forecast(forecast):
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
    timezone_offset = forecast["city"]["timezone"]  # seconds from UTC
    local_timezone = timezone(timedelta(seconds=timezone_offset))
    
    items = []
    today = datetime.now(tz=local_timezone).date()
    
    for f in forecast["list"]:
        forecast_date = datetime.fromtimestamp(f["dt"], tz=local_timezone).date()
        
        # Determine day label
        day_diff = (forecast_date - today).days
        if day_diff == 0:
            day_label = "Today"
        elif day_diff == 1:
            day_label = "Tomorrow"
        else:
            day_label = forecast_date.strftime("%A")  # Monday, Tuesday, etc.
        
        items.append({
            "day": day_label,
            "icon": f["weather"][0]["icon"],
            "description": f["weather"][0]["main"],  # "Sunny", "Cloudy", etc.
            "temp_max": round(f["temp"]["max"]),
            "temp_min": round(f["temp"]["min"]),
            "dt": f["dt"]
        })
    
    return items
