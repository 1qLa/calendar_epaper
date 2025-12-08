# ***** モジュールインポート ******
import requests
import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import os
from dotenv import load_dotenv

# .envファイルからAPIキーを読み込む処理
load_dotenv()
API_KEY = os.getenv("API_KEY")

# ************* 設定エリア **********

# 全画面解像度
TOTAL_WIDTH = 960
TOTAL_HEIGHT = 540

# 幅の計算: 全体の3割
# 960 - 672 = 288px
IMG_WIDTH = TOTAL_WIDTH - int(TOTAL_WIDTH * 0.7)

# 高さの計算: 全体の30%
IMG_HEIGHT = int(TOTAL_HEIGHT * 0.3)


# 都市のリスト
CITY_LIST = ["Tokyo", "Osaka", "Nagoya", "Fukuoka", "California", "San Francisco"]
# 今回表示する都市
TARGET_CITY = CITY_LIST[1]

# 言語設定 Trueなら日本語フォント、Falseなら英語フォント
IS_JAPANESE = False
LANG_CODE = "ja" if IS_JAPANESE else "en"

# フォントファイルへのパス
if IS_JAPANESE:
    FONT_FILE = "./src/key/ZenOldMincho-Regular.ttf"
else:
    FONT_FILE = "./src/key/KaiseiTokumin-Regular.ttf"

# フォントサイズの設定
FONT_LARGE = 32
FONT_MEDIUM = 22
FONT_SMALL = 18

# 色の設定
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)


# ************ フォントの準備処理 ************
try:
    print("フォントを適用しました。")
    FONT_LARGE_OBJ = ImageFont.truetype(FONT_FILE, FONT_LARGE)
    FONT_MEDIUM_OBJ = ImageFont.truetype(FONT_FILE, FONT_MEDIUM)
    FONT_SMALL_OBJ = ImageFont.truetype(FONT_FILE, FONT_SMALL)
except IOError:
    print(f"警告: フォントファイル'{FONT_FILE}'が見つかりません。デフォルトを使用します。")
    FONT_LARGE_OBJ = ImageFont.load_default()
    FONT_MEDIUM_OBJ = ImageFont.load_default()
    FONT_SMALL_OBJ = ImageFont.load_default()


# ********** 関数エリア *********

# ☆☆☆☆ APIから天気情報を取得する関数 ☆☆☆☆
def get_weatherInfo(city):
    try:
        # APIリクエストURLの作成
        req_url = f"https://api.openweathermap.org/data/2.5/weather?&units=metric&lang={LANG_CODE}&q={city}&appid={API_KEY}"
        
        # データを取得
        response = requests.get(req_url)
        response.raise_for_status() # エラーならここで例外発生
        
        data = response.json()

        # 必要なデータを取り出し
        location = data["name"]
        weather = data["weather"][0]["description"]
        img_id = data["weather"][0]["icon"]
        temperature = data["main"]["temp"]

        # アイコン画像のURL
        img_url = f"http://openweathermap.org/img/w/{img_id}.png"

        # 辞書にまとめて返す
        return {
            "location": location,
            "weather": weather,
            "img_url": img_url,
            "temperature": temperature
        }

    except Exception as e:
        print(f"天気情報の取得エラー: {e}")
        return None


# ☆☆☆☆ 天気予報画像を生成する関数 ☆☆☆☆
def generate_weatherInfo():
    
    # 1. APIからデータを取得
    result = get_weatherInfo(TARGET_CITY)

    # 2. ベース画像の作成
    image = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)

    # --- 取得失敗時のエラー表示処理 ---
    if result is None:
        error_message = "Weather Info\nUnavailable"
        draw.multiline_text(
            (IMG_WIDTH // 2, IMG_HEIGHT // 2),
            error_message,
            fill=RED,
            font=FONT_MEDIUM_OBJ,
            anchor="mm",
            align="center"
        )
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()


    # --- 正常時の描画処理 ---

    # 天気アイコンの描画 
    icon_center_x = (IMG_WIDTH // 3) // 2
    
    # 余白設定
    padding = 10
    bottom_padding = 20

    try:
        # URLからアイコン画像を取得
        res_img = requests.get(result["img_url"])
        res_img.raise_for_status()
        
        icon_img = Image.open(io.BytesIO(res_img.content)).convert("RGBA")
        
        # リサイズ
        target_size = (120, 120)
        icon_img = icon_img.resize(target_size, Image.Resampling.LANCZOS)
        
        # 配置座標
        icon_x = icon_center_x - (icon_img.width // 2) + padding
        icon_y = IMG_HEIGHT - icon_img.height + bottom_padding
        
        # 透過情報を維持して貼り付け
        image.paste(icon_img, (icon_x, icon_y), icon_img)

    except Exception as e:
        print(f"アイコン描画エラー: {e}")
        draw.text((30, IMG_HEIGHT // 2), "Icon Error", fill=BLACK, font=FONT_SMALL_OBJ)


    # テキスト情報の描画
    
    # 基準座標の計算
    CITY_START_X = IMG_WIDTH // 15
    CITY_START_Y = IMG_HEIGHT // 5

    WEATHER_START_X = IMG_WIDTH // 3 + 20
    WEATHER_START_Y = IMG_HEIGHT // 2

    TEMP_START_X = WEATHER_START_X + 20
    TEMP_START_Y = int(IMG_HEIGHT * 0.8)

    # 日本語の場合の調整ロジックも復元
    if IS_JAPANESE:
        CITY_START_X = IMG_WIDTH // 10
        WEATHER_START_X = IMG_WIDTH // 2


    # 都市名 
    draw.text(
        (CITY_START_X, CITY_START_Y),
        result["location"],
        fill=BLACK,
        font=FONT_LARGE_OBJ,
        anchor="lm" # 左端・上下中央
    )

    # 天気説明
    draw.text(
        (WEATHER_START_X, WEATHER_START_Y),
        result["weather"],
        fill=BLACK,
        font=FONT_MEDIUM_OBJ,
        anchor="lm"
    )

    # 気温
    temp_text = f"{result['temperature']:.1f}℃"
    draw.text(
        (TEMP_START_X, TEMP_START_Y),
        temp_text,
        fill=BLACK,
        font=FONT_LARGE_OBJ, # 気温は大きく
        anchor="lm"
    )

    # 出力 
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


# ☆☆☆☆ 外から呼び出すための関数 ☆☆☆☆
def throw_data():
    return generate_weatherInfo()


# テスト実行用
if __name__ == "__main__":
    print("天気画像を生成中...")
    png_data = generate_weatherInfo()
    
    output_filename = "weather_test.png"
    with open(output_filename, "wb") as f:
        f.write(png_data)
        
    print(f"完了: '{output_filename}' を保存しました。")