import datetime
import os.path
import calendar

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


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
  

  # ユーザーのアクセスとリフレッシュトークンを格納するtoken.jsonファイルが存在する場合、token.jsonを使用して認証する。
  if os.path.exists("./src/key/token.json"):
    creds = Credentials.from_authorized_user_file("./src/key/token.json", SCOPES)

  # 有効な資格情報がない場合、ユーザーにログインさせる
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:

      creds.refresh(Request())

    else:

      flow = InstalledAppFlow.from_client_secrets_file(
        "./src/key/redentials.json", SCOPES
      )

      creds = flow.run_local_server(port=0)

    # 次回以降の実行のために資格情報を保存
    with open("./src/key/token.json", "w") as token:
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
          calendarId="f925fe9e059650b7f59278c796d48ad55b257f2cf9bf27adf52b4c32e5a89e3d@group.calendar.google.com",
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