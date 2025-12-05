from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Weather API", version="1.0.0")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for demo; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# A simple in-memory data store for demonstration
weather_data = {
    "london": {"city": "London", "temperature": 15.5, "humidity": 72, "conditions": "cloudy"},
    "paris": {"city": "Paris", "temperature": 18.2, "humidity": 65, "conditions": "sunny"},
    "tokyo": {"city": "Tokyo", "temperature": 25.0, "humidity": 80, "conditions": "rainy"},
    "new york": {"city": "New York", "temperature": 12.3, "humidity": 55, "conditions": "clear"},
    "sydney": {"city": "Sydney", "temperature": 28.7, "humidity": 60, "conditions": "sunny"},
    "berlin": {"city": "Berlin", "temperature": 10.5, "humidity": 68, "conditions": "cloudy"},
    "warsaw": {"city": "Warsaw", "temperature": 8.2, "humidity": 75, "conditions": "cloudy"},
    "madrid": {"city": "Madrid", "temperature": 22.0, "humidity": 45, "conditions": "sunny"},
    "rome": {"city": "Rome", "temperature": 20.5, "humidity": 55, "conditions": "sunny"},
    "amsterdam": {"city": "Amsterdam", "temperature": 12.0, "humidity": 78, "conditions": "rainy"},
    "moscow": {"city": "Moscow", "temperature": 2.5, "humidity": 82, "conditions": "cloudy"},
    "beijing": {"city": "Beijing", "temperature": 18.0, "humidity": 40, "conditions": "clear"},
    "dubai": {"city": "Dubai", "temperature": 35.0, "humidity": 30, "conditions": "sunny"},
    "singapore": {"city": "Singapore", "temperature": 30.5, "humidity": 85, "conditions": "rainy"},
    "los angeles": {"city": "Los Angeles", "temperature": 24.0, "humidity": 50, "conditions": "sunny"},
}

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/weather/{city}")
def get_weather(city: str):
    """
    Retrieves weather information for a given city.
    Returns mock weather data with temperature, humidity, and conditions.
    """
    city_lower = city.lower()
    if city_lower not in weather_data:
        raise HTTPException(status_code=404, detail=f"Weather data not found for city: {city}")
    return weather_data[city_lower]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)