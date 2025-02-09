import os

from firebase_admin import firestore, storage
import firebase_admin

firebase_admin.initialize_app(options={"projectId": os.getenv("FIREBASE_PROJECT_ID")})
store_client = firestore.client()

hostname = os.getenv("FIREBASE_PROJECT_ID") + '.' + os.getenv("FIREBASE_STORAGE_DOMAIN")

class Firestorage:
    # Firebase Storageからファイルを取得する関数
    def get_bytes(blob_path):
        # Firebase Storageのバケットにアクセス
        name = hostname
        bucket = storage.bucket(name)
        # バケットからBlobを取得
        blob = bucket.blob(blob_path)
        return blob.download_as_bytes()

    def put_file(blob_path, filename):
        name = hostname
        bucket = storage.bucket(name)
        # バケットにBlobをアップロード
        blob = bucket.blob(blob_path)
        blob.upload_from_filename(filename)

class Firestore:
    # パス階層に応じて処理を行う関数
    def to_list(path:str):
        doc_ref = Firestore.get_ref(path)
        if isinstance(doc_ref, firestore.CollectionReference):
            docs = doc_ref.stream()
            return [doc.id for doc in docs]
        elif isinstance(doc_ref, firestore.DocumentReference):
            docs = doc_ref.collections()
            if docs is not None:
                return [doc.id for doc in docs]
            doc_dict = doc_ref.get().to_dict()
            return doc_dict['collections'] if 'collections' in doc_dict else []

        return []

    def to_dict(path:str):
        doc_ref = Firestore.get_ref(path)
        if isinstance(doc_ref, firestore.CollectionReference):
            return {}
        elif isinstance(doc_ref, firestore.DocumentReference):
            doc = doc_ref.get()
            doc_dict = doc.to_dict()
            if doc_dict:
                doc_dict.pop('collections', None)
            return doc_dict

        return {}

    def get_ref(path:str):
        if not path or path == '':
            return None

        path = path.rstrip('/')
        # パスをスラッシュで分割
        path_parts = path.split('/')

        doc_ref = store_client.collection(path_parts[0])
        # パスの各要素を表示
        for i in range(1, len(path_parts)):
            if isinstance(doc_ref, firestore.CollectionReference):
                doc_ref = doc_ref.document(path_parts[i])
            elif isinstance(doc_ref, firestore.DocumentReference):
                doc_ref = doc_ref.collection(path_parts[i])

        return doc_ref

    def set_field(path:str, field, value):
        doc_ref = Firestore.get_ref(path)
        doc_ref.set({field: value}, merge=True)