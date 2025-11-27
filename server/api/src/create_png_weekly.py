# モジュール
import calendar
import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import holidays
import json

from src import calendar_api


## 各種設定
# カレンダーのピクセル数(デフォルト 680:540)
CALENDAR_WIDTH = 680
CALENDAR_HEIGHT = 540

FONT_FILE = "./src/key/KaiseiTokumin-Regular.ttf"
FONT_LARGE = 36
FONT_MEDIUM = 24
FONT_SMALL = 18
FONT_TIME = 12   # 週カレンダーで使用
FONT_EVENT = 16  # 月カレンダーで使用 (週カレンダーでは12)

# フォントオブジェクトの定義 (すべてのサイズを網羅)
try:
    FONT_LARGE_OBJ = ImageFont.truetype(FONT_FILE, FONT_LARGE)
    FONT_MEDIUM_OBJ = ImageFont.truetype(FONT_FILE, FONT_MEDIUM)
    FONT_SMALL_OBJ = ImageFont.truetype(FONT_FILE, FONT_SMALL)
    FONT_TIME_OBJ = ImageFont.truetype(FONT_FILE, FONT_TIME)
    
    # FONT_EVENT_OBJは、両方のコードブロックで使われるため定義
    # 週カレンダーでは12、月カレンダーでは16とサイズが異なるため、ここでは大きい方を採用するか、
    # 各関数内で必要なサイズを改めてロードするのが望ましいが、ここでは提供された設定(16)を使用
    FONT_EVENT_OBJ = ImageFont.truetype(FONT_FILE, FONT_EVENT) 
except IOError:
    print(f"警告: フォントファイル'{FONT_FILE}'が見つかりません。デフォルトフォントを使用します。")
    FONT_LARGE_OBJ = ImageFont.load_default()
    FONT_MEDIUM_OBJ = ImageFont.load_default()
    FONT_SMALL_OBJ = ImageFont.load_default()
    FONT_TIME_OBJ = ImageFont.load_default()
    FONT_EVENT_OBJ = ImageFont.load_default()
    
# 色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
HIGHLIGHT = (235, 235, 235) # ハイライト表示時の背景色

# 今年の西暦と今日の日付を取得
now = datetime.datetime.now()
today = datetime.date.today()
year = today.year
month = today.month
name_holiday = None

# 祝日
jp_holidays = holidays.Japan(years=year)
name_holiday = None


def parse_events_from_json(events_list):
    """
    Googleカレンダーのjson形式データを解析して、
    日付をキー、予定タイトルのリストを値とする辞書を返す
    (週・月カレンダー共通)
    """
    events_dict = {}
    if not events_list:
        return events_dict
    
    try:
        for event in events_list:
            start = event.get("start", {})
            date_str = start.get("date") or start.get("dateTime")

            if date_str:
                date_obj = datetime.datetime.strptime(date_str[:10], "%Y-%m-%d").date()
                if date_obj not in events_dict:
                    events_dict[date_obj] = []
                summary = event.get("summary", "予定あり")
                
                # 週カレンダーのdraw_appointmentのために、時間情報も追加（あれば）
                start_time_str = ""
                if "dateTime" in start:
                    # 例: 2025-11-27T09:30:00+09:00 -> 09:30
                    start_time_str = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z").strftime("%H:%M")

                events_dict[date_obj].append({
                    "summary": summary,
                    "start_time": start_time_str
                })

    except json.JSONDecodeError :
        print("警告:jsonデータの解析に失敗しました")

    except Exception as e :
        print(f"警告:予定の読み込み中に問題が発生しました {e}")

    return events_dict
        
def is_holiday(date):
    """
    平日・休日・祝日を判定してその日の色を返す (週・月カレンダー共通)
    """
    global name_holiday
    color = BLACK
    name_holiday = None

    if (date.weekday() == 5):
            # 土曜日
            color = BLUE
    elif (date.weekday() == 6):
            # 日曜日
            color = RED
    
    if (date in jp_holidays):
        #祝日
        color = RED
        name_holiday = jp_holidays.get(date)

    return color

