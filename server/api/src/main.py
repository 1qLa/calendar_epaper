from fastapi import FastAPI, Response
from src import create_png
<<<<<<< HEAD
from src import weather_forecast
=======
from src import create_png_weekly
from src import create_today_png

>>>>>>> feature/jump_branch
import io
import requests

app = FastAPI() 

@app.get("/")
def read_root():
    return {"message": "HelloWorld"}

@app.get("/message")
def read_message():
    return {"message": "正常に動作しています"}

@app.get("/monthData")
def read_data():
    return Response(content=create_png.create_calendar_image(), media_type="image/png")

<<<<<<< HEAD
@app.get("/weather")
def generate_weather():
    return Response(content=weather_forecast.generate_weatherInfo(), media_type="image/png")
=======
@app.get("/weekData")
def read_week_data():
    return Response(content=create_png_weekly.create_calendar_image_week(), media_type="image/png")

@app.get("/todayData")
def read_today_data():
    return Response(content=create_today_png.create_today_image(), media_type="image/png")
>>>>>>> feature/jump_branch
