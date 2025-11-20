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
FONT_EVENT = 16

# フォントサイズはピクセル数に応じて変更推奨
try:
    FONT_FILE = "./src/key/KaiseiTokumin-Regular.ttf"
    FONT_LARGE_OBJ = ImageFont.truetype(FONT_FILE, FONT_LARGE)
    FONT_MEDIUM_OBJ = ImageFont.truetype(FONT_FILE, FONT_MEDIUM)
    FONT_SMALL_OBJ = ImageFont.truetype(FONT_FILE, FONT_SMALL)
    FONT_EVENT_OBJ = ImageFont.truetype(FONT_FILE, FONT_EVENT)
except IOError:
    print(f"警告: フォントファイル'{FONT_FILE}'が見つかりません。デフォルトフォントを使用します。")
    FONT_LARGE_OBJ = ImageFont.load_default(size=FONT_LARGE)
    FONT_MEDIUM_OBJ = ImageFont.load_default(size=FONT_MEDIUM)
    FONT_SMALL_OBJ = ImageFont.load_default(size=FONT_SMALL)
    FONT_EVENT_OBJ = ImageFont.load_default(size=FONT_EVENT)
    


# 色
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
HIGHLIGHT = (235, 235, 235) # ハイライト表示時の背景色


# 今年の西暦と今日の日付を取得
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
                events_dict[date_obj].append(summary)

    except json.JSONDecodeError :
        print("警告:jsonデータの解析に失敗しました")

    except Exception as e :
        print(f"警告:予定の読み込み中に問題が発生しました {e}")

    return events_dict
        




def draw_appointment(current_date, events_mapped, day_x, event_y, draw):
    """
    指定された位置にその日の予定を書き込む関数
    """

    if current_date in events_mapped:
        daily_events = events_mapped[current_date]

        event_y += 20

        for i, event_summary in enumerate(daily_events[:3]):
            display_text = (event_summary[:8] + '..') if len(event_summary) > 10 else event_summary
            draw.text(
                (day_x, event_y), 
                display_text, 
                fill = BLACK, 
                font = FONT_EVENT_OBJ, 
                anchor = "mm"
            )

            event_y += FONT_EVENT + 2





def is_holiday(date):
    """
    平日・休日・祝日を判定してその日の色を返す
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
        





def create_calendar_image():
    """
    今月のカレンダー画像を生成してPNGのバイトデータを返す関数
    960x540ピクセル、RGBでの表示を想定
    """


    # カレンダーモジュールを日曜日始まりに設定
    calendar.setfirstweekday(calendar.SUNDAY)
    cal_data = calendar.monthcalendar(year, month)

    # 曜日ラベル
    week_days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]



    # 生成する画像の色と解像度を指定
    image = Image.new("RGB", (CALENDAR_WIDTH, CALENDAR_HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)


    # フォントとサイズを反映
    try:

        font_title = ImageFont.truetype(FONT_FILE, FONT_LARGE)
        font_week = ImageFont.truetype(FONT_FILE, FONT_MEDIUM)
        font_day = ImageFont.truetype(FONT_FILE, FONT_SMALL)

    except IOError:

        print(f"警告:フォントファイル'{FONT_FILE}が見つかりません。デフォルトフォントを使用します。")
        font_title = ImageFont.load_default(size=FONT_LARGE)
        font_week = ImageFont.load_default(size=FONT_MEDIUM)
        font_day = ImageFont.load_default(size=FONT_SMALL)
    

    font_title = FONT_LARGE_OBJ
    font_week = FONT_MEDIUM_OBJ
    font_day = FONT_SMALL_OBJ
    # カレンダー上部に表示する年と月の情報(例:2025/11)
    title = f"{year} / {month:02d}"

    draw.text(
        (CALENDAR_WIDTH // 2, FONT_LARGE), 
        title, 
        fill = BLACK, 
        font = font_title, 
        anchor = "mm"
    )

    # 曜日ヘッダー
    cell_width = CALENDAR_WIDTH // 7
    week_header_y = CALENDAR_HEIGHT // 6

    for i, day_name in enumerate(week_days):
        x = int((i + 0.5) * cell_width)

        # 曜日ヘッダーの色変更
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
            font = font_week, 
            anchor = "mm"
        )




    ## 日付の描画と罫線
    # 日付部分のグリッド(マス目)を描き始める一番上のY座標(垂直)を定義
    day_grid_start_y = CALENDAR_HEIGHT // 5

    # セルの高さを計算
    cell_height = (CALENDAR_HEIGHT - day_grid_start_y) // 6
    
    

    try:
        events_list_json = calendar_api.getEvents(year, month)
        events_mapped = parse_events_from_json(events_list_json)
    except Exception as e:
        print(f"エラー: Googleカレンダーの予定取得または解析に失敗しました。 {e}")
        events_mapped = {} 

    for week_index, week in enumerate(cal_data):
        for day_index, day in enumerate(week):
            
            # セルの描画開始座標
            cell_x_start = day_index * cell_width
            cell_y_start = day_grid_start_y + week_index * cell_height


            cell_coords = (
                cell_x_start,
                cell_y_start,
                cell_x_start + cell_width,
                cell_y_start + cell_height
            )


            if day == 0: 
                # 0の日は罫線だけ描画 (背景は白のまま)
                draw.rectangle(cell_coords, fill=WHITE, outline=BLACK, width=1)
                continue
            

            # 今日の日付のみ背景色を変更
            if (day == today.day):
                cell_fill_color = HIGHLIGHT
                
            else:
                cell_fill_color = WHITE

            
            draw.rectangle(
                cell_coords,
                fill=cell_fill_color,
                outline=BLACK,
                width=1
            )
            
            # セルの上部に日付を描画
            x = int(cell_x_start + (cell_width * 0.5))  # セルの左右中央揃え
            y = int(cell_y_start + (cell_height * 0.2)) # セルの上部
            
            
            # 休日・祝日は色を変える
            current_date = datetime.date(year, month, day)
            color = is_holiday(current_date)

            draw.text(
                (x, y), 
                str(day), 
                fill=color, 
                font=font_day, 
                anchor="mm"
            )


            draw_appointment(current_date, events_mapped, x, y, draw)
            
                
                

    # メモリ上のバイトバッファを作成
    img_byte_arr = io.BytesIO()
    
    # PNG形式で保存
    image.save(img_byte_arr, format='PNG')
    
    # バイトデータを返す
    return img_byte_arr.getvalue()
    
    # M5PaperS3はPNGの表示に対応しているため、PNG形式で保存
    # image.save(img_byte_arr, format='PNG')
    
    # バッファの先頭に戻す (getvalue()を使うので厳密には不要)
    # img_byte_arr.seek(0) 

    # バイトデータを返す
    # return img_byte_arr.getvalue()

#
def throw_data():
    data = create_calendar_image()
    return data




if __name__ == "__main__":
    
    # print("カレンダー画像を生成中...")
    # png_data = create_calendar_image()
    
    # # サーバー（Flaskなど）では、この png_data をHTTPレスポンスとして返す
    
    # # このファイルと同じディレクトリに出力(テスト用)
    # output_filename = "this_month_calendar.png"
    # with open(output_filename, "wb") as f:
    #     f.write(png_data)
        
    # print(f"カレンダー画像を '{output_filename}' として保存しました。\n")
    data = create_calendar_image()
    print(data)
    