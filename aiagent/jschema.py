SCHEMA_AGENDA = '''{
  "type": "object",
  "required": ["title", "agenda"],
  "properties": {
    "title": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100
    },
    "agenda": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["subtitle", "time", "description"],
        "properties": {
          "subtitle": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100
          },
          "time": {
            "type": "number"
          },
          "description": {
            "type": "string",
            "minLength": 1,
            "maxLength": 500
          }
        }
      }
    }
  }
}'''

SCHEMA_QUESTIONS = '''{
    "type": "object",
    "required": ["questions"],
    "additionalProperties": false,
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "required": ["title", "format", "score"],
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
                    },
                    "score": {
			                  "type": "number"
                    },
                    "remake": {
		                    "type": "boolean"
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
            "minLength": 1,
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
            "minLength": 1,
            "maxLength": 100
        },
        "correct_num": {
            "type": "number"
        }
    }
}'''

QUESTIONS_SAMPLE = '''{
    "questions": [
        {
            "correct_answer": "can't",
            "format": "Anaume",
            "question": "「私は泳げません」を英語で言うとき、canの否定形を使って「I _ swim.」と表現します。_に入る単語を答えなさい。",
            "score": 20,
            "title": "Canの否定形"
        },
        {
            "correct_answer": "Can you help me?",
            "correct_num": 1,
            "format": "Sentaku",
            "options": [
                {
                    "item_num": 1,
                    "item_word": "Can you help me?"
                },
                {
                    "item_num": 2,
                    "item_word": "You can help me?"
                },
                {
                    "item_num": 3,
                    "item_word": "Help me can you?"
                },
                {
                    "item_num": 4,
                    "item_word": "You help me can?"
                }
            ],
            "question": "「あなたは私を手伝うことができますか？」を英語で尋ねる時、正しい文を選びなさい。",
            "score": 30,
            "title": "Canの疑問文"
        },
        {
            "correct_answer": "可能性、許可",
            "format": "Kijutsu",
            "question": "助動詞Mayが表す意味を2つ答えなさい。",
            "score": 25,
            "title": "Mayの意味"
        },
        {
            "correct_answer": "May",
            "format": "Anaume",
            "question": "「入ってもよろしいですか？」を丁寧に英語で尋ねる時、「_ I come in?」と表現します。_に入る単語を答えなさい。",
            "score": 25,
            "title": "Mayの疑問文"
        }
    ]
}'''

SCHEMA_ANSWERS = '''{
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
}'''

ANSWERS_SUMPLE = '''{
    "answers": [
        {
            "title": "Canの否定形",
            "answer": "not can"
        },
        {
            "title": "Canの疑問文",
            "answer": "2"
        },
        {
            "title": "Mayの疑問文",
            "answer": "May"
        },
        {
            "title": "Mayの意味",
            "answer": "可能性、許可"
        }
    ]
}'''

SCHEMA_RESULTS = '''{
  "type": "object",
  "required": ["results"],
  "additionalProperties": false,
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["title", "correct", "user_answer", "correct_answer"],
        "additionalProperties": false,
        "properties": {
          "title": {
            "type": "string",
            "minLength": 1,
            "maxLength": 10
          },
          "correct": {
            "type": "boolean"
          },
          "user_answer": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100
          },
	        "correct_answer": {
	            "type": "string",
	            "minLength": 1,
	            "maxLength": 100
	        },
	        "correct_num": {
	            "type": "number"
	        }
        }
      }
    }
  }
}'''

RESULTS_SAMPLE = '''{
  "results": [
    {
      "title": "動詞の使い方",
      "correct": true,
      "user_answer": "read",
      "correct_answer": "read",
      "discription": "動詞とは（参照：1ページ）"
    },
    {
      "title": "疑問文の作り方",
      "correct": false,
      "user_answer": "He is a teacher?",
      "correct_answer": "Is he a teacher?",
      "correct_num": 1,
      "discription": "疑問文とは（参照：5ページ）"
    },
    {
      "title": "名詞の複数形",
      "correct": true,
      "user_answer": "cats",
      "correct_answer": "cats",
      "discription": "名詞の複数形とは（参照：8ページ）"
    },
    {
      "title": "時間の表現",
      "correct": false,
      "user_answer": "one",
      "correct_answer": "three",
      "discription": "時間の表現とは（参照：15ページ）"
    }
  ]
}'''