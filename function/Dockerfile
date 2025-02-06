# Goの公式イメージを使用
FROM golang:1.22 AS builder

# 作業ディレクトリを設定
WORKDIR /app

# Goの依存関係をコピー
COPY go.mod go.sum ./

# 依存関係をインストール
RUN go mod tidy

# HTTPポートを公開
EXPOSE 3002

# アプリケーションを実行
CMD ["go", "run", "cmd/main.go"]