# 使用するベースイメージを指定
FROM python:3.9-slim

# 作業ディレクトリを設定
WORKDIR /app

ENV PYTHONPATH=/app

COPY entrypoint.sh ./

# シェルスクリプトをエントリーポイントとして設定
ENTRYPOINT ["sh", "entrypoint.sh"]

COPY requirements.txt ./

# pipのアップグレード
RUN pip install --upgrade pip

# 必要なパッケージをインストール
RUN pip install --no-cache-dir -r requirements.txt

# ポート3001を開放
EXPOSE 3001

# ローカルのGoogle Cloud Functionのエミュレーション用にFlaskを使ってサーバーを立てる
CMD ["python", "cmd/main.py"]
