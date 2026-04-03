# Weather Storyteller - Task 2
# Fetch current weather data for your city using OpenWeatherMap API

import requests

def get_weather(city, api_key):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": api_key,
        "units": "metric"  # Get temperature in Celsius
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print("Error fetching weather data:", response.status_code, response.text)
        return None

if __name__ == "__main__":
    # Replace with your own city and API key
    city = "Kolkata"
    api_key = "YOUR_API_KEY_HERE"
    
    weather_data = get_weather(city, api_key)
    if weather_data:
        print(f"Current weather in {city}:")
        print(f"Temperature: {weather_data['main']['temp']}°C")
        print(f"Weather: {weather_data['weather'][0]['description']}")
