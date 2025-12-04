import datetime
import os
import os.path
import calendar


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "key/credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "key/token.json")

load_dotenv() # .envファイルから環境変数を読み込む

CALENDAR_ID = os.getenv("CALENDAR_ID") 

# APIに要求する権限を指定
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

JST = datetime.timezone(datetime.timedelta(hours =+ 9), 'JST')

def getEvents(year, month):
  """
  渡された年月のカレンダーから予定のデータを取ってきて返す関数
  """


  time_min = (datetime.datetime(year, month, 1, 0, 0, 0, tzinfo = JST)).isoformat()

  last_day = calendar.monthrange(year, month)[1]
  time_max = (datetime.datetime(year, month, last_day, 23, 59, 59, tzinfo = JST)).isoformat()


  creds = None
  

  if os.path.exists(TOKEN_PATH):
      creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

  # 有効な資格情報がない場合
  if not creds or not creds.valid:
      if creds and creds.expired and creds.refresh_token:
          creds.refresh(Request())
      else:
          # ブラウザで認証して creds を取得
          flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
          creds = flow.run_local_server(port=0)  # ローカル Mac ならブラウザが開く
          # 認証情報を保存
          with open(TOKEN_PATH, "w") as token:
              token.write(creds.to_json())

  try:
    service = build("calendar", "v3", credentials=creds)

    all_events = []
    page_token = None

    while True:
      events_result = (
        service.events()
        .list(
          # calendarIdに取得したい予定のカレンダーIDを指定する
          calendarId=CALENDAR_ID,
          timeMin=time_min,
          timeMax=time_max,
          singleEvents=True,
          orderBy="startTime",
          pageToken = page_token,
          timeZone='Asia/Tokyo'
        )
        .execute()
      )

      events = events_result.get("items", [])
      all_events.extend(events)

      page_token = events_result.get('nextPageToken')
      if not page_token:
        break
      
      page_token = events.get('nextPageToken')
      if not page_token:
        break

    return all_events


  except HttpError as error:
    print(f"エラーが発生しました: {error}")