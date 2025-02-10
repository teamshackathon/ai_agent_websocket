import os
import textwrap
from datetime import datetime
import vertexai
from vertexai.generative_models import GenerativeModel

from firebase import Firestore
from func import error_response, parse_chat_path

# Vertex AI の初期化
vertexai.init(project=os.getenv('GOOGLE_PROJECT_ID'), location="asia-northeast1")

def hello_ai(request):
    # モデルの指定
    model = GenerativeModel("gemini-1.5-flash-001")
    chat = model.start_chat()

    output = chat.send_message(["自己紹介をしてください。"]).text  # テキストのみでのリクエスト
    print(output, flush=True)

    return (f"Hello AI. \n <pre>{output}</pre>"), 200


def chats_as_student(request):
    # JSONデータを取得
    data = request.get_json()

    reference = data.get('reference')
    if reference is None:
        return error_response(400, 'INPUT_ERROR', "reference is required.")

    dict_ref = parse_chat_path(str(reference))

    chats_path = "/".join(['chats', dict_ref['chatId'], 'messages'])
    print(f"chat path: {chats_path}", flush=True)

    # ドキュメントを取得
    list_doc = Firestore.to_list(chats_path)
    if list_doc is None or len(list_doc) == 0:
        return error_response(400, 'INPUT_ERROR', "Nothing found in the path.")

    # 配列の中身をintに変換
    list_doc = [int(i) for i in list_doc]
    # 大きい順にソート
    list_doc.sort(reverse=True)
    # 大きいものから10個取得
    list_doc = list_doc[:10]

    chat_history = []

    prompt = '''
    あなた(ManabiyaAI)は教師です。そしてこれは生徒とのチャットです。生徒が質問をしてきました。その質問に対して回答してください。
    今までの会話の内容を元に回答してください。**回答には話者の情報は含めません。**
    
    会話の形式:"""
    話者: 会話の内容
    - 出現順で最近の発話
    """
    
    -- これまでの会話 --
    
    '''
    prompt = textwrap.dedent(prompt)[1:-1]
    add_to_history(chat_history, "Admin", prompt)

    for doc_id in list_doc:
        doc_dict = Firestore.to_dict(f"{chats_path}/{str(doc_id)}")
        if doc_dict:
            add_to_history(chat_history, doc_dict['senderId'], doc_dict['text'])

    # AIからの回答
    output = get_response_from_ai(chat_history)

    # 新規メッセージの作成
    doc_id = str(int(datetime.now().timestamp() * 1000))

    doc_path = chats_path + "/" + doc_id
    Firestore.set_field(doc_path, "messageId", doc_id)
    Firestore.set_field(doc_path, "senderId", "ManabiyaAI")
    Firestore.set_field(doc_path, "text", output)
    Firestore.set_field(doc_path, "createdAt", datetime.now())
    Firestore.set_field(doc_path, "read", False)

    return output, 200


def chats_as_teacher(request):
    # JSONデータを取得
    data = request.get_json()

    reference = data.get('reference')
    if reference is None:
        return error_response(400, 'INPUT_ERROR', "reference is required.")

    dict_ref = parse_chat_path(str(reference))

    chats_path = "/".join(['chats', dict_ref['chatId'], 'messages'])
    print(f"chat path: {chats_path}", flush=True)

    # ドキュメントを取得
    list_doc = Firestore.to_list(chats_path)
    if list_doc is None or len(list_doc) == 0:
        return error_response(400, '_ERROR', "Nothing found in the path.")

    # 配列の中身をintに変換
    list_doc = [int(i) for i in list_doc]
    # 大きい順にソート
    list_doc.sort(reverse=True)
    # 大きいものから10個取得
    list_doc = list_doc[:10]

    chat_history = []

    prompt = '''
    あなた(ManabiyaAI)はベテラン教師です。そしてこれは教師とのチャットです。教師が質問をしてきました。その質問に対して回答してください。
    今までの会話は以下の通りです。**回答には話者の情報は含めません。**

     会話の形式:"""
     話者: 会話の内容
     - 出現順で最近の発話
     """

     -- これまでの会話 --

     '''
    prompt = textwrap.dedent(prompt)[1:-1]
    add_to_history(chat_history, "Admin", prompt)

    for doc_id in list_doc:
        doc_dict = Firestore.to_dict(f"{chats_path}/{str(doc_id)}")
        if doc_dict:
            add_to_history(chat_history, doc_dict['senderId'], doc_dict['text'])

    # AIからの回答
    output = get_response_from_ai(chat_history)

    # 新規メッセージの作成
    doc_id = str(int(datetime.now().timestamp() * 1000))

    doc_path = chats_path + "/" + doc_id
    Firestore.set_field(doc_path, "messageId", doc_id)
    Firestore.set_field(doc_path, "senderId", "ManabiyaAI")
    Firestore.set_field(doc_path, "text", output)
    Firestore.set_field(doc_path, "createdAt", datetime.now())
    Firestore.set_field(doc_path, "read", False)

    return output, 200


def add_to_history(history, role, message):
    """会話の履歴を追加"""
    history.append({"role": role, "content": message})


def get_response_from_ai(history):
    model = GenerativeModel("gemini-1.5-flash-001")
    chat = model.start_chat()

    message = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history])
    print(message, flush=True)
    # チャットの履歴を元にモデルを呼び出す
    response = chat.send_message([message]).text
    # 応答を取得
    return response