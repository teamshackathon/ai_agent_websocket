## Get Start

### Google API Key を取得する

以下のURLでGoogle AI StudioのAPIキーを作成します。

[Google AI Studio](https://aistudio.google.com/app/apikey)

`cert/google_gemini.pem`を作成して、取得したAPIキーの内容を保存します。

### Lang Smith の API Key を取得する

[Lang Smith](https://smith.langchain.com/)

`cert/langchain.pem`を作成して、取得したAPIキーの内容を保存します。

### GCP のサービスアカウントを作成する

`.evn.develop`に`GOOGLE_SERVICE_ACCOUNT`を定義し、サービスアカウントのメールアドレスを設定します。

### サービスアカウントの認証ファイルを設置する

`cert/authcation.json`を作成、サービスアカウントのJSON形式の認証ファイルの内容をコピーします。

### 各種 URL

[APIドキュメントを確認](http://localhost:8002)

### デバック起動

```bash
export PYTHONPATH=. &&\
export GOOGLE_API_KEY=$(cat cert/google_gemini.pem) &&\
export LANGCHAIN_API_KEY=$(cat cert/langchain.pem) &&\
export $(sed 's/host.docker.internal/localhost/g' .env.develop | xargs) &&\
python cmd/debug.py
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

### Cloud Function Deploy 時コマンド
```bash
export $(cat .env.production | xargs) && \
gcloud functions deploy aiagent-function \
    --gen2 \
    --runtime=python39 \
    --region=asia-northeast1 \
    --source=. \
    --trigger-http \
    --entry-point=cloud_function \
    --allow-unauthenticated \
    --service-account $GOOGLE_SERVICE_ACCOUNT
```

### Cloud Function 環境変数設定コマンド
```bash
export $(cat .env.production | xargs) && \
gcloud functions deploy aiagent-function \
    --update-env-vars LANGCHAIN_TRACING_V2=$LANGCHAIN_TRACING_V2,LANGCHAIN_ENDPOINT=$LANGCHAIN_ENDPOINT,\
LANGCHAIN_PROJECT=$LANGCHAIN_PROJECT,DOCUMENTAI_PROCESSOR_ID=$DOCUMENTAI_PROCESSOR_ID,\
FIREBASE_PROJECT_ID=$FIREBASE_PROJECT_ID,FIREBASE_STORAGE_DOMAIN=$FIREBASE_STORAGE_DOMAIN
```

LangSmithのAPI Keyを別で登録

```bash
gcloud functions deploy aiagent-function \
    --update-env-vars GOOGLE_API_KEY=$(cat cert/google_gemini.pem),LANGCHAIN_API_KEY=$(cat cert/langchain.pem)
```