# --- 週カレンダー関連関数 ---

def draw_time(draw):
    """
    00:00〜24:00の時間軸を描画する関数
    """
    text_start_x = 40
    time_start_x = text_start_x + 30
    text_start_y = 150
    btmTime = 33 # 時間ごとの縦間隔
    
    # FONT_TIME_OBJ を使用
    font_time = FONT_TIME_OBJ
    
    for hour in range(12):
        y = text_start_y + hour * btmTime
        time_text = f"{hour * 2:02d}:00"
        draw.text(
            (text_start_x, y),
            time_text,
            fill=BLACK,
            font=font_time,
            anchor="mm"
        )
        draw.line((time_start_x, y, CALENDAR_WIDTH, y), fill=BLACK, width=1)    

def draw_current_time_line(draw):
    """
    現在時刻の横線を描画
    """
    DIFF_JST_FROM_UTC = 9
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
    current_hour = now.hour
    current_minute = now.minute
    print(f"現在時刻: {now} {current_hour}:{current_minute:02d}")

    # 時間軸の開始位置・間隔（draw_time と同じにする）
    btmTime = 16.5  # 1時間ごとの縦間隔
    text_start_y = 150

    # 現在時刻のy座標を計算
    y = text_start_y + (current_hour + current_minute / 60) * btmTime

    # 線を描画（左端は時間軸右端まで伸ばす）
    x_start = 70  # 時間軸ラベルの少し右
    x_end = CALENDAR_WIDTH

    draw.line(
        (x_start, y, x_end, y),
        fill=(255, 0, 0),  # 赤色
        width=2
    )

def draw_appointment_week(current_date, events_mapped, day_x, draw):
    """
    指定された位置にその日の予定を時間軸に沿って書き込む関数 (週カレンダー用)
    予定のタイトルを灰色で背景塗りつぶし矩形内に表示
    """

    if current_date not in events_mapped:
        return

    daily_events = events_mapped[current_date]

    # 時間軸の開始位置（draw_timeと同じ）
    text_start_y = 150
    PX_PER_HOUR = 33 / 2  # 16.5 ピクセル/時間

    font_event = FONT_EVENT_OBJ 

    for event in daily_events[:10]:  # 最大10件まで表示
        summary = event.get("summary", "予定あり")
        start_time_str = event.get("start_time", "00:00")
        end_time_str = event.get("end_time", None)

        # 開始時間を分解
        try:
            start_hour, start_minute = map(int, start_time_str.split(":"))
        except:
            start_hour, start_minute = 0, 0

        # 終了時間を分解（不明なら開始時間+1時間）
        if end_time_str:
            try:
                end_hour, end_minute = map(int, end_time_str.split(":"))
            except:
                end_hour, end_minute = start_hour + 1, start_minute
        else:
            end_hour, end_minute = start_hour + 1, start_minute

        # y座標計算
        y_start = text_start_y + (start_hour + start_minute / 60) * PX_PER_HOUR
        y_end = text_start_y + (end_hour + end_minute / 60) * PX_PER_HOUR

        # 矩形の横幅と塗りつぶし色
        rect_width = 41
        fill_color = (200, 200, 200)  # 灰色

        # 背景を塗りつぶす矩形
        draw.rectangle(
            [day_x - rect_width, y_start, day_x + rect_width, y_end],
            fill=fill_color,
            outline=None,  # 枠線を残す場合
            width=1
        )

        # テキストは開始時間を表示せず、予定名だけ
        display_text = (summary[:10] + '...') if len(summary) > 10 else summary

        # 矩形内にテキスト表示（中央揃え）
        draw.text(
            (day_x, (y_start + y_end) / 2),
            display_text,
            fill=BLACK,
            font=font_event,
            anchor="mm"
        )



