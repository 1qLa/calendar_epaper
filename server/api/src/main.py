from fastapi import FastAPI, Response
from src import create_png
from src import weather_forecast
from src import create_png_weekly
from src import create_today_png
from src import composer
from src import composer_week
from src.calendar_api import getEvents
import hashlib
from fastapi import Request, Response

import asyncio # 非同期処理のための標準ライブラリ
import json
import datetime

app = FastAPI() 

async def check_and_update_calendar_task():
    """
    5分おきにカレンダーの更新をチェックし、変更があれば画像を更新するタスク。
    """
    global last_events_json 
    last_events_json = None 
    
    while True:
        now = datetime.datetime.now()
        year = now.year
        month = now.month
        
        # 1. 現在のカレンダーデータを取得
        current_events = getEvents(year, month)

        # 2. 比較のためにデータをJSON文字列に変換
        current_events_json = json.dumps(current_events, sort_keys=True, ensure_ascii=False)

        # 3. 更新判定
        if last_events_json is None or current_events_json != last_events_json:
            print(f"[{now.strftime('%H:%M:%S')}] ⭕️更新あり - 画像を更新します。")
            # 画像生成関数を呼び出して画像を更新
            composer_week.get_dashboard_image() 
            
            last_events_json = current_events_json
        else:
            print(f"[{now.strftime('%H:%M:%S')}] ❌変更なし。")

        # 4. 5分間 (300秒) 待機
        await asyncio.sleep(300)

@app.on_event("startup")
async def startup_event():
    """
    FastAPIサーバー起動時に、監視タスクを開始する。
    """
    # check_and_update_calendar_task をバックグラウンドタスクとして実行
    asyncio.create_task(check_and_update_calendar_task())
    print("バックグラウンドでカレンダー監視タスクを開始しました。")
    
# 
@app.get("/dashboard")
def get_dashboard(request: Request):
    # 1. コンテンツ生成
    image_data = composer.get_dashboard_image()
    
    # 2. ETagの生成
    etag_hash = hashlib.sha256(image_data).hexdigest()
    
    # 3. クライアントからのキャッシュ情報確認
    client_etag = request.headers.get("if-none-match")
    
    # 4. 比較とレスポンス処理
    if client_etag == etag_hash:
        return Response(
            status_code=304, 
            headers={"ETag": etag_hash}
            )
    return Response(
        content=image_data, 
        media_type="image/png", 
        headers={"ETag": etag_hash}
    )

@app.get("/dashboard_week")
def get_dashboard_week(request: Request):
    image_data = composer_week.get_dashboard_image()
    
    etag_hash = hashlib.sha256(image_data).hexdigest()
    client_etag = request.headers.get("if-none-match")
    
    if client_etag == etag_hash:
        return Response(
            status_code=304, 
            headers={"ETag": etag_hash}
        )

    return Response(
        content=image_data, 
        media_type="image/png", 
        headers={"ETag": etag_hash}
    )
#デバック用****
@app.get("/")
def read_root():
    return {"message": "HelloWorld"}

@app.get("/message")
def read_message():
    return {"message": "正常に動作しています"}

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
