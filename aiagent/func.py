import base64
import zipfile
import shutil
import os
import json

import functions_framework
import google.generativeai as genai
from langchain_chroma import Chroma
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import GoogleGenerativeAI, GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_text_splitters import CharacterTextSplitter

from pydantic import BaseModel, Field
from chromadb import PersistentClient
import jschema
import jprompt
from firebase import Firestore, Firestorage



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
def chat_ai_as_student(request):

    # JSONデータを取得
    data = request.get_json()

    reference = data.get('reference')
    if reference is None:
        return error_response(400, 'INPUT_ERROR', "reference is required.")
    
    dict_ref = parse_chat_path(str(reference))

    chats_path = dict_ref['chats'] + '/' + dict_ref['chatId'] + '/messages'
    print(chats_path, flush=True)
    # ドキュメントを取得
    list_doc = Firestore.to_list(chats_path)
    
    if list_doc is None or len(list_doc) == 0:
        return error_response(400, '_ERROR', "Nothing found in the path.")

    print(list_doc, flush=True)

    # 配列の中身をintに変換
    list_doc = [int(i) for i in list_doc]
    # 大きい順にソート
    list_doc.sort(reverse=True)
    # 大きいものから10個取得
    list_doc = list_doc[:10]

    context = []
    for doc_id in list_doc:
        doc_path = chats_path + '/' + str(doc_id)
        doc_dict = Firestore.to_dict(doc_path)
        print(doc_dict, flush=True)
        if doc_dict is not None:
            context.append(f"{doc_dict['senderId']}:"+doc_dict['text'] + f"{doc_dict['messageId']}に送信")

    context = '\n'.join(context)

    prompt = """
    あなたは教師です。そしてこれは生徒とのチャットです。生徒が質問をしてきました。その質問に対して回答してください。
    今までの会話は以下の通りです。
    """ + context


    model = GoogleGenerativeAI(model="gemini-2.0-flash-exp")
    output = model.invoke(prompt)
    from datetime import datetime
    # 新規メッセージの作成
    doc_id = str(int(datetime.now().timestamp() * 1000))

    Firestore.set_field(chats_path + "/" + doc_id, "messageId", doc_id)
    Firestore.set_field(chats_path + "/" + doc_id, "senderId", "ManabiyaAI")
    Firestore.set_field(chats_path + "/" + doc_id, "text", output)
    Firestore.set_field(chats_path + "/" + doc_id, "createdAt", datetime.now())
    Firestore.set_field(chats_path + "/" + doc_id, "read", False)

    return output, 200

@functions_framework.http
def chat_ai_as_teacher(request):

    # JSONデータを取得
    data = request.get_json()

    reference = data.get('reference')
    if reference is None:
        return error_response(400, 'INPUT_ERROR', "reference is required.")
    
    dict_ref = parse_chat_path(str(reference))

    chats_path = dict_ref['chats'] + '/' + dict_ref['chatId'] + '/messages'
    print(chats_path, flush=True)
    # ドキュメントを取得
    list_doc = Firestore.to_list(chats_path)
    
    if list_doc is None or len(list_doc) == 0:
        return error_response(400, '_ERROR', "Nothing found in the path.")

    print(list_doc, flush=True)

    # 配列の中身をintに変換
    list_doc = [int(i) for i in list_doc]
    # 大きい順にソート
    list_doc.sort(reverse=True)
    # 大きいものから10個取得
    list_doc = list_doc[:10]

    context = []
    for doc_id in list_doc:
        doc_path = chats_path + '/' + str(doc_id)
        doc_dict = Firestore.to_dict(doc_path)
        print(doc_dict, flush=True)
        if doc_dict is not None:
            context.append(f"{doc_dict['senderId']}:"+doc_dict['text'] + f"{doc_dict['messageId']}に送信")

    context = '\n'.join(context)

    prompt = """
    あなたはベテラン教師です。そしてこれは教師とのチャットです。教師が質問をしてきました。その質問に対して回答してください。
    今までの会話は以下の通りです。
    """ + context


    model = GoogleGenerativeAI(model="gemini-2.0-flash-exp")
    output = model.invoke(prompt)
    from datetime import datetime
    # 新規メッセージの作成
    doc_id = str(int(datetime.now().timestamp() * 1000))

    Firestore.set_field(chats_path + "/" + doc_id, "messageId", doc_id)
    Firestore.set_field(chats_path + "/" + doc_id, "senderId", "ManabiyaAI")
    Firestore.set_field(chats_path + "/" + doc_id, "text", output)
    Firestore.set_field(chats_path + "/" + doc_id, "createdAt", datetime.now())
    Firestore.set_field(chats_path + "/" + doc_id, "read", False)

    return output, 200
    

