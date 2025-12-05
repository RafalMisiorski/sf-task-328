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