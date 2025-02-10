import io
import json
import random
import time
import textwrap
import threading
import numpy as np
import matplotlib.patches as mpatches
import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

import jschema
import jprompt
from func import error_response, created_response, replaced2json, format_json, prepare_agenda, prepare_questions, parse_path, notification, lesson_info
from firebase import Firestore, Firestorage

# 日本語フォントを指定（グラフ画像内日本語用）
plt.rcParams["font.family"] = "IPAPGothic"

def create_summary(request):
    # JSONデータを取得
    data = request.get_json()
    if not data:
        return error_response(400, 'INPUT_ERROR', "get request is not allow.")

    reference = data.get('reference')
    if reference is None:
        return error_response(400, 'INPUT_ERROR', "reference is required.")

    dict_ref = parse_path(reference)

    dict_agenda, err = prepare_agenda(dict_ref)
    if err:
        return error_response(400, 'SETTING_ERROR', err)

    dict_questions, err = prepare_questions(dict_ref)
    if err:
        return error_response(400, 'SETTING_ERROR', err)

    notices = data.get('notice')
    if notices and isinstance(notices, list):
        for notice in notices:
            print(f"[create_summary] prepare notice: {notice}", flush=True)
            notification(notice, "小テストの集計を受け付けました", "小テストの集計・分析結果が作成されるまで今しばらくお待ち下さい。")

    # バックグラウンドで処理を実行
    threading.Thread(target=background_process, args=(data, reference, dict_agenda, dict_questions)).start()

    return created_response(reference)


def background_process(data, reference, dict_agenda, dict_questions):
    # 生徒の採点結果一覧を取得
    list_result = collect_results(reference)

    max_sample_num = data.get('max_sample_num')
    if max_sample_num or not isinstance(max_sample_num, int):
        # デフォルト回答数を設定
        max_sample_num = 10

    if len(list_result) < max_sample_num:
        # ダミー採点結果を作成
        dummy_results = create_dummy_results(dict_questions, max_sample_num - len(list_result))
        if dummy_results and len(dummy_results) > 0:
            # ダミー採点結果を採点結果一覧に追加
            list_result.extend(dummy_results)

    dict_ref = parse_path(reference)
    # グラフ画像の基底パス
    storage_path = "/".join(["graph_img", dict_ref.get('subject',''), dict_ref.get('lesson_id','')])

    # 正答率の辞書を作成
    dict_title_rates = make_dictionary_of_correct(list_result)
    # 問題毎の正答数を集計
    dict_title_stats = collect_correct_incorrect(list_result)
    print(f"[create_summary] collected questions_result. ref:{reference}", flush=True)

    # 正答率グラフを生成
    img_path = create_correct_graph(dict_title_rates, storage_path)
    # 問題毎の正答グラフを生成
    dict_img_path = create_correct_graph_by_title(dict_title_stats, storage_path)
    print(f"[create_summary] created summary graph. ref:{reference}", flush=True)

    # 小テストの分析結果を取得
    md_analysis = analysis_questions_result(dict_agenda, dict_questions, dict_title_rates, dict_title_stats)
    print(f"[create_summary] analysis completed. ref:{reference}", flush=True)

    field_name = 'summary'
    dict_summary = {'markdown': md_analysis}
    dict_summary['images'] = []
    dict_summary['images'].append(img_path)
    dict_summary['images'].extend(dict_img_path.values())
    # Firestoreに分析結果とグラフ画像パスを格納
    Firestore.set_field(reference, field_name, dict_summary)

    notices = data.get('notice')
    if notices:
        dict_lesson = lesson_info(dict_ref)
        for notice in notices:
            print(f"[create_summary] notice: {notice}", flush=True)
            dict_teacher = Firestore.to_dict(f"teachers/{notice}")

            message = f"""
                        {dict_teacher.get('name')}先生
                        授業お疲れ様でした。いつもありがとうございます。
                        {dict_lesson.get('lesson_class','担当クラス')}の{dict_lesson.get('subject_name','')}小テスト（{dict_lesson.get('lesson_count')}）の回収・分析が完了いたしました。
                        
                        分析結果の詳細につきましては、授業の分析メニューをご確認ください。
                        ご不明な点がございましたら、お気軽にチャットメニューから問い合わせてください。
                        
                        引き続き、先生の業務をサポートさせていただきます。
                        
                        よろしくお願いいたします。 @Manabiya AI
                        """
            message = textwrap.dedent(message)[1:-1]

            notification(notice, "小テストの集計が完了しました", message)

    print(f"[create_summary] finish. ref:{reference}", flush=True)

