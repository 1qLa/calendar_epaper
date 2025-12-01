# モジュールをインポート
import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import holidays
import json

# 自作のAPI取得モジュール
from src import calendar_api

## --- 設定エリア ---

# 画像全体のサイズ
CALENDAR_WIDTH = 280  # 幅
CALENDAR_HEIGHT = 450 # 高さ

# レイアウト設定: 上から何%の位置から描き始めるか 
START_Y_RATIO = 0.3
START_Y = int(CALENDAR_HEIGHT * START_Y_RATIO)

# フォントファイルへのパス
FONT_FILE = "./src/key/KaiseiTokumin-Regular.ttf"

# フォントサイズの設定
FONT_SIZE_DATE = 28   # 「12月25日」などの日付用
FONT_SIZE_TIME = 18   # 「16:00」などの時間用
FONT_SIZE_TITLE = 20  # 「買い物」などの件名用

# 色の設定 (RGB)
COLOR_BG = (245, 245, 245)  # 背景色（画像に合わせて少しグレーに）
COLOR_TEXT = (0, 0, 0)      # 文字色（黒）
COLOR_LINE = (0, 0, 0)      # 線の色（黒）

# フォントオブジェクトの生成（読み込み失敗時の対策付き）
try:
    font_date = ImageFont.truetype(FONT_FILE, FONT_SIZE_DATE)
    font_time = ImageFont.truetype(FONT_FILE, FONT_SIZE_TIME)
    font_title = ImageFont.truetype(FONT_FILE, FONT_SIZE_TITLE)
except IOError:
    print("フォントが見つかりません。デフォルトを使用します。")
    font_date = ImageFont.load_default()
    font_time = ImageFont.load_default()
    font_title = ImageFont.load_default()


## --- 関数エリア ---

def parse_events_with_time(events_list):
    """
    Googleカレンダーのデータから、今日の予定の「時間」と「件名」を抽出する関数
    """
    todays_events = []
    
    # 今日の日付オブジェクト
    target_date = datetime.date.today()
    # テスト用
    # target_date = datetime.date(2024, 12, 25) 

    if not events_list:
        return []

    for event in events_list:
        start = event.get("start", {})
        end = event.get("end", {})
        summary = event.get("summary", "タイトルなし")

        # --- 時間の判定処理 ---
        
        # パターンA: 「終日」の予定 (例: start: {'date': '2024-12-25'})
        if 'date' in start:
            event_date = datetime.datetime.strptime(start['date'], "%Y-%m-%d").date()
            if event_date == target_date:
                todays_events.append({
                    'time_str': '終日',   # 左側に表示する文字
                    'summary': summary    # 右側に表示する文字
                })

        # パターンB: 「時間指定」の予定 (例: start: {'dateTime': '2024-12-25T16:00:00+09:00'})
        elif 'dateTime' in start:
            # ISO形式の日付文字列を解析
            dt_start = datetime.datetime.fromisoformat(start['dateTime'])
            dt_end = datetime.datetime.fromisoformat(end['dateTime'])

            # 日付が今日と一致するか確認
            if dt_start.date() == target_date:
                # 時間を "16:00" の形式にする
                start_str = dt_start.strftime('%H:%M')
                end_str = dt_end.strftime('%H:%M')
                
                # 2行で表示するために改行コード(\n)を入れる
                time_display = f"{start_str}\n{end_str}"
                
                todays_events.append({
                    'time_str': time_display,
                    'summary': summary
                })

    return todays_events


def draw_centered_text(draw, text, x, y, font, color=COLOR_TEXT):
    """
    指定した座標(x, y)を中心に文字を描画する便利関数
    """
    # テキストの描画サイズを取得（バウンディングボックス）
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    
    # 中心位置を計算して描画
    draw.text((x - text_w / 2, y - text_h / 2), text, font=font, fill=color)


