import asyncio
import datetime
import json
import hashlib
from src import composer, composer_week
from src.calendar_api import getEvents

# グローバル変数としてキャッシュを保持
image_cache = {
    "month": {"data": None, "etag": None},
    "week":  {"data": None, "etag": None}
}

last_events_json = None
last_update_time = None  # 最後に画像を更新した時間

# カレンダーに変更がなくても、天気更新のために画像を更新する間隔（分）
FORCE_UPDATE_MINUTES = 30 

# ********** 関数エリア *********
#☆☆☆ カレンダー監視＆キャッシュ更新タスク ☆☆☆☆
async def update_cache_task():
    global last_events_json, image_cache, last_update_time

    while True:
        try:
            now = datetime.datetime.now()
            
            # ---  カレンダーの変更チェック ---
            current_events = getEvents(now.year, now.month)
            current_events_json = json.dumps(current_events, sort_keys=True, ensure_ascii=False)

            # ---  更新判定 ---
            
            # カレンダーの中身が変わったか？
            is_calendar_changed = (last_events_json is None or current_events_json != last_events_json)
            
            # 前回の更新から30分以上経ったか
            is_time_expired = False
            if last_update_time is not None:
                elapsed = now - last_update_time
                if elapsed > datetime.timedelta(minutes=FORCE_UPDATE_MINUTES):
                    is_time_expired = True
            
            # 初回も含めて判定
            should_update = is_calendar_changed or is_time_expired or (last_update_time is None)


            if should_update:
                reason = "カレンダー変更" if is_calendar_changed else "定期(天気)更新"
                print(f"[{now.strftime('%H:%M:%S')}] 更新実行 ({reason}): 画像を作り直します。")
                
                # 画像の生成 , キャッシュ更新
                month_data = composer.get_dashboard_image()
                image_cache["month"]["data"] = month_data
                image_cache["month"]["etag"] = hashlib.sha256(month_data).hexdigest()

                week_data = composer_week.get_dashboard_image()
                image_cache["week"]["data"] = week_data
                image_cache["week"]["etag"] = hashlib.sha256(week_data).hexdigest()

                # 状態を保存
                last_events_json = current_events_json
                last_update_time = now # ★更新時間を記録
                
            else:
                print(f"[{now.strftime('%H:%M:%S')}] 変更なし: カレンダー変更なし & 時間内なのでスキップ。")

        except Exception as e:
            print(f" 監視タスクでエラー発生: {e}")

        # 5分待機
        await asyncio.sleep(300)

# ☆☆☆☆ キャッシュから画像データを取得する関数 ☆☆☆☆
def get_cached_data(mode="month"):
    if image_cache[mode]["data"] is None:
        if mode == "week":
            data = composer_week.get_dashboard_image()
        else:
            data = composer.get_dashboard_image()
        
        etag = hashlib.sha256(data).hexdigest()
        return data, etag

    return image_cache[mode]["data"], image_cache[mode]["etag"]