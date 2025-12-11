from fastapi import FastAPI, Response, Request
from src import cache_manager 
import asyncio

# デバッグ用import
from src import create_png, weather_forecast, create_png_weekly, create_today_png

app = FastAPI() 

@app.on_event("startup")
async def startup_event():
    # サーバー起動時に監視タスクを開始
    asyncio.create_task(cache_manager.update_cache_task())

# 本番用エンドポイント

@app.get("/dashboard")
def get_dashboard(request: Request):
    # マネージャーから「現在の最新画像」をもらう
    image_data, etag_hash = cache_manager.get_cached_data(mode="month")
    
    # 
    client_etag = request.headers.get("if-none-match")
    
    # 同じなら(304)を返す 
    if client_etag == etag_hash:
        return Response(status_code=304, headers={"ETag": etag_hash})
    
    #  違うなら画像を返す
    return Response(
        content=image_data, 
        media_type="image/png", 
        headers={"ETag": etag_hash}
    )

@app.get("/dashboard_week")
def get_dashboard_week(request: Request):
    # 週間カレンダーも同じ仕組み
    image_data, etag_hash = cache_manager.get_cached_data(mode="week")
    
    client_etag = request.headers.get("if-none-match")
    
    if client_etag == etag_hash:
        return Response(status_code=304, headers={"ETag": etag_hash})

    return Response(
        content=image_data, 
        media_type="image/png", 
        headers={"ETag": etag_hash}
    )


# デバッグ用 ---------------

@app.get("/")
def read_root():
    return {"message": "HelloWorld"}

@app.get("/monthData")
def read_data():
    return Response(content=create_png.create_calendar_image(), media_type="image/png")

@app.get("/weather")
def generate_weather():
    return Response(content=weather_forecast.generate_weatherInfo(), media_type="image/png")

@app.get("/weekData")
def read_week_data():
    return Response(content=create_png_weekly.create_calendar_image_week(), media_type="image/png")

@app.get("/todayData")
def read_today_data():
    return Response(content=create_today_png.create_today_image(), media_type="image/png")