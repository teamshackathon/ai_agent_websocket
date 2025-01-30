from langchain_google_genai import GoogleGenerativeAI
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from google.cloud import storage
import google.generativeai as genai
import functions_framework
import base64
import os

class Recipe(BaseModel):
    ingredients: list[str] = Field(description="ingredients of the dish")
    steps: list[str] = Field(description="steps to make the dish")

output_parser = PydanticOutputParser(pydantic_object=Recipe)

@functions_framework.http
def hello_ai(request):
    model = GoogleGenerativeAI(model="gemini-2.0-flash-exp")
    output = model.invoke("自己紹介をしてください。")
    print(output, flush=True)

    return (f"Hello AI. \n <pre>{output}</pre>"), 200



@functions_framework.http
def process_file(request):
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    blob_bytes = get_resource_bytes("textbook/20250118-002面-新婦人タブ２面.pdf")
    blob_bytes = b''.join(blob_bytes) if isinstance(blob_bytes, tuple) else blob_bytes
    doc_data = base64.standard_b64encode(blob_bytes).decode("utf-8")

    prompt = '''添付した資料を以下のルールを踏まえて文字列として抽出してください。
    - タイトルは先頭に`# `をつける
    - サブタイトルは先頭に`## `をつける
    - １文中の改行は削除する
    - 文先頭の空白の前で改行する
    '''
    text = model.generate_content([{'mime_type': 'application/pdf', 'data': doc_data}, prompt]).text

    print(text, flush=True)

    return (f"Process File. <pre>{text}</pre>"), 200


def get_resource_bytes(file_name):
      # Google Cloud Storage クライアントの作成
    client = storage.Client()

    # 環境変数からバケット名を取得
    bucket_name = os.getenv('RESOURCE_BUCKET_NAME')

    if not bucket_name or not file_name:
        return "Bucket name or FileName not set", 400

    # 指定されたバケットからファイルを取得
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(file_name)

    return blob.download_as_bytes()

