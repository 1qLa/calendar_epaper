import asyncio
import datetime
import json
import hashlib
from src import composer, composer_week
from src.calendar_api import getEvents

# グローバル変数としてキャッシュを保持
image_cache = {}

last_events_json = None
last_update_time = None  # 最後に画像を更新した時間

# カレンダーに変更がなくても、天気更新のために画像を更新する間隔（分）
FORCE_UPDATE_MINUTES = 30 

# ********** 関数エリア *********
#☆☆☆ カレンダー監視＆キャッシュ更新タスク ☆☆☆☆
# cache_manager.py

# ... (インポート等はそのまま) ...

async def update_cache_task():
    global last_events_json, image_cache, last_update_time

    while True:
        try:
            now = datetime.datetime.now()
            year, month = now.year, now.month # 今日の年月を取得
            
            # --- 更新判定ロジックはそのまま ---
            current_events = getEvents(year, month)
            current_events_json = json.dumps(current_events, sort_keys=True, ensure_ascii=False)
            
            is_calendar_changed = (last_events_json is None or current_events_json != last_events_json)
            is_time_expired = False
            if last_update_time is not None:
                elapsed = now - last_update_time
                if elapsed > datetime.timedelta(minutes=FORCE_UPDATE_MINUTES):
                    is_time_expired = True
            
            should_update = is_calendar_changed or is_time_expired or (last_update_time is None)

            if should_update:
                print(f"[{now.strftime('%H:%M:%S')}] 定期更新を実行します。")
                
                # ★今月のキャッシュキーを指定して更新
                month_data = composer.get_dashboard_image(year, month)
                cache_key = f"month_{year}_{month}"
                image_cache[cache_key] = {
                    "data": month_data,
                    "etag": hashlib.sha256(month_data).hexdigest()
                }

                # 週間カレンダー（これは常に「今」で良い）
                week_data = composer_week.get_dashboard_image()
                image_cache["week_current"] = { # 週間用の固定キー
                    "data": week_data,
                    "etag": hashlib.sha256(week_data).hexdigest()
                }

                last_events_json = current_events_json
                last_update_time = now
                
        except Exception as e:
            print(f" 監視タスクでエラー発生: {e}")

        await asyncio.sleep(300)

def get_cached_data(mode="month", year=None, month=None):
    today = datetime.date.today()
    y = year if year is not None else today.year
    m = month if month is not None else today.month
    
    # 週間モードの場合は固定キー、月間は年月キー
    if mode == "week":
        cache_key = "week_current"
    else:
        cache_key = f"{mode}_{y}_{m}"

    if cache_key not in image_cache:
        # キャッシュがなければ生成して保存
        if mode == "week":
            data = composer_week.get_dashboard_image()
        else:
            data = composer.get_dashboard_image(y, m)
        
        etag = hashlib.sha256(data).hexdigest()
        image_cache[cache_key] = {"data": data, "etag": etag}

    return image_cache[cache_key]["data"], image_cache[cache_key]["etag"]