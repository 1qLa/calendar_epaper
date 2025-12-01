from fastapi import FastAPI, Response
from src import create_png
from src import create_png_weekly
import io

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

@app.get("/weekData")
def read_week_data():
    return Response(content=create_png_weekly.create_calendar_image_week(), media_type="image/png")