def collect_results(reference):
    # レッスンは以下の生徒のパス
    students_path = reference + "/students"
    list_result = []

    # レッスン配下の生徒一覧を取り出す
    list_student = Firestore.to_list(students_path)
    for student in list_student:
        # 生徒毎の採点結果を取得
        dict_student = Firestore.to_dict(students_path + "/" + student)
        result = dict_student.get('questions_result')
        if result:
            list_result.append(result)

    return list_result


def create_dummy_results(dict_questions, max_sample_num):
    # ランダム回答データを生成
    random_answers = create_sample_answers_from_vector(dict_questions)
    json_random_answers = json.loads(random_answers)
    # ダミーの採点結果一覧を作成
    dummy_results = make_dummy_result(dict_questions, json_random_answers, max_sample_num)

    return dummy_results


def create_sample_answers_from_vector(dict_questions):
    prompt = ChatPromptTemplate.from_template('''\
    授業の小テストの問題データに対してランダムな回答データを作成します。
    
    問題データ:"""
    {question}
    """
    
    ランダム回答ルール:"""
    {rule_random_answers}
    """
    
    質問:{query}
    
    問題形式:"""
    {schema_question}
    """
    
    ランダム回答形式:"""
    {schema_random_answers}
    """
    ''')

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")

    chain = (
            {
                "question":RunnableLambda(lambda x: dict_questions), # 小テスト問題内容（小テストの正解・得点を使用する）
                "schema_question":RunnableLambda(lambda x: jschema.SCHEMA_QUESTIONS),
                "schema_random_answers":RunnableLambda(lambda x: jschema.SCHEMA_RANDOM_ANSWERS),
                "query": RunnablePassthrough(),
                "rule_random_answers":RunnableLambda(lambda x: jprompt.RULE_RANDOM_ANSWERS)
            }
            | prompt
            | llm
            | StrOutputParser()
            | replaced2json
    )

    query = f"`問題形式`を覚えて、`問題データ`に対する`ランダム回答データ`を作成してください。`ランダム回答データ`の作成は、`ランダム回答ルール`に従ってください。出力結果は`ランダム回答データ`のみとします。"
    # JSON形式のランダム回答結果を作成
    answers_data = chain.invoke(query)
    print(answers_data, flush=True)

    return answers_data


def create_dummy_result_from_vector(dict_questions, dict_answers):
    prompt = ChatPromptTemplate.from_template('''\
    以下の文脈だけを踏まえて質問に回答してください。

    問題データ:"""
    {question}
    """

    採点ルール:"""
    {rule}
    """

    質問:{query}

    回答データ:"""
    {answer}
    """
    
    採点定義:"""
    {schema_score}
    """
    ''')

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")

    chain = (
            {
                "question": RunnableLambda(lambda x: dict_questions),  # 小テスト問題内容（小テストの正解・得点を使用する）
                "rule": RunnableLambda(lambda x: jprompt.RULE_DUMMY_RESULTS),
                "query": RunnablePassthrough(),
                "answer": RunnableLambda(lambda x: dict_answers),
                "schema_score": RunnableLambda(lambda x: jschema.SCHEMA_RESULTS),
            }
            | prompt
            | llm
            | StrOutputParser()
            | replaced2json
    )

    query = f"`問題データ`の内容（正解、得点）元に`採点ルール`に基づき、`回答データ`を採点してください。採点結果は`採点定義`のJSON形式で出力してください。"
    # JSON形式のランダム回答結果を作成
    results_data = chain.invoke(query)
    print(results_data, flush=True)

    return results_data


def analysis_questions_result(dict_agenda, dict_questions, dict_title_rates, dict_title_stats):
    prompt = ChatPromptTemplate.from_template('''\
    以下の内容を踏まえて質問に回答してください。

    アジェンダ:"""
    {agenda}
    """

    問題:"""
    {question}
    """

    質問:{query}

    学生の回答：正答率:"""
    {title_correct_rates}
    """

    学生の回答：各タイトルに対する正解・不正解の回答の集計結果:"""
    {title_stats}
    """

    ''')

    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp")

    chain = (
            {
                "agenda": RunnableLambda(lambda x: dict_agenda),  # 授業のアジェンダ
                "question": RunnableLambda(lambda x: dict_questions), # 小テスト問題内容（小テストの正解・得点を使用する）
                # "rule":RunnableLambda(lambda x: RULE_ANSWERED_ANALYSIS), # 分析のルール
                "query": RunnablePassthrough(),
                # "schema_answer_analysis":RunnableLambda(lambda x: SCHEMA_ANSWERED_ANALYSIS), # 分析構造の定義（outputの型）
                "title_correct_rates": RunnableLambda(lambda x: dict_title_rates),  # 正答率
                "title_stats": RunnableLambda(lambda x: dict_title_stats)  # 各タイトルに対する正解・不正解の回答を集計
            }
            | prompt
            | llm
            | StrOutputParser()
            | replaced2json
    )

    query = f"あなたは先生のアシスタントです。`agenda`は授業の流れです。小テストの内容である`question`（正解、得点）と学生の回答結果の簡易的な分析結果である`title_correct_rates`と`title_stats`に基づき、学生の授業の理解度を分析してください。 理解度の分析結果を踏まえ、次回の授業で学生に対しどのようなフォローを入れるべきかアドバイスをください。 返事は必要ありません"
    # マークダウン形式の分析結果を生成
    md_analysis = chain.invoke(query)
    print(md_analysis, flush=True)

    return md_analysis


