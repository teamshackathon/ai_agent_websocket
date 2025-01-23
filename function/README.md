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

### Google Cloud Project の設定
```bash
gcloud config set project $(Project ID)
```

### Cloud Function Deploy 時コマンド
```bash
export $(cat .env.production | xargs) && \
gcloud functions deploy minting-function \
    --gen2 \
    --runtime=go122 \
    --region=asia-northeast1 \
    --source=. \
    --entry-point=HandleWebSocket \
    --trigger-http \
    --allow-unauthenticated \
    --service-account $GOOGLE_SERVICE_ACCOUNT
```

### Cloud Function 環境変数設定コマンド
```bash
export $(cat .env.production | xargs) && \
gcloud functions deploy minting-function \
    --update-env-vars GCP_PROJECT=$GCP_PROJECT,COSE_ORIGIN=$COSE_ORIGIN
```

