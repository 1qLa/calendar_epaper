# モジュールインポート
import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import holidays
import json

from src import calendar_api

# 設定エリア (数値は元のコードを維持)

# 全画面解像度
TOTAL_WIDTH = 960
TOTAL_HEIGHT = 540

CALENDAR_WIDTH = int(TOTAL_WIDTH * 0.7)
CALENDAR_HEIGHT = TOTAL_HEIGHT

# 余白設定
MARGIN = 8
MARGIN_TIMELINE = 7 
MARGIN_TIMELINE_HEIGHT = 2

TIMELINE_START_Y = 150       # 時間軸の開始位置
PIXELS_PER_HOUR = 16.5       # 1時間あたりの高さ
RECT_WIDTH = 41              # 予定ボックスの幅

# フォントファイルパス
FONT_FILE = "./src/key/KaiseiTokumin-Regular.ttf"

# フォントサイズ設定
FONT_LARGE = 36
FONT_MEDIUM = 24
FONT_SMALL = 18
FONT_TIME = 12 
FONT_EVENT = 14

# 色設定
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
HIGHLIGHT = (235, 235, 235)  
GRAY_BG = (200, 200, 200)    

# 日付情報の取得
today = datetime.date.today()
year = today.year
month = today.month

# 祝日データの取得
jp_holidays = holidays.Japan(years=year)

# フォントの準備処理
try:
    FONT_LARGE_OBJ = ImageFont.truetype(FONT_FILE, FONT_LARGE)
    FONT_MEDIUM_OBJ = ImageFont.truetype(FONT_FILE, FONT_MEDIUM)
    FONT_SMALL_OBJ = ImageFont.truetype(FONT_FILE, FONT_SMALL)
    FONT_TIME_OBJ = ImageFont.truetype(FONT_FILE, FONT_TIME)
    FONT_EVENT_OBJ = ImageFont.truetype(FONT_FILE, FONT_EVENT)
except IOError:
    print(f"警告: フォントファイル'{FONT_FILE}'が見つかりません。デフォルトを使用します。")
    FONT_LARGE_OBJ = ImageFont.load_default()
    FONT_MEDIUM_OBJ = ImageFont.load_default()
    FONT_SMALL_OBJ = ImageFont.load_default()
    FONT_TIME_OBJ = ImageFont.load_default()
    FONT_EVENT_OBJ = ImageFont.load_default()


# ********関数エリア**********

# ☆☆☆☆ Googleカレンダーデータを解析して辞書に変換する関数 ☆☆☆☆
def parse_events_from_json(events_list):
    """
    Googleカレンダーデータを解析して辞書に変換
    """
    events_dict = {}
    if not events_list:
        return events_dict
    
    try:
        for event in events_list:
            start = event.get("start", {})
            end = event.get("end", {})
            date_str = start.get("date") or start.get("dateTime")

            if date_str:
                date_obj = datetime.datetime.strptime(date_str[:10], "%Y-%m-%d").date()
                if date_obj not in events_dict:
                    events_dict[date_obj] = []
                
                summary = event.get("summary", "予定あり")
                
                # 開始時刻
                start_time_str = "00:00"
                if "dateTime" in start:
                    dt_start = datetime.datetime.fromisoformat(start.get("dateTime"))
                    start_time_str = dt_start.strftime("%H:%M")

                # 終了時刻
                end_time_str = None
                if "dateTime" in end:
                    dt_end = datetime.datetime.fromisoformat(end.get("dateTime"))
                    end_time_str = dt_end.strftime("%H:%M")
                
                events_dict[date_obj].append({
                    "summary": summary,
                    "start_time": start_time_str,
                    "end_time": end_time_str
                })

    except Exception as e:
        print(f"データ解析エラー: {e}")

    return events_dict


def is_holiday(date):
    """休日判定"""
    color = BLACK
    if (date.weekday() == 5): color = BLUE
    elif (date.weekday() == 6): color = RED
    if (date in jp_holidays): color = RED
    return color


# 描画パーツ関数
def draw_time_axis(draw):
    """
    時間軸(00:00~24:00)を描画
    元のコードの配置ロジックを使用
    """
    text_start_x = 40
    line_start_x = text_start_x + 30
    
    # 時間軸の開始位置
    y_base = TIMELINE_START_Y - MARGIN
    
    # 2時間ごとの間隔
    step_pixels = PIXELS_PER_HOUR * 2

    for hour in range(13):
        y = y_base + hour * step_pixels
        time_text = f"{hour * 2:02d}:00"
        
        # 24:00の調整
        if hour == 12:
            draw.text(
                (text_start_x, y - step_pixels / 6),
                "24:00",
                fill=BLACK,
                font=FONT_TIME_OBJ,
                anchor="mm"
            )
        else:
            draw.text(
                (text_start_x, y),
                time_text,
                fill=BLACK,
                font=FONT_TIME_OBJ,
                anchor="mm"
            )
        
        # 横線
        draw.line((line_start_x, y, CALENDAR_WIDTH - MARGIN_TIMELINE, y), fill=BLACK, width=1)


def draw_current_time_line(draw):
    DIFF_JST_FROM_UTC = 9
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=DIFF_JST_FROM_UTC)
    
    current_hour = now.hour
    current_minute = now.minute
    
    # 元のコードと同じ計算式
    y_base = TIMELINE_START_Y - MARGIN
    y = y_base + (current_hour + current_minute / 60) * PIXELS_PER_HOUR

    x_start = 70
    x_end = CALENDAR_WIDTH

    draw.line((x_start, y, x_end, y), fill=RED, width=2)


