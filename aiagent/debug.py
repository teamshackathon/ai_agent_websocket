import json

import func
from func import error_response
from firebase import Firestore

def test_firebase(request):
    path = request.args.get('path')
    list = Firestore.to_list(path)
    dict = Firestore.to_dict(path)
    print(f"Returned: {list}, {dict}", flush=True)
    return "OK", 200

def test_zip(request):
    func.zip_directory("/tmp/chroma", "/tmp/chroma.zip")
    func.shutil.rmtree("/tmp/chroma")
    func.unzip_file("/tmp/chroma.zip", "/tmp/chroma")
    return "OK", 200

def set_store_value(request):
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


def copy_store_field(request):
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

def show_store_field(request):
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