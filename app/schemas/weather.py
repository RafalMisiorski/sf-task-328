from pydantic import BaseModel

class WeatherResponseSchema(BaseModel):
    city: str
    temperature: float
    unit: str
    description: str