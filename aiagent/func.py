import base64
import zipfile
import shutil
import os
import json
from typing import Dict, Tuple, Union

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

def hello_ai(request):
    model = GoogleGenerativeAI(model="gemini-2.0-flash-exp")
    output = model.invoke("自己紹介をしてください。")
    print(output, flush=True)

    return (f"Hello AI. \n <pre>{output}</pre>"), 200

def chats_as_student(request):

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


def chats_as_teacher(request):

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


def create_questions(request):
    # JSONデータを取得
    data = request.get_json()

    reference = data.get('reference')
    if reference is None:
        return error_response(400, 'INPUT_ERROR', "reference is required.")

    # TODO Noticeパラメータ取得の実装予定

    dict_ref = parse_path(str(reference))

    start_page, finish_page, err = prepare_page(dict_ref)
    if err:
        return error_response(400, 'SETTING_ERROR', err)

    db, err = prepare_chroma(dict_ref)
    if err:
        return error_response(400, 'SETTING_ERROR', err)

    # 小テスト格納フィールド名
    field_name = "questions_draft"
    questions_data = create_questions_from_vector(db, start_page, finish_page)
    Firestore.set_field(reference, field_name, questions_data)

    # TODO Notice実装予定

    return created_response(reference, questions=field_name)


def answered_questions(request):
    # JSONデータを取得
    data = request.get_json()

    reference = data.get('reference')
    if reference is None:
        return error_response(400, 'INPUT_ERROR', "reference is required.")

    dict_ref = parse_path(str(reference))
    dict_ref_field = Firestore.to_dict(reference)

    dict_answers = dict_ref_field.get('questions_answer')
    if dict_answers is None:
        return error_response(400, 'INPUT_ERROR', "cant find questions_answer field.")

    dict_agenda, err = prepare_agenda(dict_ref)
    if err:
        return error_response(400, 'SETTING_ERROR', err)

    dict_questions, err = prepare_questions(dict_ref)
    if err:
        return error_response(400, 'SETTING_ERROR', err)

    db, err = prepare_chroma(dict_ref)
    if err:
        return error_response(400, 'SETTING_ERROR', err)

    result_data = create_questions_result_from_vector(db, dict_questions, dict_answers)

    # 小テスト採点結果格納フィールド名
    result_field_name = "questions_result"
    Firestore.set_field(reference, result_field_name, result_data)

    homeworks_data = create_homeworks_from_vector(dict_agenda, dict_questions, result_data)

    # 宿題格納フィールド名
    homeworks_field_name = "homeworks"
    Firestore.set_field(reference, homeworks_field_name, homeworks_data)

    return created_response(reference, questions_result=result_field_name, homeworks=homeworks_field_name)


def submit_homework(request):
    # JSONデータを取得
    data = request.get_json()

    reference = data.get('reference')
    if reference is None:
        return error_response(400, 'INPUT_ERROR', "reference is required.")

    dict_ref = parse_path(str(reference))
    dict_ref_field = Firestore.to_dict(reference)

    dict_homeworks_answer = dict_ref_field.get('homeworks_answer')
    if dict_homeworks_answer is None:
        return error_response(400, 'INPUT_ERROR', "cant find homeworks_answer field.")

    dict_homeworks, err = prepare_homeworks(dict_ref)
    if err:
        return error_response(400, 'SETTING_ERROR', err)

    db, err = prepare_chroma(dict_ref)
    if err:
        return error_response(400, 'SETTING_ERROR', err)

    homeworks_result = create_homeworks_result_from_vector(db, dict_homeworks, dict_homeworks_answer)

    # 小テスト採点結果格納フィールド名
    result_field_name = "homeworks_result"
    Firestore.set_field(reference, result_field_name, homeworks_result)

    return created_response(reference, homeworks_result=result_field_name)


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
    agenda_data = chain.invoke(query)
    print(agenda_data, flush=True)

    return agenda_data


