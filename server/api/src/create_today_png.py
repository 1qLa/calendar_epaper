# ***** モジュールインポート ******
import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import json

# 自作のAPI取得モジュール
from src import calendar_api

# ************* 設定エリア **********

# M5Paperの全画面解像度
TOTAL_WIDTH = 960
TOTAL_HEIGHT = 540

# ★幅の計算: 全体の3割（カレンダーが7割使った残り）
LEFT_WIDTH = int(TOTAL_WIDTH * 0.7)
IMG_WIDTH = TOTAL_WIDTH - LEFT_WIDTH

# 高さの計算: 天気予報(上)と予定(下)
WEATHER_RATIO = 0.3# 天気予報エリアの割合
IMG_HEIGHT = int(TOTAL_HEIGHT * (1 - WEATHER_RATIO)) # 予定エリアの高さ

# レイアウト設定描き始めのY座標
# 天気の下に貼り付ける「予定専用画像」
START_Y = 20

# フォントファイルへのパス
FONT_FILE = "./src/key/KaiseiTokumin-Regular.ttf"

# フォントサイズの設定
FONT_SIZE_DATE = 28   # 日付用
FONT_SIZE_TIME = 18   # 時間用
FONT_SIZE_TITLE = 20  # 件名用

# 色の設定
COLOR_BG = (255, 255, 255)  # 背景色
COLOR_TEXT = (0, 0, 0)      # 文字色
COLOR_LINE = (0, 0, 0)      # 線の色

# ************ フォントの準備処理 ************
try:
    font_date = ImageFont.truetype(FONT_FILE, FONT_SIZE_DATE)
    font_time = ImageFont.truetype(FONT_FILE, FONT_SIZE_TIME)
    font_title = ImageFont.truetype(FONT_FILE, FONT_SIZE_TITLE)
except IOError:
    print("フォントが見つかりません。デフォルトを使用します。")
    font_date = ImageFont.load_default()
    font_time = ImageFont.load_default()
    font_title = ImageFont.load_default()


# ********** 関数エリア *********

# ☆☆☆☆ 中心に文字を描画する便利関数 ☆☆☆☆
def draw_centered_text(draw, text, x, y, font, color=COLOR_TEXT):
    # テキストのサイズを取得して中心座標を計算・描画する
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    draw.text((x - text_w / 2, y - text_h / 2), text, font=font, fill=color)


# ☆☆☆☆ 今日の予定データ（時間付き）を抽出する関数 ☆☆☆☆
def parse_events_with_time(events_list):
    # Googleカレンダーのデータから、時間と件名を抽出してリストで返す
    todays_events = []
    
    # 今日の日付オブジェクト
    target_date = datetime.date.today()

    if not events_list:
        return []

    for event in events_list:
        start = event.get("start", {})
        end = event.get("end", {})
        summary = event.get("summary", "タイトルなし")

        # --- 時間の判定処理 ---
        
        # パターンA: 「終日」の予定
        if 'date' in start:
            event_date = datetime.datetime.strptime(start['date'], "%Y-%m-%d").date()
            if event_date == target_date:
                todays_events.append({
                    'time_str': '終日',   # 左側に表示する文字
                    'summary': summary    # 右側に表示する文字
                })

        # パターンB: 「時間指定」の予定
        elif 'dateTime' in start:
            # ISO形式の日付文字列を解析
            dt_start = datetime.datetime.fromisoformat(start['dateTime'])
            dt_end = datetime.datetime.fromisoformat(end['dateTime'])

            # 日付が今日と一致するか確認
            if dt_start.date() == target_date:
                start_str = dt_start.strftime('%H:%M')
                end_str = dt_end.strftime('%H:%M')
                
                # 2行で表示するために改行コード(\n)を入れる
                time_display = f"{start_str}\n{end_str}"
                
                todays_events.append({
                    'time_str': time_display,
                    'summary': summary
                })

    return todays_events


# ☆☆☆☆ 今日の予定画像生成関数 ☆☆☆☆
def create_today_image():
    
    # 1. ベース画像の作成 (計算した幅 IMG_WIDTH を使用)
    image = Image.new("RGB", (IMG_WIDTH, IMG_HEIGHT), COLOR_BG)
    draw = ImageDraw.Draw(image)

    # 今日の日付を取得
    now = datetime.date.today()

    # 2. 予定データの取得
    try:
        raw_events = calendar_api.getEvents(now.year, now.month)
        schedule_list = parse_events_with_time(raw_events)
    except Exception as e:
        print(f"エラー: カレンダーデータの取得に失敗 {e}")
        schedule_list = []


    # --- 描画処理開始 ---
    current_y = START_Y

    # ******* ヘッダー部分 (日付) *******
    
    # 曜日取得
    weekdays_jp = ["月", "火", "水", "木", "金", "土", "日"]
    wd = weekdays_jp[now.weekday()]

    # 日付テキスト作成
    date_text = f"{now.month:2d}  月  {now.day:2d}  日   ({wd})"

    # 日付を描画 (幅の半分を指定)
    draw_centered_text(draw, date_text, IMG_WIDTH // 2, current_y + 20, font_date)

    current_y += 50

    # 区切り線を描画
    draw.line(
        (20, current_y, IMG_WIDTH - 20, current_y),
        fill=COLOR_LINE,
        width=2
    )
    
    # ******* 予定リスト部分 (表形式) *******
    
    row_height = 60    # 1行の高さ
    time_col_width = 80 # 時間表示エリアの幅
    
    # 予定がない場合
    if not schedule_list:
        draw_centered_text(draw, "予定はありません", IMG_WIDTH // 2, current_y + 40, font_title)
    
    # 予定がある場合、ループして描画
    for event in schedule_list:
        
        row_top = current_y
        row_bottom = current_y + row_height
        
        # 1. 時間を描画 (左側)
        time_text = event['time_str']
        time_center_x = 20 + (time_col_width / 2)
        time_center_y = row_top + (row_height / 2)
        
        # 改行を含むテキストのサイズ取得と描画
        bbox = draw.multiline_textbbox((0, 0), time_text, font=font_time, spacing=4)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        
        draw.multiline_text(
            (time_center_x - w / 2, time_center_y - h / 2), 
            time_text, 
            fill=COLOR_TEXT, 
            font=font_time, 
            align="center",
            spacing=4
        )

        # 2. 縦線を描画
        line_x = 20 + time_col_width
        draw.line(
            (line_x, row_top + 10, line_x, row_bottom - 10),
            fill=COLOR_LINE,
            width=1
        )

        # 3. 件名を描画 (右側)
        title_text = event['summary']
        title_start_x = line_x + 15
        title_center_y = row_top + (row_height / 2)
        
        draw.text(
            (title_start_x, title_center_y),
            title_text,
            fill=COLOR_TEXT,
            font=font_title,
            anchor="lm" # 左端・上下中央揃え
        )

        # 4. 行の下線を描画
        draw.line(
            (20, row_bottom, IMG_WIDTH - 20, row_bottom),
            fill=COLOR_LINE,
            width=1
        )

        # 次の行へ
        current_y += row_height
        
        # 画面からはみ出す場合は終了
        if current_y > IMG_HEIGHT - row_height:
            break

    # 画像をバイトデータに変換
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


# ☆☆☆☆ 外から呼び出すための関数 ☆☆☆☆
def throw_data():
    data = create_today_image()
    return data


# テスト実行用
if __name__ == "__main__":
    print("画像生成中...")
    png_data = create_today_image()
    
    with open("today_design_check.png", "wb") as f:
        f.write(png_data)
    print("完了: 'today_design_check.png' を保存しました。")