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

Hello AI: [http://localhost:3001/](http://localhost:3001/)\
教科書読込: [http://localhost:3001/process_file](http://localhost:3001/process_file)

### デバック起動

```bash
export PYTHONPATH=. &&\
export GOOGLE_API_KEY=$(cat cert/google_gemini.pem) &&\
export LANGCHAIN_API_KEY=$(cat cert/langchain.pem) &&\
export $(sed 's/host.docker.internal/localhost/g' .env.develop | xargs) &&\
python cmd/main.py
```