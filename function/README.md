# Getting Started

## Debug
ローカル環境でのデバック方法について

### GCP のサービスアカウントを作成する

`.evn.develop`に`GOOGLE_SERVICE_ACCOUNT`を定義し、サービスアカウントのメールアドレスを設定します。

### サービスアカウントの認証ファイルを設置する

`cert/authcation.json`を作成、サービスアカウントのJSON形式の認証ファイルの内容をコピーします。

### Debug 時コマンド
```bash
export $(cat .env.develop | xargs) && \
go run cmd/main.go
```

## Product
GCPへデプロイする方法について

### GCP のサービスアカウントを作成する

`.evn.production`に`GOOGLE_SERVICE_ACCOUNT`を定義し、サービスアカウントのメールアドレスを設定します。

### GCP Service の有効化

GCPの以下のサービスを有効にします。

- API とサービス -> ライブラリ -> Cloud Speech-to-Text API
- API とサービス -> ライブラリ -> Vertex AI API
- API とサービス -> ライブラリ -> Gemini for Google Cloud

認証情報に`GOOGLE_SERVICE_ACCOUNT`のサービスアカウントが含まれているか確認。

### サービスアカウントに AI Platform の権限を与える

```bash
gcloud projects add-iam-policy-binding $(Project ID) \
--member="serviceAccount:$(Service Account Mail Address)" \
--role="roles/aiplatform.user"
```

### Google Cloud Project の設定
```bash
gcloud config set project $(Project ID)
```

### コンテナイメージをビルドする

```bash
export $(cat .env.production | xargs) &&\
gcloud builds submit --tag gcr.io/$GOOGLE_PROJECT_ID/aiagent-websocket .
```

### Google Cloud Run にデプロイする

```bash
export $(cat .env.production | xargs) &&\
gcloud run deploy aiagent-websocket \
  --image gcr.io/$GOOGLE_PROJECT_ID/aiagent-websocket \
  --platform managed \
  --region asia-northeast1 \
  --service-account $GOOGLE_SERVICE_ACCOUNT \
  --allow-unauthenticated
```