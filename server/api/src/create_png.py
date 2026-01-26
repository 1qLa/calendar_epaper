
# *****モジュールインポート******
import calendar
import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import holidays
import json

#Googleカレンダー取得用
from src import calendar_api

# *************設定エリア**********

#全画面解像度
TOTAL_WIDTH = 960
TOTAL_HEIGHT = 540

#カレンダー幅7割に設定
CALENDAR_WIDTH = int(TOTAL_WIDTH * 0.7)
CALENDAR_HEIGHT = TOTAL_HEIGHT

# 余白の設定
MARGIN = 3

# フォントファイルへのパス
FONT_FILE = "./src/key/KaiseiTokumin-Regular.ttf"

# フォントサイズの設定
FONT_LARGE = 36  # 年月タイトル用
FONT_MEDIUM = 24 # 曜日ヘッダー用
FONT_SMALL = 18  # 日付の数字用
FONT_EVENT = 14  # 予定のリスト用

# 色の設定
WHITE = (255, 255, 255)      # 背景用
BLACK = (0, 0, 0)            # 文字用
BLUE = (0, 0, 255)           # 土曜用
RED = (255, 0, 0)            # 日曜・祝日用
HIGHLIGHT = (235, 235, 235)  # 今日の背景用

# 日付情報の取得
today = datetime.date.today()
# year = today.year
# month = today.month



# ************フォントの準備処理************
try:
    # 指定されたフォントファイルを読み込む
    FONT_LARGE_OBJ = ImageFont.truetype(FONT_FILE, FONT_LARGE)
    FONT_MEDIUM_OBJ = ImageFont.truetype(FONT_FILE, FONT_MEDIUM)
    FONT_SMALL_OBJ = ImageFont.truetype(FONT_FILE, FONT_SMALL)
    FONT_EVENT_OBJ = ImageFont.truetype(FONT_FILE, FONT_EVENT)
except IOError:
    # ファイルがない場合はデフォルトのフォントを使う
    print(f"警告: フォントファイル'{FONT_FILE}'が見つかりません。")
    FONT_LARGE_OBJ = ImageFont.load_default()
    FONT_MEDIUM_OBJ = ImageFont.load_default()
    FONT_SMALL_OBJ = ImageFont.load_default()
    FONT_EVENT_OBJ = ImageFont.load_default()



# **********関数エリア *********


# ☆☆☆☆GoogleカレンダーのJSONから予定辞書を作成する関数☆☆☆☆
def parse_events_from_json(events_list):
    # GoogleカレンダーのリストJSONから、日付ごとの予定辞書を作成する処理
    events_dict = {}
    if not events_list:
        return events_dict
    
    try:
        for event in events_list:
            start = event.get("start", {})
            # "date"(終日) または "dateTime"(時間指定) を取得
            date_str = start.get("date") or start.get("dateTime")

            if date_str:
                # 文字列の先頭10文字(YYYY-MM-DD)だけで日付データを作る
                date_obj = datetime.datetime.strptime(date_str[:10], "%Y-%m-%d").date()
                
                # 辞書にリストがなければ作成
                if date_obj not in events_dict:
                    events_dict[date_obj] = []
                
                # 予定のタイトルを取得して追加
                summary = event.get("summary", "予定あり")
                events_dict[date_obj].append(summary)

    except Exception as e :
        print(f"予定の読み込みエラー {e}")

    return events_dict


# ☆☆☆☆日付マスに予定を書き込む関数☆☆☆☆
def draw_appointment(current_date, events_mapped, day_x, event_y, draw):
    # カレンダーの日付マスに予定を書き込む処理

    if current_date in events_mapped:
        # その日の予定リストを取り出す
        daily_events = events_mapped[current_date]

        # 書き出し位置を少し下げる
        event_y += 20

        # 最大3件までループして描画
        for i, event_summary in enumerate(daily_events[:3]):
            # 文字数が多すぎる場合は ".." で省略する処理
            if len(event_summary) > 10:
                display_text = event_summary[:8] + '..'
            else:
                display_text = event_summary
            
            # テキストを描画
            draw.text(
                (day_x, event_y), 
                display_text, 
                fill = BLACK, 
                font = FONT_EVENT_OBJ, 
                anchor = "mm" # 真ん中揃え
            )
            # 次の行のためにY座標を足す
            event_y += FONT_EVENT + 2

# ☆☆☆☆祝日判定関数☆☆☆☆
def is_holiday(date):
    # 指定された日付が祝日かどうかを判定し、色を返す関数
    color = BLACK
    
    if (date.weekday() == 5):
            # 土曜日
            color = BLUE
    elif (date.weekday() == 6):
            # 日曜日
            color = RED
    
    # 祝日判定ライブラリを使ってチェック
    if (date in jp_holidays):
        color = RED

    return color


