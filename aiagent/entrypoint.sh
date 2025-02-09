#!/bin/bash
export GOOGLE_API_KEY=$(cat cert/google_gemini.pem)
export LANGCHAIN_API_KEY=$(cat cert/langchain.pem)
if [ -n "$DEVELOP" ]; then
    export $(cat .env.develop | xargs)
else
    export $(cat .env.production | xargs)
fi
exec "$@"