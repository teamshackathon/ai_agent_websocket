# 使用するベースイメージを指定
FROM python:3.9-slim

# 作業ディレクトリを設定
WORKDIR /app

ENV PYTHONPATH=/app

# pipのアップグレード
RUN pip install --upgrade pip
# 必要なパッケージをインストール
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのソースコードをコピー
COPY . .

ENTRYPOINT ["sh", "entrypoint.sh"]
CMD ["python", "cmd/main.py"]