def create_calendar_image_week():
    """
    今日を含む「1週間のカレンダー画像」を生成してPNGのバイトデータを返す関数
    """
    
    today = datetime.date.today()
    year = today.year
    month = today.month

    week_days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        
    start_of_week = today - datetime.timedelta(days=(today.weekday() + 1) % 7)
    week_dates = [start_of_week + datetime.timedelta(days=i) for i in range(7)]

    image = Image.new("RGB", (CALENDAR_WIDTH, CALENDAR_HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)

    font_title = FONT_LARGE_OBJ
    font_week = FONT_SMALL_OBJ
    font_day = FONT_MEDIUM_OBJ

    # タイトルの書き込み (変更なし)
    title = f"{year} / {month:02d}"
    draw.text((CALENDAR_WIDTH // 2, 35), title, fill=BLACK, font=font_title, anchor="mm")
    
    # 曜日の書き込み (変更なし)
    cell_width = CALENDAR_WIDTH // 8
    week_header_y = CALENDAR_HEIGHT // 6
    time_space = 125

    for i, day_name in enumerate(week_days):
        x = int(i * cell_width) + time_space
        color = RED if day_name == 'Sun' else BLUE if day_name == 'Sat' else BLACK
        draw.text((x, week_header_y), day_name, fill = color, font = font_week, anchor = "mm")


    # 予定読み込み (変更なし)
    try:
        events_list_json = calendar_api.getEvents(year, month) 
        events_mapped = parse_events_from_json(events_list_json)
    except Exception as e:
        print(f"エラー: Googleカレンダーの予定取得または解析に失敗しました。 {e}")
        events_mapped = {}

    day_grid_start_y = CALENDAR_HEIGHT // 5
    cell_height = (CALENDAR_HEIGHT - day_grid_start_y) // 10

    # 予定描画のために必要な情報を保存するリストを初期化
    appointments_to_draw = []
    
    # --- 1. 日付セルと日付数字の描画（この時点では予定は描画しない） ---
    for day_index, date_obj in enumerate(week_dates):
        cell_x_start = day_index * cell_width + 85
        cell_y_start = day_grid_start_y 

        cell_coords = (cell_x_start, cell_y_start, cell_x_start + cell_width, CALENDAR_HEIGHT)

        cell_fill_color = HIGHLIGHT if date_obj == today else WHITE

        draw.rectangle(cell_coords, fill=cell_fill_color, outline=BLACK, width=1)

        # セル内に日付数字を描く
        x = int(cell_x_start + cell_width * 0.5)
        y = int(cell_y_start + cell_height * 0.2) + 12

        color = is_holiday(date_obj)

        draw.text((x, y), str(date_obj.day), fill=color, font=font_day, anchor="mm")
        
        # 予定描画に必要な情報を保存
        appointments_to_draw.append({
            'date': date_obj,
            'day_x': x + 0.6
        })
        
        # ★ ここから draw_appointment_week を削除（描画順序を変更するため）
        # draw_appointment_week(date_obj, events_mapped, x + 0.6, draw)
        
    # --- 2. 時間軸の描画（時間軸を最下層にしたい場合は、これを予定の描画よりも前に移動） ---
    
    # 時間軸の描画（時間目盛り）
    # これが予定の下に来るようにする
    draw_time(draw)    
    
    # 現在時刻ラインの描画
    # これが予定の下に来るようにする
    draw_current_time_line(draw)

    # --- 3. Googleカレンダーの予定を描画（これを最後に実行し、時間軸の上に来るようにする） ---
    
    for item in appointments_to_draw:
        draw_appointment_week(item['date'], events_mapped, item['day_x'], draw)


    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

# --- メイン実行とデータ公開関数 ---

def throw_data():
    """
    外部からカレンダー画像データを取得するために呼び出される関数
    mode="week"で週カレンダー、mode="month"で月カレンダーを生成
    """
    data = create_calendar_image_week()
    return data


if __name__ == "__main__":
    
    # 週間カレンダーのテスト実行
    print("週間カレンダー画像を生成中...")
    png_data_week = create_calendar_image_week()
    with open("this_week_calendar.png", "wb") as f:
        f.write(png_data_week)
    print(f"週間カレンダー画像を 'this_week_calendar.png' として保存しました。\n")