@functions_framework.http
def create_agenda(request):
    # JSONデータを取得
    data = request.get_json()

    reference = data.get('reference')
    if reference is None:
        return error_response(400, 'INPUT_ERROR', "reference is required.")

    start_page = data.get('start_page')
    if start_page is None:
        return error_response(400, 'INPUT_ERROR', "start_page is required.")

    finish_page = data.get('finish_page')
    if finish_page is None:
        return error_response(400, 'INPUT_ERROR', "finish_page is required.")

    # TODO Noticeパラメータ取得の実装予定

    dict_ref = parse_path(str(reference))
    subject_path = dict_ref['year'] + '/' + dict_ref['class'] + '/common/' + dict_ref['subject']
    # ドキュメントを取得
    dict_field = Firestore.to_dict(subject_path)

    if dict_field is None or dict_field == {}:
        return error_response(400, 'SETTING_ERROR', "Failed find text path.")

    # Chroma DB path
    chroma_path = "/tmp/chroma"
    # Chroma DB
    db = None

    if dict_field.get('text_chroma') is None:
        # テキストからChromaDBを作成
        if dict_field.get('text') is None:
            return error_response(400, 'SETTING_ERROR', "Failed find text field.")

        # PDFをドキュメントに変換
        docs = convert_pdf_to_docs(str(dict_field['text']))
        # ChromaDBを作成
        db = create_chroma(chroma_path, docs)
        # ChromaDBをstrageに保存
        storage_path = store_chroma(chroma_path, dict_ref)
        # storageのパスをFirestoreに保存
        Firestore.set_field(subject_path,'text_chroma', storage_path)

    else:
        # ChromaDBをfirestoreから取得
        text_chroma_path = dict_field.get('text_chroma')
        # ChromaDBをfirestorageから取得
        restore_chroma(text_chroma_path, chroma_path)
        # ChromaDBを作成
        db = create_chroma(chroma_path)

    # アジェンダ作成
    agenda_data = create_agenda_from_vector(db, start_page, finish_page)

    # アジェンダ格納フィールド名
    field_name = "agenda_draft"
    json_agenda = json.loads(agenda_data)
    Firestore.set_field(reference, field_name, json_agenda)

    Firestore.set_field(reference, 'start_page', int(start_page))
    Firestore.set_field(reference, 'finish_page', int(finish_page))

    # TODO Notice実装予定

    return created_response(reference, agenda=field_name)


@functions_framework.http
def create_questions(request):
    # JSONデータを取得
    data = request.get_json()

    reference = data.get('reference')
    if reference is None:
        return error_response(400, 'INPUT_ERROR', "reference is required.")

    # TODO Noticeパラメータ取得の実装予定

    dict_ref = parse_path(str(reference))
    dict_ref_field = Firestore.to_dict(reference)

    start_page = dict_ref_field.get('start_page')
    finish_page = dict_ref_field.get('finish_page')

    if start_page is None or finish_page is None:
        return error_response(400, 'SETTING_ERROR', "Failed cant find start_page/finish_page.")

    subject_path = dict_ref['year'] + '/' + dict_ref['class'] + '/common/' + dict_ref['subject']
    # ドキュメントを取得
    dict_field = Firestore.to_dict(subject_path)

    if dict_field is None or dict_field == {}:
        return error_response(400, 'SETTING_ERROR', "Failed find text path.")

    # ChromaDBをfirestoreから取得
    text_chroma_path = dict_field.get('text_chroma')
    if text_chroma_path is None:
        return error_response(400, 'SETTING_ERROR', "Failed make agenda before making question.")

    # Chroma DB path
    chroma_path = "/tmp/chroma"
    # ChromaDBをfirestorageから取得
    restore_chroma(text_chroma_path, chroma_path)
    # ChromaDBを作成
    db = create_chroma(chroma_path)

    question_data = create_questions_from_vector(db, start_page, finish_page)

    # 小テスト格納フィールド名
    field_name = "questions_draft"
    json_questions = json.loads(question_data)
    Firestore.set_field(reference, field_name, json_questions)

    # TODO Notice実装予定

    return created_response(reference, questions=field_name)


