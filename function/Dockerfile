# Goの公式イメージを使用
FROM golang:1.22 AS builder

# 作業ディレクトリを設定
WORKDIR /app

# Goの依存関係をコピー
COPY go.mod go.sum ./
# 依存関係をインストール
RUN go mod tidy

# アプリケーションのソースコードをコピー
COPY . .

# アプリケーションをビルド
RUN go build -o cmd/main .

ENTRYPOINT ["sh", "entrypoint.sh"]
CMD ["go", "run", "cmd/main.go"]