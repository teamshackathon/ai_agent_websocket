## Cloud Run にデプロイする

### コンテナイメージをビルドする

```bash
export $(cat .env.production | xargs) &&\
gcloud builds submit --tag gcr.io/$GOOGLE_PROJECT_ID/aiagent-apidoc .
```

### Google Cloud Run にデプロイする

```bash
gcloud run deploy aiagent-apidoc \
  --image gcr.io/$GOOGLE_PROJECT_ID/aiagent-apidoc \
  --platform managed \
  --region asia-northeast1 \
  --service-account $GOOGLE_SERVICE_ACCOUNT \
  --allow-unauthenticated
```

