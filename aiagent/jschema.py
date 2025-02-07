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

SCHEMA_QUESTION = '''{
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


QUESTION_SAMPLE = '''{
		"questions": [
				{
				    "title": "動詞の使い方",
				    "format": "Anaume",
				    "score": 25,
				    "question": "英語の文で「I _ a book.」と書く場合、空欄にはどの動詞を入れますか？",
				    "correct_answer": "read"
				},
				{
				    "title": "疑問文の作り方",
				    "format": "Sentaku",
				    "score": 25,
				    "question": "次の文を疑問文にするにはどの語順を使いますか？「He is a teacher.」",
				    "options": [
				        {"item_num": 1, "item_word": "Is he a teacher?"},
				        {"item_num": 2, "item_word": "He is a teacher?"},
				        {"item_num": 3, "item_word": "A teacher is he?"}
				    ],
				    "correct_answer": "Is he a teacher?",
				    "correct_num": 1
				},
				{
				    "title": "名詞の複数形",
				    "format": "Kijutsu",
				    "score": 25,
				    "question": "「cat」の複数形は何ですか？",
				    "correct_answer": "cats"
				},
				{
				    "title": "時間の表現",
				    "format": "Anaume",
				    "score": 25,
				    "question": "英語で「今は3時です」と言いたい場合、空欄には何が入りますか？「It is _ o'clock.」",
				    "correct_answer": "three"
				}
    ]
}'''

SCHEMA_ANSWER = '''{
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

SCHEMA_RESULT = '''{
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
    },
    "total_score": {
      "type": "number"
    },
    "max_score": {
      "type": "number"
    }
  }
}'''