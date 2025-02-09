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

[API仕様](http://localhost:8001)

### デバック起動

```bash
export PYTHONPATH=. &&\
export GOOGLE_API_KEY=$(cat cert/google_gemini.pem) &&\
export LANGCHAIN_API_KEY=$(cat cert/langchain.pem) &&\
export $(sed 's/host.docker.internal/localhost/g' .env.develop | xargs) &&\
sed -i '' 's/app.debug = False/app.debug = True/' cmd/main.py &&\
python cmd/main.py
```

## Cloud Run にデプロイする

### コンテナイメージをビルドする

```bash
export $(cat .env.production | xargs) &&\
sed -i '' 's/app.debug = True/app.debug = False/' cmd/main.py &&\
gcloud builds submit --tag gcr.io/$GOOGLE_PROJECT_ID/aiagent-app .
```

### Google Cloud Run にデプロイする

```bash
gcloud run deploy aiagent-app \
  --image gcr.io/$GOOGLE_PROJECT_ID/aiagent-app \
  --platform managed \
  --region asia-northeast1 \
  --service-account $GOOGLE_SERVICE_ACCOUNT \
  --allow-unauthenticated
```

 ### Firebase へのアクセス権限を追加

```bash
gcloud projects add-iam-policy-binding $GOOGLE_PROJECT_ID \
  --member="serviceAccount:$GOOGLE_SERVICE_ACCOUNT" \
  --role="roles/firebase.admin"
```

### Fire storage　の CORS 設定

```bash
gsutil cors set cors.json gs://manabiyaai.firebasestorage.app
```