def create_questions_from_vector(db, start_page, finish_page):
    retriever = db.as_retriever()

    rule_questions_runnable = RunnableLambda(lambda x: jprompt.RULE_QUESTIONS)
    schema_questions_runnable = RunnableLambda(lambda x: jschema.SCHEMA_QUESTIONS)
    questions_sample_runnable = RunnableLambda(lambda x: jschema.QUESTIONS_SAMPLE)

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

    出力形式:"""
    {schema}
    """

    出力例:"""
    {schema_sample}
    """
    ''')

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")

    chain = (
            {"context": retriever, "question": RunnablePassthrough(), "rule": rule_questions_runnable, "schema": schema_questions_runnable, "schema_sample": questions_sample_runnable}
            | prompt
            | llm
            | StrOutputParser()
            | replaced2json
    )

    query = f"授業の小テストを作成します。`文脈`の**page {start_page}**から**page {finish_page}**の内容を元に問題を**4題以上**作成してください。問題の重要度を鑑みて`出力形式`の`score`の点数設定をしてください。"
    # Json形式の小テスト作成
    questions_data = chain.invoke(query)
    print(questions_data, flush=True)

    return format_json(questions_data, key="questions")


def create_questions_result_from_vector(db, dict_questions, dict_answers):
    retriever = db.as_retriever()

    questions_runnable = RunnableLambda(lambda x: dict_questions)  # 小テスト問題内容（小テストの正解・得点を使用する）
    answers_runnable = RunnableLambda(lambda x: dict_answers)  # 学生の解答

    rule_results_runnable = RunnableLambda(lambda x: jprompt.RULE_RESULTS)
    schema_results_runnable = RunnableLambda(lambda x: jschema.SCHEMA_RESULTS)  # 採点構造
    results_sample_runnable = RunnableLambda(lambda x: jschema.RESULTS_SAMPLE)  # 学生の回答に対する採点結果の例

    prompt = ChatPromptTemplate.from_template('''\
    以下の文脈だけを踏まえて質問に回答してください。

    文脈:"""
    {context}
    """

    問題:"""
    {question}
    """

    採点ルール:"""
    {rule}
    """

    質問:{query}

    採点定義:"""
    {schema_score}
    """

    学生の回答:"""
    {answer}
    """

    採点結果構造の出力形式の例:"""
    {answer_score}
    """
    ''')

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")

    chain = (
            {"context": retriever, "question": questions_runnable, "rule": rule_results_runnable,
             "query": RunnablePassthrough(), "schema_score": schema_results_runnable, "answer": answers_runnable,
             "answer_score": results_sample_runnable}
            | prompt
            | llm
            | StrOutputParser()
            | replaced2json
    )

    query = f"`問題`の内容（正解、得点）元に`採点ルール`に基づき、`学生の回答`を採点してください。\n採点結果は`採点定義`の形式で出力してください。"
    # Json形式の採点結果作成
    results_data = chain.invoke(query)
    print(results_data, flush=True)

    return format_json(results_data, key="results")


def create_homeworks_from_vector(dict_agenda, dict_questions, dict_results):
    agenda_runnable = RunnableLambda(lambda x: dict_agenda) # 授業のアジェンダ
    questions_runnable = RunnableLambda(lambda x: dict_questions) # 小テスト問題内容（小テストの正解・得点を使用する）
    results_runnable = RunnableLambda(lambda x: dict_results) # 小テスト採点結果

    rule_questions_runnable = RunnableLambda(lambda x: jprompt.RULE_QUESTIONS) # 問題作成時の共通ルール
    rule_homework_runnable = RunnableLambda(lambda x: jprompt.RULE_HOMEWORK) # 宿題作成時のルール
    schema_questions_runnable = RunnableLambda(lambda x: jschema.SCHEMA_QUESTIONS) # 小テストの構造定義
    questions_sample_runnable = RunnableLambda(lambda x: jschema.QUESTIONS_SAMPLE) # 小テストの構造例

    prompt = ChatPromptTemplate.from_template('''\
    質問:{query}
    
    出題のルール:"""
    {rule1}
    {rule2}
    """
    
    アジェンダ:"""
    {agenda}
    """
    
    問題データ:"""
    {question}
    """
    
    採点結果:"""
    {score}
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
            {"query": RunnablePassthrough(), "rule1": rule_questions_runnable, "rule2": rule_homework_runnable,
             "agenda": agenda_runnable, "question": questions_runnable, "score": results_runnable,
             "schema": schema_questions_runnable, "schema_sample": questions_sample_runnable}
            | prompt
            | llm
            | StrOutputParser()
            | replaced2json
    )

    query = f"`採点結果`から回答者の苦手な分野を特定し、その分野を克服できるような宿題を作成してください。"
    # Json形式の採点結果作成
    homework_data = chain.invoke(query)
    print(homework_data, flush=True)

    return format_json(homework_data, key="questions")


def create_homeworks_result_from_vector(db, dict_homework, dict_answers):
    retriever = db.as_retriever()

    homework_runnable = RunnableLambda(lambda x: dict_homework) # 宿題内容（宿題の正解・得点を使用する）
    answers_runnable = RunnableLambda(lambda x: dict_answers) # 学生の解答

    rule_results_runnable = RunnableLambda(lambda x: jprompt.RULE_RESULTS) # 採点ルールの定義
    schema_result_runnable = RunnableLambda(lambda x: jschema.SCHEMA_RESULTS) # 採点構造
    results_sample_runnable = RunnableLambda(lambda x: jschema.RESULTS_SAMPLE) # 学生の回答に対する採点結果構造の例

    prompt = ChatPromptTemplate.from_template('''\
    以下の文脈だけを踏まえて質問に回答してください。
    
    文脈:"""
    {context}
    """
    
    問題:"""
    {homework}
    """
    
    採点ルール:"""
    {rule}
    """
    
    質問:{query}
    
    採点定義:"""
    {schema_score}
    """
    
    学生の回答:"""
    {answer}
    """
    
    採点結果構造の出力形式の例:"""
    {answer_score}
    """
    ''')

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")

    chain = (
            {"context": retriever, "homework": homework_runnable, "rule": rule_results_runnable,
             "query": RunnablePassthrough(), "schema_score": schema_result_runnable, "answer": answers_runnable,
             "answer_score": results_sample_runnable}
            | prompt
            | llm
            | StrOutputParser()
            | replaced2json
    )

    query = f"`問題`の内容（正解、得点）元に`採点ルール`に基づき、`学生の回答`を採点してください。\n採点結果は`採点定義`の形式で出力してください。"
    # Json形式の採点結果作成
    homework_data = chain.invoke(query)
    print(homework_data, flush=True)

    return format_json(homework_data, key="results")


@chain
def replaced2json(output: str) -> str:
  replaced_output = output.replace('```json', '').replace('```', '')
  # replaced_output = json.loads(replaced_output) # これを加えるとdict型になってしまう
  return replaced_output


### Making Resource ###

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

def prepare_page(dict_ref) -> Union[tuple[str, str, None], tuple[None, None, str]]:
    lesson_path = "/".join([dict_ref.get('year',''), dict_ref.get('class',''), 'common', dict_ref.get('subject',''), 'lessons', dict_ref.get('lesson_id','')])
    dict_field = Firestore.to_dict(lesson_path)

    if not dict_field:
        return None, None, "cant find lesson."

    start_page = dict_field.get('start_page')
    finish_page = dict_field.get('finish_page')

    if start_page is None or finish_page is None:
        return None, None, "cant find start_page/finish_page."

    return start_page, finish_page, None

def prepare_agenda(dict_ref) -> Union[tuple[Dict, None], tuple[None, str]]:
    lesson_path = "/".join([dict_ref.get('year',''), dict_ref.get('class',''), 'common', dict_ref.get('subject',''), 'lessons', dict_ref.get('lesson_id','')])
    dict_field = Firestore.to_dict(lesson_path)

    if not dict_field:
        return None, "cant find lesson."

    dict_agenda = dict_field.get('agenda_publish')

    if dict_agenda is None:
        return None, "cant find agenda_publish."

    return dict_agenda, None

def prepare_questions(dict_ref) -> Union[tuple[Dict, None], tuple[None, str]]:
    lesson_path = "/".join([dict_ref.get('year',''), dict_ref.get('class',''), 'common', dict_ref.get('subject',''), 'lessons', dict_ref.get('lesson_id','')])
    dict_field = Firestore.to_dict(lesson_path)

    if not dict_field:
        return None, "cant find lesson."

    dict_questions = dict_field.get('questions_publish')

    if dict_questions is None:
        return None, "cant find questions_publish."

    return dict_questions, None

def prepare_homeworks(dict_ref) -> Union[tuple[Dict, None], tuple[None, str]]:
    student_path = "/".join([dict_ref.get('year',''), dict_ref.get('class',''), 'common', dict_ref.get('subject',''), 'lessons', dict_ref.get('lesson_id',''), 'students', dict_ref.get('student')])
    dict_field = Firestore.to_dict(student_path)

    if not dict_field:
        return None, "cant find student."

    dict_homework = dict_field.get('homeworks')

    if dict_homework is None:
        return None, "cant find homeworks."

    return dict_homework, None

### For Chroma ###

def prepare_chroma(dict_ref) -> Union[tuple[None, str], tuple[Chroma, None]]:
    subject_path = "/".join([dict_ref.get('year',''), dict_ref.get('class',''), 'common', dict_ref.get('subject','')])
    dict_field = Firestore.to_dict(subject_path)

    if dict_field is None or dict_field == {}:
        return None, "Failed find text path."

    # ChromaDBをfirestoreから取得
    text_chroma_path = dict_field.get('text_chroma')
    if text_chroma_path is None:
        return None, "Failed make agenda before making question."

    # Chroma DB path
    chroma_path = "/tmp/chroma"
    # ChromaDBをfirestorageから取得
    restore_chroma(text_chroma_path, chroma_path)
    # ChromaDBを作成
    db = create_chroma(chroma_path)

    return db, None


def store_chroma(persist_directory, dict_ref):
    # chromaディレクトリをZipファイル化
    zip_filename = f"chroma_{dict_ref.get('year','year')}_{dict_ref.get('class','class')}_{dict_ref.get('subject','subject')}.zip"
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

def format_json(data, key=None):
    '''
    JSON文字列をオブジェクトにして返す。
    キーが指定されている場合はキーは以下を返す
    :param data: JSON文字列
    :param key: キー名
    :return: オブジェクト
    '''
    obj = json.loads(data)
    if not key: return obj
    if isinstance(obj, list): return obj
    if isinstance(obj, dict): return obj.get(key)
    return obj

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
    :return: object[year, class, common, subject, lessons, lesson_id, students, student]
    '''
    keys = ['year', 'class', 'common', 'subject', 'lessons', 'lesson_id', 'students', 'student']
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

def created_response(reference, agenda=None, questions=None, questions_result=None, homeworks=None, homeworks_result=None):
    response = {}
    response['reference'] = reference

    field = {}
    if agenda is not None:
        field['agenda'] = agenda
    if questions is not None:
        field['questions'] = questions
    if questions_result is not None:
        field['questions_result'] = questions_result
    if homeworks is not None:
        field['homeworks'] = homeworks
    if homeworks_result is not None:
        field['homeworks_result'] = homeworks_result
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

def test_store_value(request):
    # JSONデータを取得
    data = request.get_json()

    reference = data.get('reference')
    if reference is None:
        return error_response(400, 'INPUT_ERROR', "reference is required.")

    key = data.get('key')
    if key is None:
        return error_response(400, 'INPUT_ERROR', "key is required.")

    value = data.get('value')
    if value is None:
        return error_response(400, 'INPUT_ERROR', "value is required.")

    Firestore.set_field(reference, key, value)
    return "OK", 200


def test_copy_field(request):
    # JSONデータを取得
    data = request.get_json()

    reference = data.get('reference')
    if reference is None:
        return error_response(400, 'INPUT_ERROR', "reference is required.")

    fromKey = data.get('fromKey')
    if fromKey is None:
        return error_response(400, 'INPUT_ERROR', "fromKey is required.")

    toKey = data.get('toKey')
    if toKey is None:
        return error_response(400, 'INPUT_ERROR', "toKey is required.")

    dict_field = Firestore.to_dict(reference)
    if not dict_field:
        return error_response(400, 'INPUT_ERROR', "not exist reference.")

    dict_fromKey = dict_field.get(fromKey)
    if not dict_fromKey:
        return error_response(400, 'INPUT_ERROR', "not exist fromKey field.")

    Firestore.set_field(reference, toKey, dict_fromKey)
    return "OK", 200

def test_show_field(request):
    # JSONデータを取得
    data = request.get_json()

    reference = data.get('reference')
    if reference is None:
        return error_response(400, 'INPUT_ERROR', "reference is required.")

    key = data.get('key')
    if key is None:
        return error_response(400, 'INPUT_ERROR', "key is required.")

    dict_field = Firestore.to_dict(reference)
    if not dict_field:
        return error_response(400, 'INPUT_ERROR', "not exist reference.")

    return json.dumps(dict_field.get(key, []), ensure_ascii=False, sort_keys=True), 200