def create_today_image():
    """
    メインの画像生成関数
    """
    
    # 1. ベース画像の作成 (背景色で塗りつぶし)
    image = Image.new("RGB", (CALENDAR_WIDTH, CALENDAR_HEIGHT), COLOR_BG)
    draw = ImageDraw.Draw(image)

    # 今日の日付を取得
    now = datetime.date.today()
    # テスト用
    # now = datetime.date(2024, 12, 25)

    # 2. 予定データの取得
    try:
        raw_events = calendar_api.getEvents(now.year, now.month)
        # 上で作った関数で「時間」と「件名」のリストに変換
        schedule_list = parse_events_with_time(raw_events)
    except Exception as e:
        print(f"エラー: カレンダーデータの取得に失敗 {e}")
        schedule_list = []


    # --- 描画開始 ---
    
    # 描画の基準となるY座標（最初は START_Y からスタート）
    current_y = START_Y

    # ==========================
    #  ヘッダー部分 (日付)
    # ==========================
    
    # 曜日を日本語に変換するためのリスト
    weekdays_jp = ["月", "火", "水", "木", "金", "土", "日"]
    wd = weekdays_jp[now.weekday()] # 0=月曜, ... 6=日曜

    # 表示する文字を作成: "12 月 25 日 (木)"
    # 数字と文字の間にスペースを入れて見やすく調整
    date_text = f"{now.month:2d}  月  {now.day:2d}  日   ({wd})"

    # 日付を描画 (横幅のちょうど真ん中、現在のY座標に)
    draw_centered_text(draw, date_text, CALENDAR_WIDTH // 2, current_y + 20, font_date)

    # Y座標を進める（日付の高さ分 + 余白）
    current_y += 50

    # ヘッダー下の太線を描画
    draw.line(
        (20, current_y, CALENDAR_WIDTH - 20, current_y), # (開始X, 開始Y, 終了X, 終了Y)
        fill=COLOR_LINE,
        width=2 # 線の太さ
    )
    
    # ==========================
    #  予定リスト部分 (表形式)
    # ==========================
    
    # 1行あたりの高さ
    row_height = 60
    
    # 時間カラムの幅（左側の幅）
    time_col_width = 80 
    
    # 予定がない場合のメッセージ
    if not schedule_list:
        draw_centered_text(draw, "予定はありません", CALENDAR_WIDTH // 2, current_y + 40, font_title)
    
    # 予定がある場合、ループして順番に描く
    for event in schedule_list:
        
        # --- この行のエリア計算 ---
        row_top = current_y         # 行の上端
        row_bottom = current_y + row_height # 行の下端
        
        # 1. 時間を描画 (左側のエリア)
        # 時間の文字を取得 (例: "16:00\n18:00")
        time_text = event['time_str']
        
        # 時間エリアの中心座標を計算
        time_center_x = 20 + (time_col_width / 2)
        time_center_y = row_top + (row_height / 2)
        
        # 時間を描画 (行間隔を少し狭めるために spacing 引数を利用)
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

        # 2. 縦線を描画 (時間と件名の境界線)
        line_x = 20 + time_col_width
        # 行の上から下まで線を引く（少し余白を開けるため +5, -5 しています）
        draw.line(
            (line_x, row_top + 10, line_x, row_bottom - 10),
            fill=COLOR_LINE,
            width=1
        )

        # 3. 件名を描画 (右側のエリア)
        title_text = event['summary']
        
        # 件名の開始X座標
        title_start_x = line_x + 15
        title_center_y = row_top + (row_height / 2)
        
        # 件名を描画 (左揃え、上下中央)
        # アンカー "lm" = Left Middle (左端・上下中央) を基準にする
        draw.text(
            (title_start_x, title_center_y),
            title_text,
            fill=COLOR_TEXT,
            font=font_title,
            anchor="lm" 
        )

        # 4. 下線を描画 (行の区切り線)
        draw.line(
            (20, row_bottom, CALENDAR_WIDTH - 20, row_bottom),
            fill=COLOR_LINE,
            width=1
        )

        # 次の行を描くためにY座標を更新
        current_y += row_height
        
        # 画面からはみ出しそうならループを終了
        if current_y > CALENDAR_HEIGHT - row_height:
            break


    # --- 画像出力処理 ---
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()


def throw_data():
    """外部から呼ばれるエントリーポイント"""
    data = create_today_image()
    return data


# --- 動作確認用ブロック ---
if __name__ == "__main__":
    # このファイルを直接実行したときだけ動くコード
    print("画像生成中...")
    png_data = create_today_image()
    
    # 確認用に保存
    with open("today_design_check.png", "wb") as f:
        f.write(png_data)
    print("完了: 'today_design_check.png' を保存しました。")