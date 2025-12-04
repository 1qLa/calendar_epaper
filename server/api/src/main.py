from fastapi import FastAPI, Response
from src import create_png
from src import weather_forecast
import io
import requests

app = FastAPI() 

@app.get("/")
def read_root():
    return {"message": "HelloWorld"}

@app.get("/message")
def read_message():
    return {"message": "正常に動作しています"}

@app.get("/data")
def read_data():
    return Response(content=create_png.create_calendar_image(), media_type="image/png")

@app.get("/weather")
def generate_weather():
    return Response(content=weather_forecast.generate_weatherInfo(), media_type="image/png")