def make_dummy_result(dict_questions, json_random_answers, max_sample_num):
    list_random_answers = json_random_answers.get("random_answers")

    # 回答リスト
    list_results = []
    for i in range(max_sample_num):
        dict_answers = {}
        answer_items = []
        dict_answers["answers"] = answer_items
        for random_answers in list_random_answers:
            random_answer = random_answers.get('answer')
            answer = {}
            answer['title'] = random_answers.get('title')
            answer['answer'] = random.choice(random_answer)
            answer_items.append(answer)

        results = create_dummy_result_from_vector(dict_questions, dict_answers)
        json_results = format_json(results, 'results')
        # 採点結果に追加
        list_results.append(json_results)
        # トークン超過対策
        time.sleep(5)

    return list_results


def make_dictionary_of_correct(list_results):
    # @title 各問題(title)に対するcorrectを集計する辞書の作成

    dict_title_correct = {}  # 各titleに対するcorrectを集計する辞書

    for results in list_results:
        for result in results:
            title = result.get("title", "")
            correct = result.get("correct", False)
            if title in dict_title_correct:
                dict_title_correct[title].append(correct)  # 既存のtitleにcorrectを追加
            else:
                dict_title_correct[title] = [correct]  # 新しいtitleにcorrectを追加

    dict_title_rates = {}  # 各titleと正答率を格納する辞書

    for title, corrects in dict_title_correct.items():
        correct_count = corrects.count(True)
        total_count = len(corrects)
        correct_rate = (correct_count / total_count) * 100
        dict_title_rates[title] = correct_rate  # titleと正答率を辞書に追加

    return dict_title_rates


def collect_correct_incorrect(list_results):
    # @title 各問題(title)に対する正解・不正解の回答数を集計
    dict_title_stats = {}

    for results in list_results:
        for result in results:
            title = result.get("title", "")
            is_correct = result.get("correct", False)  # Trueなら正解、Falseなら不正解
            user_answer = result.get("user_answer")

            if user_answer is None:
                user_answer = ''
            elif isinstance(user_answer, int):
                user_answer = str(user_answer)

            # 初めてのタイトルなら、タイトル名、正解、不正解の辞書を初期化
            if title not in dict_title_stats:
                dict_title_stats[title] = {
                    "title": title,
                    "correct": {},
                    "incorrect": {}
                }

            if is_correct:
                # 正解の場合、"correct" 辞書内で user_answer のカウントを更新
                if user_answer in dict_title_stats[title]["correct"]:
                    dict_title_stats[title]["correct"][user_answer] += 1
                else:
                    dict_title_stats[title]["correct"][user_answer] = 1
            else:
                # 不正解の場合、"incorrect" 辞書内で user_answer のカウントを更新
                if user_answer in dict_title_stats[title]["incorrect"]:
                    dict_title_stats[title]["incorrect"][user_answer] += 1
                else:
                    dict_title_stats[title]["incorrect"][user_answer] = 1

    # 辞書の values()（各タイトルの集計結果）をリストに変換して JSON 形式に変換
    #output_json_title_stats = json.dumps(list(title_stats.values()), indent=4, ensure_ascii=False)
    #print(output_json_title_stats)

    return dict_title_stats


