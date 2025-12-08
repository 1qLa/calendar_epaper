# ***** モジュールインポート ******
from PIL import Image
import io

from src import create_png_weekly    # 週間カレンダー
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

def combine_dashboard():
    canvas = Image.new("RGB", (TOTAL_WIDTH, TOTAL_HEIGHT), (255, 255, 255))

    # 各モジュールから画像データを取得する
    calendar_bytes = create_png_weekly.throw_data()#週のカレンダー画像データ取得

    weather_bytes = weather_forecast.throw_data()#天気予報画像データ取得
    
    today_bytes = create_today_png.throw_data()#今日の予定画像データ取得


    img_calendar = Image.open(io.BytesIO(calendar_bytes))
    img_weather = Image.open(io.BytesIO(weather_bytes))
    img_today = Image.open(io.BytesIO(today_bytes))


    
    #左上,月のカレンダー
    canvas.paste(img_calendar, (0, 0))

    # 右上,天気予報
    canvas.paste(img_weather, (SPLIT_X, 0))

    # 右下,今日の予定
    canvas.paste(img_today, (SPLIT_X, SPLIT_Y))


    # 画像をバイトデータに戻して返す
    output = io.BytesIO()
    canvas.save(output, format="PNG")
    return output.getvalue()


# ☆☆☆☆ 外から呼び出すための関数 ☆☆☆☆
def get_dashboard_image():
    return combine_dashboard()


# テスト実行用
if __name__ == "__main__":
    print("ダッシュボード画像を生成中...")
    png_data = combine_dashboard()
    
    output_filename = "dashboard_test.png"
    with open(output_filename, "wb") as f:
        f.write(png_data)
        
    print(f"完了: '{output_filename}' を保存しました。")