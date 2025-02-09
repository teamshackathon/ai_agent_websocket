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

import functions_framework
import jschema
import jprompt
from func import error_response, created_response
from firebase import Firestore, Firestorage



@functions_framework.http
def create_analysis_result(request):
    # JSONデータを取得
    data = request.get_json()

    reference = data.get('reference')
    if reference is None:
        return error_response(400, 'INPUT_ERROR', "reference is required.")

    max_sample_num = data.get('max_sample_num')
    if max_sample_num is None:
        return error_response(400, 'INPUT_ERROR', "max_sample_num is required.")


def create_sample_ansers(dict_ref):

    return "OK", 200