def create_correct_graph(dict_title_rates, storage_path):
    titles = list(dict_title_rates.keys())
    rates = list(dict_title_rates.values())

    # グラフの作成
    plt.figure(figsize=(10, 6))
    bars = plt.bar(titles, rates, color='skyblue')
    plt.xlabel('Title')
    plt.ylabel('正答率 (%)')
    plt.title('各Titleの正答率')
    plt.ylim(0, 100)

    # 各バーの上に値を表示
    for bar in bars:
        height = bar.get_height()
        plt.annotate(f'{height:.1f}%',
                     xy=(bar.get_x() + bar.get_width() / 2, height),
                     xytext=(0, 3),  # 上に3ポイントのオフセット
                     textcoords="offset points",
                     ha='center', va='bottom')

    plt.tight_layout()

    # 画像パス名
    png_image_path = storage_path + "/correct_graph.png"
    # 画像をメモリ上に保持するためのバッファ作成
    with io.BytesIO() as buf:
        plt.savefig(buf, format='png')
        buf.seek(0)  # バッファの先頭にシーク

        # 変数に画像データ（バイト列）として格納
        png_image_data = buf.getvalue()
        # 画像データをStorageに保存
        Firestorage.put_bytes(png_image_path, png_image_data, content_type='image/png')
        # 画像データ保存パスを格納

        # グラフを表示
        #plt.show()
        plt.close()

    return png_image_path


def create_correct_graph_by_title(dict_title_stats, storage_path):
    # png_images: 各タイトルごとに生成されたグラフのPNG画像データを保持する辞書
    png_images = {}

    for title, stats in dict_title_stats.items():
        # 各タイトルの正解・不正解の回答集計を取得
        correct_answers = stats.get("correct", {})
        incorrect_answers = stats.get("incorrect", {})

        # 正解・不正解のキーの和集合を取得
        all_labels = list(set(correct_answers.keys()).union(incorrect_answers.keys()))
        if not all_labels:
            continue
        all_labels.sort()

        # 表示用リスト（実際にグラフに出す選択肢のみ）
        displayed_labels = []
        displayed_counts = []
        displayed_colors = []

        # 各選択肢ごとに、正解と不正解のうちどちらか一方が非ゼロであれば表示
        for label in all_labels:
            c = correct_answers.get(label, 0)
            i = incorrect_answers.get(label, 0)
            # 本来は、どちらか一方が非ゼロとなるはず
            if c > 0 and i > 0:
                # 万が一両方非ゼロの場合、どちらか大きい方を採用（あるいは適宜対処）
                if c >= i:
                    displayed_labels.append(label)
                    displayed_counts.append(c)
                    displayed_colors.append("skyblue")
                else:
                    displayed_labels.append(label)
                    displayed_counts.append(i)
                    displayed_colors.append("salmon")
            elif c > 0:
                displayed_labels.append(label)
                displayed_counts.append(c)
                displayed_colors.append("skyblue")
            elif i > 0:
                displayed_labels.append(label)
                displayed_counts.append(i)
                displayed_colors.append("salmon")
            # 両方0の場合は表示しない

        if not displayed_labels:
            continue

        # X軸の位置を設定
        indices = np.arange(len(displayed_labels))

        plt.figure(figsize=(8, 6))
        bars = plt.bar(indices, displayed_counts, color=displayed_colors, width=0.6)

        plt.title(f"{title} - 回答頻度")
        plt.xlabel("ユーザーの回答")
        plt.ylabel("回答数")
        plt.xticks(indices, displayed_labels)

        # カスタム凡例の作成
        legend_handles = []
        if "skyblue" in displayed_colors:
            legend_handles.append(mpatches.Patch(color='skyblue', label='正解'))
        if "salmon" in displayed_colors:
            legend_handles.append(mpatches.Patch(color='salmon', label='不正解'))
        if legend_handles:
            plt.legend(handles=legend_handles)

        # 各棒グラフの上にカウント値を表示
        for bar in bars:
            height = bar.get_height()
            plt.annotate(f'{height}',
                         xy=(bar.get_x() + bar.get_width() / 2, height),
                         xytext=(0, 3),
                         textcoords="offset points",
                         ha='center', va='bottom')

        plt.tight_layout()

        # PNG画像としてメモリ上に保存し、バイトデータを取得
        with io.BytesIO() as buf:
            plt.savefig(buf, format='png')
            buf.seek(0)

            # 画像バイトデータ
            png_image_data = buf.getvalue()
            # 画像パス名
            png_image_path = storage_path + "/" + title + ".png"
            # 画像データをStorageに保存
            Firestorage.put_bytes(png_image_path, png_image_data, content_type='image/png')
            # 画像データ保存パスを格納
            png_images[title] = png_image_path

            # グラフを表示
            #plt.show()
            plt.close()

    # --- 結果の確認 ---
    #print("生成されたグラフ画像のタイトル一覧:")
    #for title in png_images.keys():
    #    print(title)

    # --- 画像の表示 ---
    #for title, img_path in png_images.items():
    #    print("png imaage: " + title + " [" + img_path + "]")

    return png_images

