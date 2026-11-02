import os
import requests

def get_weather(query):
    """
    Fetches the current weather based on the query or IP location.
    Returns a formatted string to be spoken by the bot.
    """
    try:
        # Find city name from query or use IP location
        city = None
        if 'in ' in query:
            parts = query.split('in ')
            if len(parts) > 1:
                city = parts[1].strip()
        
        if not city:
            try:
                ip_req = requests.get('https://ipinfo.io/json', timeout=5)
                city = ip_req.json().get('city', 'Delhi')
            except Exception:
                city = 'Delhi'

        api_key = os.getenv("WEATHER_API_KEY", "").strip()
        if not api_key:
            return "Weather service is not configured. Set WEATHER_API_KEY first."

        url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric"
        res = requests.get(url, timeout=5)
        data = res.json()
        
        if str(data.get("cod")) == "200":
            temp = data["list"][0]["main"]["temp"]
            weather_desc = data["list"][0]["weather"][0]["description"]
            return f"The current temperature in {city} is {temp} degree Celsius with {weather_desc}."
        else:
            return f"Sorry, I couldn't find weather for {city}."
    except Exception:
        return "Sorry, I couldn't fetch the weather right now."
