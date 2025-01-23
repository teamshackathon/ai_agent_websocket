
1. 初期ビルド
```
以下の条件を満たす環境を構築するWebアプリの初期コードを作成してください。

- クライアントサイド:Next.js
- サーバーサイド: CloudFunction 言語: Go
- クライアントアプリからWebsocket通信でサーバーサイドに音声データを送信する
- サーバーサイドでは生成AI(Speech to Text)に音声データを送信し、テキストデータを取得する
```

2. 問題生成プロンプト
```
以下の`教材テキスト`を読み込んでください。

$(教材テキスト)
```

```
講師が`教材テキスト`を元に授業を行った際の`授業音声テキスト`を読み込んでください。

$(授業音声テキスト)
```

```
あなたは日本の中学生の英語教師です。
`教示テキスト`を元に`授業音声テキスト`を加味して生徒に対して小テストを作成します。
以下の要件に従って、問題文を作成してください。

- 問題数は全部で4問で各問いにタイトルを付与します。
- 問題は重要度の高い部分から優先的に作成します。
- `授業音声テキスト`で解説されている箇所は重要度の高い課題として扱います。
- 問題は`問題タイプ`のいづれかを使用して`問題 Schema`を元としたJSON形式で出力してください。
- 問題タイプは出題する問題に対して適切と考えられる形式のものを使用してください。

**問題タイプ**
1. Anaume
    - 問題文中に空白(アンダーバー: _)を埋め込み、空白部分を回答させる
    - 回答は自由入力
2. Sentaku
    - 問題文中に空白(アンダーバー: _)を埋め込み、空白部分を回答させる
    - 回答は回答項目から選択する
    - 回答項目は正解を含む3つを用意
3. Kijutsu
    - 問題文はある単語に対しての説明をしている
    - 回答は自由入力

**問題 Schema**
{
    "type": "object",
    "required": ["questions"],
    "additionalProperties": false,
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "required": ["title", "format"],
                "additionalProperties": false,
                "properties": {
                    "title": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 10
                    },
                    "format": {
                        "type": "string",
                        "enum": ["Anaume", "Sentaku", "Kijutsu"]
                    }
                }
            }
        }
    },
    "dependencies": {
        "format": {
            "oneOf": [
                {
                    "properties": {
                        "format": {
                            "enum": ["Anaume"]
                        },
                        "question": {
                            "$ref": "#/definitions/question"
                        },
                        "correct_answer": {
                            "$ref": "#/definitions/correct_answer"
                        }
                    }
                },
                {
                    "properties": {
                        "format": {
                            "enum": ["Sentaku"]
                        },
                        "question": {
                            "$ref": "#/definitions/question"
                        },
                        "options": {
                            "$ref": "#/definitions/options"
                        },
                        "correct_answer": {
                            "$ref": "#/definitions/correct_answer"
                        }
                        "correct_num": {
                            "$ref": "#/definitions/correct_num"
                        }
                    }
                },
                {
                    "properties": {
                        "format": {
                            "enum": ["Kijutsu"]
                        },
                        "question": {
                            "$ref": "#/definitions/question"
                        },
                        "correct_answer": {
                            "$ref": "#/definitions/correct_answer"
                        }
                    }
                }
            ]
        }
    },
    "definitions": {
        "question": {
            "type": "string",
            "minLength": 20,
            "maxLength": 100
        },
        "options": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["item_num", "item_word"],
                "additionalProperties": false,
                "properties": {
                    "item_num": {
                        "type": "number"
                    },
                    "item_word": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 20
                    }
                }
            }
        },
        "correct_answer": {
            "type": "string",
            "minLength": 20,
            "maxLength": 100
        },
        "correct_num": {
            "type": "number"
        }
    }
}
```


3. 回答採点
```
回答データはJson形式で採点には以下のルールが適用されます。
- 回答データは順不同です。
- 回答データの`title`は問題データの`title`と合致しているものに対する回答です。
- 回答内容が数値の場合、問題の`correct_num`の値と比較する。

**回答 Schema**
{
    "type": "object",
    "required": ["answers"],
    "additionalProperties": false,
    "properties": {
        "answers": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["title"],
                "additionalProperties": false,
                "properties": {
                    "title": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 10
                    },
                    "answer": {
                        "oneOf": [
                            {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": 100
                            },
                            {
                                "type": "number"
                            }
                        ]
                    }
                }
            }
        }
    }
}
```

```
以下の問題データを読み込んでください。

$(問題データ)
```

```
以下の回答データを読み込んでください。

$(回答データ)
```

```
先に読み込んだ問題データに対して、回答データが正解かどうかを採点してください。
```