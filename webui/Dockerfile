# ベースイメージにNode.jsのLTS版を使用
FROM node:18-alpine

# 作業ディレクトリを設定
WORKDIR /app

# パッケージ定義ファイルをコンテナにコピー
COPY package.json package-lock.json ./

# 必要なパッケージをインストール
RUN npm install

# ソースコードをコンテナにコピー
COPY . .

# ポート3000を公開
EXPOSE 3000

# コンテナ起動時にNext.jsの開発サーバーを実行
CMD ["yarn", "dev"]