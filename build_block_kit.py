def format_gemini_response(text):
    return {
        "text":"Geminiによる回答結果",
        "attachments": [
            {   
                "color": "4285f4",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": ":gemini-ai: Geminiによる回答結果",
                            "emoji": True
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": text
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "役に立った",
                                    "emoji": True
                                },
                                "style": "primary",
                                "action_id": "feedback_useful"
                            },
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "情報が正しくない",
                                    "emoji": True
                                },
                                "style": "danger",
                                "action_id": "feedback_incorrect"
                            }
                        ]
                    }
                ]
            }
        ]
    }



def build_feedback_block_kit():
    """ フィードバック用のBlock Kitのペイロードを生成 """
    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*`情報が正しくない`* が選択されたため回答が非表示になりました。\n社内FAQ自動応答の改善にご協力お願いします。\n"
                }
            },
            {
                "type": "section",
                "block_id": "feedback_reason_block",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Q1. 次のうちどれに当てはまりますか？*"
                },
                "accessory": {
                    "type": "radio_buttons",
                    "options": [
                        {"text": {"type": "plain_text", "text": "情報が古い・更新されていない", "emoji": True}, "value": "outdated_info"},
                        {"text": {"type": "plain_text", "text": "情報が事実に即していない、間違っている", "emoji": True}, "value": "incorrect_response"},
                        {"text": {"type": "plain_text", "text": "法令や就業規則などに則していない回答だった", "emoji": True}, "value": "non_compliant_response"},
                        {"text": {"type": "plain_text", "text": "共有されたリンクにアクセスできなかった", "emoji": True}, "value": "invalid_link"},
                    ],
                    "action_id": "radio_buttons_feedback_reason"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Q2. どういう回答結果を期待していましたか？*"
                }
            },
            {
                "type": "input",
                "block_id": "expected_response_block",
                "element": {
                    "type": "plain_text_input",
                    "multiline": True,
                    "action_id": "text_input_expected_response"
                },
                "label": {
                    "type": "plain_text",
                    "text": " ",
                    "emoji": True
                }
            },
            {
                "type": "actions",
                "block_id": "feedback_submit_actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "FeedBackを送信する",
                            "emoji": True
                        },
                        "style": "primary",
                        "value": "FeedBack送信ボタン",
                        "action_id": "submit_user_feedback"
                    }
                ]
            }
        ]
    }
