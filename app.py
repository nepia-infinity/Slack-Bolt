from gemini import call_gemini
import logging, os, pytz, json
from typing import Dict, Optional
from datetime import datetime, time
import requests
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logging.basicConfig(level=logging.DEBUG)
app = App(token=os.environ.get("SLACK_BOT_TOKEN_FOR_SOCKET_MODE"))


def get_current_time(now):
    """現在時刻をyyyy/mm/dd（E）HH:mmの形式で返す関数（日本時間）"""
    weekday_str = ["月", "火", "水", "木", "金", "土", "日"][now.weekday()]
    return now.strftime(f"%Y/%m/%d（{weekday_str}）%H:%M")



def get_greeting(now):
    """時刻に基づいて挨拶を返す関数 (datetime オブジェクトを受け取る)"""
    current_time = now.time()
    morning_start = time(5, 0)
    morning_end = time(9, 0)
    daytime_start = time(9, 1)
    daytime_end = time(17, 0)

    if morning_start <= current_time <= morning_end:
        return "おはようございます。"
    
    elif daytime_start <= current_time <= daytime_end:
        return "お疲れ様です。"
    
    else:
        return "夜遅くまでお疲れ様です。"
    
    
    
def reply_in_thread(say, event, greeting, current_time_str, user_query):
    thread_ts = event.get("thread_ts") or event["ts"]
    text = f"<@{event['user']}> さん！{greeting}\n"  # event からユーザー情報を取得
    text += f"*受付日時: {current_time_str} * \n\n\n"
    text += call_gemini(user_query)
    say(
        format_gemini_response(text),
        thread_ts=thread_ts
    )



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



def recieve_user_feedback(state_values, logger):
    value, selected_item = get_selected_item(state_values, logger)
    user_input = get_user_input_data(state_values, logger)
    
    print(f"value: {value}, option: {selected_item}\n")
    print(f"ユーザーが入力した内容：\n{user_input}\n")
    
    return selected_item, user_input



def get_selected_item(state_values: Dict, logger: logging.Logger) -> tuple[Optional[str], Optional[str]]:
    """
    state_values から選択されたラジオボタンの value と text を取得します。

    Args:
        state_values: body['state']['values'] の辞書。
        logger: ロギング用のロガーインスタンス。

    Returns:
        (value, text) のタプル。見つからない場合やエラー時は (None, None)。
    """
    
    reason_value: Optional[str] = None
    reason_text: Optional[str] = None

    try:
        reason_state = state_values.get("feedback_reason_block", {}).get("radio_buttons_feedback_reason", {})
        selected_option = reason_state.get('selected_option')

        if selected_option and isinstance(selected_option, dict):
            reason_value = selected_option.get('value')
            option_text_obj = selected_option.get('text')
            
            if isinstance(option_text_obj, dict):
                reason_text = option_text_obj.get('text')
            
    except Exception as e:
        logger.error("blockから値を上手く取り出せませんでした")
        
    return reason_value, reason_text



def get_user_input_data(state_values: Dict, logger: logging.Logger) -> str:
    """
    state_values からテキスト入力の値を取得します。

    Args:
        state_values: body['state']['values'] の辞書。
        logger: ロギング用のロガーインスタンス。

    Returns:
        入力されたテキスト。入力がない場合やエラー時は空文字列 ""。
    """
    
    expected_text: str = ""
    
    try:
        # 固定IDを使って state_values からアクセス
        response_state = state_values.get("expected_response_block", {}).get("text_input_expected_response", {})
        expected_text_value = response_state.get('value')
        
        # None の場合は空文字列 "" にする
        expected_text = expected_text_value if expected_text_value is not None else ""
        
    except Exception as e:
        logger.error("blockから値を上手く取り出せませんでした")

    return expected_text



# 特定のキーワードを含むメッセージに反応するイベント
@app.message("教えてGemini")
def handle_keyword_message(message, say, event):
    now = datetime.now(pytz.timezone("Asia/Tokyo"))
    current_time_str = get_current_time(now)
    greeting = get_greeting(now)
    
    # Geminiに送るためのテキストを成形する
    user_query = message["text"].replace("教えてGemini", "")
    
    # 問い合わせに対して返信する
    reply_in_thread(say, event, greeting, current_time_str, user_query)



# アプリへのメンションに反応するイベント
@app.event("app_mention")
def handle_app_mention(event, say):
    now = datetime.now(pytz.timezone("Asia/Tokyo"))
    current_time_str = get_current_time(now)
    greeting = get_greeting(now)

    # ボット自身のメンション部分を取り除き、ユーザーが実際にボットに尋ねた内容（質問）だけを抽出する処理
    bot_user_id = "<@U016LGTKQCF>"
    user_query = event["text"].replace(bot_user_id, "")

    # 「教えてGemini」キーワードが含まれていない場合のみ処理する
    if "教えてGemini" not in event["text"]:
        if user_query:
            reply_in_thread(say, event, greeting, current_time_str, user_query)
        
        else:
            say("何かご質問はありますか？")



@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)



@app.action("feedback_useful")
def handle_feedback_useful(ack, body, logger):
    ack()  # アクションの受付をSlackに通知 「 acknowledge（承認する、確認する）」 の略語
    logger.info(f"フィードバック（役に立った）を受け取りました: {body}")
    
    

@app.action("feedback_incorrect")
def handle_feedback_incorrect(ack, body, logger):
    ack() # アクションの受付をSlackに通知 「 acknowledge（承認する、確認する）」 の略語
    response_url = body["response_url"]

    requests.post(response_url, json= build_feedback_block_kit())
    logger.info("フィードバックを送信しました。")
    
    

@app.action("radio_buttons_feedback_reason")
def handle_some_action(ack, body, logger):
    ack()
    logger.info(body)
    


@app.action("submit_user_feedback")
def handle_feedback_submission(ack, body, logger, client):
    ack()
        
    # state オブジェクトから入力値を取得
    state_values = body['state']['values']
    logger.info(f"{json.dumps(state_values, indent=4)}\n")
    
    # 選択肢、入力内容を取得
    option, user_input = recieve_user_feedback(state_values, logger)
    
    # 保存したい内容を辞書型で取得
    interaction_context = {
        "user_id": body["user"]["id"],
        "channel_id": body["container"]["channel_id"],
        "thread_ts": body["container"].get("thread_ts"),
        "selected_item": option,
        "user_input": user_input
    }
    
    print(f"{json.dumps(interaction_context, indent=4, ensure_ascii=False)}\n")
    
    


   
if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN_FOR_SOCKET_MODE"])
    handler.start()
