import requests
import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

# from src import calendar_api

IMG_WIDTH = 280
IMG_HEIGHT = 135

# 色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)

FONT_LARGE = 32
FONT_MEDIUM = 22
FONT_SMALL = 18

CITY_LIST = ["Tokyo", "Osaka", "Nagoya", "Fukuoka", "California", "San Francisco"]

# 言語選択
isJapanese = False
lang = None

# レイアウト設定
padding = 10
bottom_padding = 20

# 言語によってフォント変更
if (isJapanese):
    FONT_FILE = "./src/key/ZenOldMincho-Regular.ttf"
    lang = "ja"
    
else:
    FONT_FILE = "./src/key/KaiseiTokumin-Regular.ttf"
    lang = "en"
    

try:

    print("フォントを適用しました。")
    FONT_LARGE_OBJ = ImageFont.truetype(FONT_FILE, FONT_LARGE)
    FONT_MEDIUM_OBJ = ImageFont.truetype(FONT_FILE, FONT_MEDIUM)
    FONT_SMALL_OBJ = ImageFont.truetype(FONT_FILE, FONT_SMALL)

except IOError:

    print(f"警告: フォントファイル'{FONT_FILE}'が見つかりません。デフォルトのフォントを使用します。")
    FONT_LARGE_OBJ = ImageFont.load_default(size=FONT_LARGE)
    FONT_MEDIUM_OBJ = ImageFont.load_default(size=FONT_MEDIUM)
    FONT_SMALL_OBJ = ImageFont.load_default(size=FONT_SMALL)


def get_weatherInfo(city):
    """
    引数に都市の名前を渡してその都市の今日の天気予報を返す関数
    成功時：辞書データ
    失敗時：None
    """

    try:

        # apiリクエストURL
        req_url = f"https://api.openweathermap.org/data/2.5/weather?&units=metric&lang={lang}&q={city}&appid={API_KEY}"
        
        response = requests.get(req_url)
        response.raise_for_status()

        data = response.json()

        
        # JSONデータを変数に代入
        location = data["name"]
        weather = data["weather"][0]["description"]
        img_id = data["weather"][0]["icon"]
        temperature = data["main"]["temp"]

        # 天気アイコン
        img_url = f"http://openweathermap.org/img/w/{img_id}.png"

        # 天気情報
        data_list = {
            "location" : location,
            "weather" : weather,
            "img_url" : img_url,
            "temperature" : temperature
        }

        return data_list


    except requests.exceptions.RequestException as e:

        print(f"天気情報の取得に失敗しました:{e}")
        return None
    
    except KeyError as e:

        print(f"予期しないデータ形式です。{e}")
        return None
    


def generate_weatherInfo():
    """
    天気予報の画像を生成する関数
    """
    result = get_weatherInfo(CITY_LIST[5])

    image = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)

    # 情報取得に失敗した場合、エラー画像を出力
    if result is None:
        error_message = "Weather Info\nUnavailable"
        draw.text(
            (IMG_WIDTH // 2, IMG_HEIGHT // 2),
            error_message,
            fill=RED,
            font=FONT_MEDIUM_OBJ, # フォントオブジェクトを使用
            anchor="mm",
            align="center"
        )
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='PNG')
        return img_byte_arr.getvalue()



    ## 1.天気アイコン配置
    #アイコンエリアの中心座標
    icon_center_x = (IMG_WIDTH // 3) // 2

    try:
        response = requests.get(result["img_url"])
        response.raise_for_status()

        icon_img = Image.open(io.BytesIO(response.content)).convert("RGBA")
        
        # リサイズ (アスペクト比を保持して収める)
        target_size = (120, 120)
        icon_img = icon_img.resize(target_size, Image.Resampling.LANCZOS)
        
        # 画像の配置(左)
        icon_x = icon_center_x - (icon_img.width // 2) + padding
        icon_y = IMG_HEIGHT - icon_img.height + bottom_padding
        
        # 画像を貼り付ける (mask=icon_img で透過処理)
        image.paste(icon_img, (icon_x, icon_y), icon_img)
        
    except Exception as e:

        print(f"アイコン画像の取得または貼り付けに失敗しました: {e}")
        draw.text(
            (IMG_WIDTH // 4, IMG_HEIGHT // 2),
            "Icon Error",
            fill = BLACK,
            font = FONT_SMALL_OBJ,
            anchor = "mm"
        )


    ## 2.テキスト描画
    # テキストの描画開始座標
    CITY_START_X = IMG_WIDTH // 15
    CITY_START_Y = IMG_HEIGHT // 5

    WEATHER_START_X = IMG_WIDTH // 3 + 20
    WEATHER_START_Y = IMG_HEIGHT // 2

    TEMP_START_X = WEATHER_START_X + 20
    TEMP_START_Y = IMG_HEIGHT * 0.8

    # 日本語の場合は文字のインデントを深くする
    if (isJapanese):
        CITY_START_X = IMG_WIDTH // 10
        WEATHER_START_X = IMG_WIDTH // 2



    # 都市名(上部)
    draw.text(
        (CITY_START_X, CITY_START_Y),
        result["location"],
        fill=BLACK,
        font=FONT_LARGE_OBJ,
        anchor="lm"
    )

    # 天候情報(中央)
    draw.text(
        (WEATHER_START_X, WEATHER_START_Y),
        result["weather"],
        fill=BLACK,
        font=FONT_MEDIUM_OBJ,
        anchor="lm"
    )


    # 気温(下部)
    temp_text = f"{result['temperature']:.1f}℃"

    draw.text(
        (TEMP_START_X, TEMP_START_Y),
        temp_text,
        fill=BLACK,
        # 気温はフォント固定
        font=ImageFont.truetype(
            "./src/key/KaiseiTokumin-Regular.ttf", 
            FONT_LARGE
        ),
        anchor="lm"
    )
    

    img_byte_arr = io.BytesIO()

    image.save(img_byte_arr, format='PNG')

    return img_byte_arr.getvalue()




if __name__ == "__main__":
    
    # print("カレンダー画像を生成中...")
    png_data = generate_weatherInfo()
    
    # # サーバー（Flaskなど）では、この png_data をHTTPレスポンスとして返す
    
    # # このファイルと同じディレクトリに出力(テスト用)
    output_filename = "weather.png"
    with open(output_filename, "wb") as f:
        f.write(png_data)


