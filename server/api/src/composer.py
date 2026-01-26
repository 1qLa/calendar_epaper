# ***** モジュールインポート ******
from PIL import Image
import io
import datetime

from src import create_png    # 月間カレンダー
from src import weather_forecast    # 天気予報
from src import create_today_png    # 今日の予定


# ************* 設定エリア **********

#全画面解像度
TOTAL_WIDTH = 960
TOTAL_HEIGHT = 540



# 左が7割、右側が3割
SPLIT_X = int(TOTAL_WIDTH * 0.7)

# 右側の上下
# 天気が3割、予定が7割
SPLIT_Y = int(TOTAL_HEIGHT * 0.3)


# ********** 関数エリア *********

def combine_dashboard(year=None, month=None):
    canvas = Image.new("RGB", (TOTAL_WIDTH, TOTAL_HEIGHT), (255, 255, 255))

    # 引数がなければ現在時刻
    if year is None or month is None:
        now = datetime.datetime.now()
        year, month = now.year, now.month

    # 各モジュールから画像データを取得する
    # ★ここが重要：create_png に引数を渡す
    calendar_bytes = create_png.throw_data(year, month) 

    weather_bytes = weather_forecast.throw_data() # 天気は常に最新でOK
    today_bytes = create_today_png.throw_data()   # 今日の予定も最新でOK

    img_calendar = Image.open(io.BytesIO(calendar_bytes))
    img_weather = Image.open(io.BytesIO(weather_bytes))
    img_today = Image.open(io.BytesIO(today_bytes))

    # 合成
    canvas.paste(img_calendar, (0, 0))
    canvas.paste(img_weather, (SPLIT_X, 0))
    canvas.paste(img_today, (SPLIT_X, SPLIT_Y))

    output = io.BytesIO()
    canvas.save(output, format="PNG")
    return output.getvalue()


# ☆☆☆☆ 外から呼び出すための関数 ☆☆☆☆
def get_dashboard_image(year=None, month=None):
    return combine_dashboard(year, month)

# テスト実行用
if __name__ == "__main__":
    print("ダッシュボード画像を生成中...")
    png_data = combine_dashboard()
    
    output_filename = "dashboard_test.png"
    with open(output_filename, "wb") as f:
        f.write(png_data)
        
    print(f"完了: '{output_filename}' を保存しました。")