### langchain functions ###

def create_chroma(chroma_path, docs=None):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    os.makedirs(chroma_path, exist_ok=True)
    client = PersistentClient(path=chroma_path)

    # create instance
    db = Chroma(
        collection_name="langchain_store",
        embedding_function=embeddings,
        client=client
    )

    if docs:
        # ドキュメントをドキュメント化し、保存
        db.add_documents(documents=docs, embedding=embeddings)
    return db

def create_agenda_from_vector(db, start_page, finish_page):
    # テキストに関連するドキュメントを得るインターフェースを「Retriever」と言います。
    retriever = db.as_retriever()

    schema_agenda_runnable = RunnableLambda(lambda x: jschema.SCHEMA_AGENDA)

    prompt = ChatPromptTemplate.from_template('''\
    以下の文脈だけを踏まえて質問に回答してください。

    文脈:"""
    {context}
    """

    質問:{question}

    出力形式:"""
    {schema_agenda}
    """
    
    ''')

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")

    chain = (
        {"context": retriever, "question": RunnablePassthrough(), "schema_agenda": schema_agenda_runnable}
        | prompt
        | llm
        # | class2json
        | StrOutputParser()
        | replaced2json
        # | json2dict
    )

    query = f"今回の授業は{start_page}ページから{finish_page}ページを学習します。授業時間は40分です。授業のアジェンダを作成してください。"
    # Json形式のアジェンダ作成
    json_agenda = chain.invoke(query)

    return json_agenda


def create_questions_from_vector(db, start_page, finish_page):
    # テキストに関連するドキュメントを得るインターフェースを「Retriever」と言います。
    retriever = db.as_retriever()

    rule_test_runnable = RunnableLambda(lambda x: jprompt.RULE_TEST)
    schema_question_runnable = RunnableLambda(lambda x: jschema.SCHEMA_QUESTION)
    question_sample_runnable = RunnableLambda(lambda x: jschema.QUESTION_SAMPLE)

    # TODO 授業音声を取り込んで問題に反映させる

    prompt = ChatPromptTemplate.from_template('''\
    以下の文脈だけを踏まえて質問に回答してください。

    文脈:"""
    {context}
    """

    質問:{question}

    問題のルール:"""
    {rule}
    """

    問題定義の出力形式:"""
    {schema}
    """

    問題定義の出力形式の例:"""
    {schema_sample}
    """
    ''')

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")

    chain = (
            {"context": retriever, "question": RunnablePassthrough(), "rule": rule_test_runnable, "schema": schema_question_runnable, "schema_sample": question_sample_runnable}
            | prompt
            | llm
            | StrOutputParser()
            | replaced2json
    )

    query = f"授業の小テストを作成します。{start_page}ページから{finish_page}ページの内容を元に問題を4題作成してください。問題の重要度を鑑みて`score`の点数設定をしてください。"
    # Json形式の小テスト作成
    questions_data = chain.invoke(query)

    return questions_data


@chain
def replaced2json(output: str) -> str:
  replaced_output = output.replace('```json', '').replace('```', '')
  # replaced_output = json.loads(replaced_output) # これを加えるとdict型になってしまう
  return replaced_output

