from gemini import call_gemini
import logging, os, pytz, json
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
                "text": {
                    "type": "mrkdwn",
                    "text": "*Q1. 次のうちどれに当てはまりますか？*"
                },
                "accessory": {
                    "type": "radio_buttons",
                    "options": [
                        {"text": {"type": "plain_text", "text": "情報が古い・更新されていない", "emoji": True}, "value": "value-0"},
                        {"text": {"type": "plain_text", "text": "法令や就業規則などに則していない回答だった", "emoji": True}, "value": "value-1"},
                        {"text": {"type": "plain_text", "text": "共有されたリンクにアクセスできなかった", "emoji": True}, "value": "value-2"},
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



# 特定のキーワードを含むメッセージに反応するイベント
@app.message("教えてGemini")
def handle_keyword_message(message, say, event):
    now = datetime.now(pytz.timezone('Asia/Tokyo'))
    current_time_str = get_current_time(now)
    greeting = get_greeting(now)
    
    # 問い合わせに対して返信する
    reply_in_thread(say, event, greeting, current_time_str, message['text'])



# アプリへのメンションに反応するイベント
@app.event("app_mention")
def handle_app_mention(event, say):
    now = datetime.now(pytz.timezone('Asia/Tokyo'))
    current_time_str = get_current_time(now)
    greeting = get_greeting(now)

    # ボット自身のメンション部分を取り除き、ユーザーが実際にボットに尋ねた内容（質問）だけを抽出する処理
    bot_user_id = "<@U016LGTKQCF>"
    user_query = event["text"].replace(bot_user_id, "")

    # 「教えてGemini」キーワードが含まれていない場合のみ処理する
    if "教えてGemini" not in event["text"]:
        if user_query:
            reply_in_thread(say, event, greeting, current_time_str, user_query)  # event を渡す
        
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
    ack()  # アクションを受け付けたことをSlackに通知
    response_url = body["response_url"]  # response_urlを取得

    # フィードバックフォームを送信
    requests.post(response_url, json= build_feedback_block_kit())
    logger.info("フィードバックフォームを送信しました。")
    
    

@app.action("radio_buttons_feedback_reason")
def handle_some_action(ack, body, logger):
    ack()
    logger.info(body)
    


@app.action("submit_user_feedback")
def handle_feedback_submission(ack, body, logger, client):
    ack()

    # 基本情報の取得
    user_id = body['user']['id']
    channel_id = body['container']['channel_id']
    message_ts = body['container']['message_ts']
    thread_ts = body['container'].get('thread_ts', message_ts) # スレッド対応

    # state オブジェクトから入力値を取得
    state_values = body['state']['values']
    logger.info(f"Received state: {json.dumps(state_values, indent=4)}")

    # ラジオボタンの選択値を取得
    reason_block_id = "feedback_reason_block"
    reason_action_id = "radio_buttons_feedback_reason"
    selected_reason_value = None
    selected_reason_text = None
    try:
        # selected_option が None でないことを確認してからアクセス
        selected_option = state_values[reason_block_id][reason_action_id].get('selected_option')
        if selected_option:
            selected_reason_value = selected_option['value']
            selected_reason_text = selected_option['text']['text']
            
        else:
            logger.warning("Radio button was not selected.")
            
    except KeyError as e:
        logger.error(f"Error accessing radio button state (Block ID: {reason_block_id}, Action ID: {reason_action_id}): {e}")

    # テキスト入力の値を取得
    expected_response_block_id = "expected_response_block"
    expected_response_action_id = "text_input_expected_response"
    expected_response_text = None
    
    try:
        expected_response_text = state_values[expected_response_block_id][expected_response_action_id]['value']
        # 入力が空の場合、None や空文字列になることがある
        if expected_response_text is None:
             expected_response_text = ""
             
    except KeyError as e:
        logger.error(f"Error accessing text input state (Block ID: {expected_response_block_id}, Action ID: {expected_response_action_id}): {e}")

    # 取得した値を使って処理
    logger.info(f"Feedback submitted by <@{user_id}> in <#{channel_id}> (message: {message_ts})")
    logger.info(f"  Q1 (Reason): {selected_reason_value} ('{selected_reason_text}')")
    logger.info(f"  Q2 (Expected): {expected_response_text}")

    # (例) 取得したデータをデータベースに保存する
    # db.save_feedback(
    #     user_id=user_id,
    #     channel_id=channel_id,
    #     message_ts=message_ts,
    #     reason=selected_reason_value,
    #     expected_text=expected_response_text
    # )

    # (例) ユーザーに完了メッセージを送信
    try:
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            thread_ts=thread_ts,
            text=f"フィードバックを受け付けました。\n選択された理由: {selected_reason_text}\n期待した回答: {expected_response_text}\nご協力ありがとうございます！"
        )
    except SlackApiError as e:
        logger.error(f"Error posting ephemeral confirmation: {e}")


   
if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN_FOR_SOCKET_MODE"])
    handler.start()
