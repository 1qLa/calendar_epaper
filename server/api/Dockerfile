#ベースのイメージ
FROM python:3.12-slim

#--------
#1.環境変数
#--------
#バッファリングを無効化・標準出力を即時出力する設定
ENV PYTHONUNBUFFERED=1
#.pycファイルを生成しない設定
ENV PYTHONDONTWRITEBYTECODE=1

#--------
#2.作業ディレクトリの設定
#--------
WORKDIR /app

#--------
#3.必要なパッケージのインストール
#--------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

#--------
#4.セキュリティ設定
#--------
#コンテナ内でroot権限を使わないようにする
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

#--------
#5.コードのコピー
#--------
COPY ./src ./src

#--------
#6.実行
#--------
USER appuser
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]