def convert_pdf_to_docs(file_path):
    model = genai.GenerativeModel("gemini-2.0-flash-exp")

    blob_bytes = Firestorage.get_bytes(file_path)
    if blob_bytes is None:
        raise ValueError(f"Failed to retrieve bytes from file: {file_path}")
    doc_data = base64.standard_b64encode(blob_bytes).decode("utf-8")

    response = model.generate_content([{'mime_type': 'application/pdf', 'data': doc_data}, jprompt.RULE_TEXT]).text

    # text_splitter = CharacterTextSplitter(chunk_size=1500, chunk_overlap=100, separator='\n---\n')
    text_splitter = CharacterTextSplitter(chunk_size=1500, chunk_overlap=500)
    texts = text_splitter.create_documents([response])
    docs = text_splitter.split_documents(texts)

    return docs

def store_chroma(persist_directory, dict_ref):
    # chromaディレクトリをZipファイル化
    zip_filename = f"chroma_{dict_ref['year']}_{dict_ref['class']}_{dict_ref['subject']}.zip"
    zip_path = f"/tmp/{zip_filename}"
    zip_directory(persist_directory, zip_path)

    # ZipファイルをFirestorageにアップロード
    storage_path = f"chroma/{zip_filename}"
    Firestorage.put_file(storage_path, zip_path)

    return storage_path

def restore_chroma(storage_path, persist_directory):
    file_path = "/tmp/chroma.zip"
    # chromaディレクトリをZipファイル化
    bytes = Firestorage.get_bytes(storage_path)
    with open(file_path, 'wb') as file:
        # bytesデータをファイルに書き込む
        file.write(bytes)
        unzip_file(file_path, persist_directory)

### Utility Functions ###

def zip_directory(directory_path, zip_name):
    # zipファイルを作成
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # ディレクトリ内のファイルを全て追加
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                # zipファイル内での相対パスを指定
                arcname = os.path.relpath(file_path, directory_path)
                zipf.write(file_path, arcname)

def unzip_file(zip_name, extract_to_folder):
    # 解凍先のフォルダが存在する場合は削除してから作り直し
    if os.path.exists(extract_to_folder):
        shutil.rmtree(extract_to_folder)
    os.makedirs(extract_to_folder)

    # ZIPファイルを解凍
    with zipfile.ZipFile(zip_name, 'r') as zipf:
        zipf.extractall(extract_to_folder)

def parse_path(path):
    '''
    パスの各要素を解析する
    :param path: reference path
    :return: object[year, class, student, subject, lessons, lesson_id]
    '''
    keys = ['year', 'class', 'student', 'subject', 'lessons', 'lesson_id']
    path_parts = path.split('/')

    dict_path = {}
    for i in range(len(path_parts)):
        if len(keys) <= i: break
        dict_path[keys[i]] = path_parts[i]

    return dict_path

def parse_chat_path(path):
    '''
    Chatsパスの各要素を解析する
    :param path: reference path
    :return: object[chats, chatId, messages]
    '''

    keys = ['chats', 'chatId', 'messages']
    path_parts = path.split('/')
    dict_path = {}
    for i in range(len(path_parts)):
        if len(keys) <= i: break
        dict_path[keys[i]] = path_parts[i]

    return dict_path

def created_response(reference, agenda=None, questions=None, results=None):
    response = {}
    response['reference'] = reference

    field = {}
    if agenda is not None:
        field['agenda'] = agenda
    if questions is not None:
        field['questions'] = questions
    if results is not None:
        field['results'] = results
    response['field'] = field

    return response, 200

def error_response(code, type, message):
    return {
        "code": code,
        "type": type,
        "message": message
    }, code

### Test Functions ###

def test_firebase(request):
    path = request.args.get('path')
    list = Firestore.to_list(path)
    dict = Firestore.to_dict(path)
    print(f"Returned: {list}, {dict}", flush=True)
    return "OK", 200

def test_zip(request):
    zip_directory("/tmp/chroma", "/tmp/chroma.zip")
    shutil.rmtree("/tmp/chroma")
    unzip_file("/tmp/chroma.zip", "/tmp/chroma")
    return "OK", 200