def draw_event_rect(current_date, events_mapped, day_center_x, draw):
    if current_date not in events_mapped:
        return

    daily_events = events_mapped[current_date]
    
    # 開始位置
    y_base = TIMELINE_START_Y

    for event in daily_events[:10]:
        summary = event.get("summary", "予定")
        start_str = event.get("start_time", "00:00")
        end_str = event.get("end_time")

        # 時間変換
        try:
            sh, sm = map(int, start_str.split(":"))
        except:
            sh, sm = 0, 0
            
        if end_str:
            try:
                eh, em = map(int, end_str.split(":"))
            except:
                eh, em = sh + 1, sm
        else:
            eh, em = sh + 1, sm

        # Y座標計算
        y_start = y_base + (sh + sm / 60) * PIXELS_PER_HOUR
        y_end = y_base + (eh + em / 60) * PIXELS_PER_HOUR

        # 描画
        # 塗りつぶし
        draw.rectangle(
            [day_center_x - RECT_WIDTH, y_start, day_center_x + RECT_WIDTH, y_end],
            fill=GRAY_BG,
            outline=None
        )
        
        # 2. 上下の線
        draw.line(
            [(day_center_x - RECT_WIDTH, y_start), (day_center_x + RECT_WIDTH, y_start)],
            fill=BLACK, width=1
        )
        draw.line(
            [(day_center_x - RECT_WIDTH, y_end), (day_center_x + RECT_WIDTH, y_end)],
            fill=BLACK, width=1
        )

        # テキスト
        display_text = (summary[:10] + '...') if len(summary) > 10 else summary
        text_y = (y_start + y_end) / 2
        
        draw.text(
            (day_center_x, text_y),
            display_text,
            fill=BLACK,
            font=FONT_EVENT_OBJ,
            anchor="mm"
        )


# メイン画像生成関数
def create_calendar_image_week():
    
    # 今週の日付範囲取得
    today = datetime.date.today()
    start_of_week = today - datetime.timedelta(days=(today.weekday() + 1) % 7)
    week_dates = [start_of_week + datetime.timedelta(days=i) for i in range(7)]
    week_days_en = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    # ベース画像
    image = Image.new("RGB", (CALENDAR_WIDTH, CALENDAR_HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)

    # タイトル描画
    title = f"{today.year} / {today.month:02d}"
    draw.text(
        ((CALENDAR_WIDTH - MARGIN) // 2, 35),
        title,
        fill=BLACK,
        font=FONT_LARGE_OBJ,
        anchor="mm"
    )
    
    # 曜日ヘッダー描画
    cell_width = (CALENDAR_WIDTH - MARGIN) // 8
    week_header_y = CALENDAR_HEIGHT // 6 - MARGIN
    time_space = 125

    for i, day_name in enumerate(week_days_en):
        x = int(i * cell_width) + time_space
        color = BLACK
        if day_name == 'Sun': color = RED
        elif day_name == 'Sat': color = BLUE
        
        draw.text((x, week_header_y), day_name, fill=color, font=FONT_SMALL_OBJ, anchor="mm")

    # 予定データの取得
    try:
        raw_events = calendar_api.getEvents(today.year, today.month)
        events_mapped = parse_events_from_json(raw_events)
    except Exception as e:
        print(f"データ取得エラー: {e}")
        events_mapped = {}

    # 日付グリッド描画
    day_grid_start_y = CALENDAR_HEIGHT // 5
    cell_height = (CALENDAR_HEIGHT - day_grid_start_y) // 10
    
    day_centers = []

    for day_index, date_obj in enumerate(week_dates):
        # 座標計算
        cell_x_start = day_index * cell_width + 85
        cell_y_start = day_grid_start_y - MARGIN

        cell_coords = (cell_x_start, cell_y_start, cell_x_start + cell_width, CALENDAR_HEIGHT - MARGIN_TIMELINE_HEIGHT)
        cell_fill_color = HIGHLIGHT if date_obj == today else WHITE

        # 背景と枠線
        draw.rectangle(cell_coords, fill=cell_fill_color, outline=BLACK, width=1)

        # 日付数字
        x = int(cell_x_start + cell_width * 0.5)
        y = int(cell_y_start + cell_height * 0.2) + 12
        color = is_holiday(date_obj)

        draw.text((x, y), str(date_obj.day), fill=color, font=FONT_MEDIUM_OBJ, anchor="mm")
        
        # 中心座標を保存
        day_centers.append({
            "date": date_obj,
            "center_x": x + 0.6
        })

    # 時間軸の描画
    draw_time_axis(draw)

    # 予定の描画
    for info in day_centers:
        draw_event_rect(info["date"], events_mapped, info["center_x"], draw)

    # 現在時刻線
    draw_current_time_line(draw)

    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


# 外から呼び出し用
def throw_data():
    return create_calendar_image_week()


# テスト用
if __name__ == "__main__":
    print("週間カレンダー画像を生成中...")
    png_data_week = create_calendar_image_week()
    with open("this_week_calendar.png", "wb") as f:
        f.write(png_data_week)
    print("完了: 'this_week_calendar.png' を保存しました。")