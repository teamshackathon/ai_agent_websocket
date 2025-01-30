#!/bin/bash
#export GOOGLE_API_KEY=$(cat /app/cert/google_gemini.pem)
export LANGCHAIN_API_KEY=$(cat /app/cert/langchain.pem)
export $(cat /app/.env.develop | xargs)
exec "$@"