#　☆☆☆☆カレンダー画像生成関数☆☆☆☆
def create_calendar_image(year, month):
    
    global jp_holidays
    # 祝日データの取得 
    jp_holidays = holidays.country_holidays("JP", years=year)
    # カレンダーの形を計算
    calendar.setfirstweekday(calendar.SUNDAY)
    cal_data = calendar.monthcalendar(year, month)
    
    week_days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    # 1. 画像のキャンバスを作る
    image = Image.new("RGB", (CALENDAR_WIDTH, CALENDAR_HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)

    # タイトル（年/月）を描く処理
    title = f"{year} / {month:02d}"
    
    draw.text(
        ((CALENDAR_WIDTH - MARGIN) // 2, FONT_LARGE), 
        title, 
        fill = BLACK, 
        font = FONT_LARGE_OBJ, 
        anchor = "mm"
    )

    # 曜日ヘッダーを描く処理
    # 1マスの幅を計算
    cell_width = (CALENDAR_WIDTH - MARGIN) // 7
    # 曜日を表示するY座標
    week_header_y = CALENDAR_HEIGHT // 6

    for i, day_name in enumerate(week_days):
        # X座標の計算
        x = int((i + 0.5) * cell_width)

        # 土日の色変え
        if (day_name == 'Sun'):
            color = RED
        elif (day_name == 'Sat'):
            color = BLUE
        else :
            color = BLACK

        draw.text(
            (x, week_header_y), 
            day_name, 
            fill = color, 
            font = FONT_MEDIUM_OBJ, 
            anchor = "mm"
        )

    # 日付マスを描く処理
    
    # マス目を描き始めるY座標 (全体の1/5の位置)
    day_grid_start_y = CALENDAR_HEIGHT // 5

    # 1マスの高さを計算
    full_height = 80
    cell_height = (CALENDAR_HEIGHT - day_grid_start_y + full_height) // 6
    
    # Googleカレンダーから予定を取得
    try:
        events_list_json = calendar_api.getEvents(year, month)
        events_mapped = parse_events_from_json(events_list_json)
    except Exception as e:
        print(f"エラー: 予定取得失敗 {e}")
        events_mapped = {} 

    # カレンダーの週ごとのループ
    for week_index, week in enumerate(cal_data):
        # 日ごとのループ
        for day_index, day in enumerate(week):
            
            # マスの座標計算
            cell_x_start = day_index * cell_width + MARGIN
            cell_y_start = day_grid_start_y + week_index * cell_height

            cell_coords = (
                cell_x_start,
                cell_y_start,
                cell_x_start + cell_width,
                cell_y_start + cell_height
            )

            # 日付がない部分(0)は枠線だけ描いてスキップ
            if day == 0: 
                draw.rectangle(cell_coords, fill=WHITE, outline=BLACK, width=1)
                continue
            
            # *** 今日の日付の処理 ***
            if (day == today.day and month == today.month and year == today.year):
                # 今日なら背景をグレーにする
                cell_fill_color = HIGHLIGHT
            else:
                # それ以外は白
                cell_fill_color = WHITE
            
            # マス目の四角を描画
            draw.rectangle(
                cell_coords,
                fill=cell_fill_color,
                outline=BLACK,
                width=1
            )
            
            # --- 文字を描く座標の計算 ---
            x = int(cell_x_start + (cell_width * 0.5))  # 左右中央
            y = int(cell_y_start + (cell_height * 0.2)) # 上から20%の位置
            
            
            # --- 休日の色判定 ---
            current_date = datetime.date(year, month, day)
            color = is_holiday(current_date)

            # 日付の数字を描画
            draw.text(
                (x, y), 
                str(day), 
                fill=color, 
                font=FONT_SMALL_OBJ, 
                anchor="mm"
            )

            # 予定の文字を描画する関数を呼び出し
            draw_appointment(current_date, events_mapped, x, y, draw)
            

    # 画像をバイトデータに変換して完了
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


# ☆☆☆☆外から呼び出すための関数☆☆☆☆
def throw_data(year=None, month=None):
    if year is None or month is None:
        today = datetime.date.today()
        year, month = today.year, today.month
    data = create_calendar_image(year, month)
    return data

# テスト実行用
# if __name__ == "__main__":
#     print("カレンダー画像を生成中...")
#     png_data = create_calendar_image()
    
#     output_filename = "this_month_calendar.png"
#     with open(output_filename, "wb") as f:
#         f.write(png_data)
        
#     print(f"完了: '{output_filename}' を保存しました。")