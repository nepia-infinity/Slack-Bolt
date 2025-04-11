from gemini import call_gemini
import logging, os, pytz, json, requests
from typing import Dict, Optional
from datetime import datetime
from time_utils import get_current_time
from greeting_utils import get_greeting
from build_block_kit import format_gemini_response, build_feedback_block_kit
from interaction_utils import recieve_user_feedback
from get_slack_messages import get_thread_messages, extract_question_and_answer
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

logging.basicConfig(level=logging.DEBUG)
app = App(token=os.environ.get("SLACK_BOT_TOKEN_FOR_SOCKET_MODE"))

load_dotenv()
client = WebClient(token=os.environ["SLACK_BOT_TOKEN_FOR_SOCKET_MODE"])
    
    
    
def reply_in_thread(say, event, greeting, current_time_str, user_query):
    thread_ts = event.get("thread_ts") or event["ts"]
    text = f"<@{event['user']}> さん！{greeting}\n"  # event からユーザー情報を取得
    text += f"*受付日時: {current_time_str} * \n\n\n"
    text += call_gemini(user_query)
    say(
        format_gemini_response(text),
        thread_ts=thread_ts
    )



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
    
    channel_id = body["container"]["channel_id"]
    thread_ts = body["container"].get("thread_ts")
    messages = get_thread_messages(client, channel_id, thread_ts)
    user_query, answer = extract_question_and_answer(messages)
    
    interaction_context = {
        "thread_ts": thread_ts,
        "channel_id": channel_id,
        "user_id": body["user"]["id"],
        "user_query": user_query,
        "answer": answer
    }
    
    print(f"{json.dumps(interaction_context, indent=4)}\n")
         
    # Geminiからの応答を置き換える
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
        "thread_ts": body["container"].get("thread_ts"),
        "channel_id": body["container"]["channel_id"],
        "user_id": body["user"]["id"],
        "selected_item": option,
        "user_input": user_input
    }
    
    print(f"{json.dumps(interaction_context, indent=4, ensure_ascii=False)}\n")
    
    


   
if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN_FOR_SOCKET_MODE"])
    handler.start()
