from gemini import call_gemini
import logging, os, pytz, json, requests
from datetime import datetime
from time_utils import get_current_time
from greeting_utils import get_greeting
from build_block_kit import format_gemini_response
from update_user_action import show_feedback
from interaction_utils import extract_incorrect_response_feedback
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

    if user_query:
        reply_in_thread(say, event, greeting, current_time_str, user_query)
    
    else:
        say("何かご質問はありますか？")



@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)



# 役に立ったを押した時の反応
@app.action("feedback_useful")
def handle_feedback_useful(ack, body, logger):
    ack()  # アクションの受付をSlackに通知 「 acknowledge（承認する、確認する）」 の略語
    logger.info(f"フィードバック（役に立った）を受け取りました: {body}")
    
    is_useful = True
    show_feedback(client, body, is_useful)
        
       
        
# 情報が正しくないを押した時の反応
@app.action("feedback_incorrect")
def handle_feedback_incorrect(ack, body, logger):
    ack() # アクションの受付をSlackに通知 「 acknowledge（承認する、確認する）」 の略語
    
    is_useful = False
    show_feedback(client, body, is_useful)

    
    
# ラジオボタンを押した時の反応
@app.action("radio_buttons_feedback_reason")
def handle_some_action(ack, body, logger):
    ack()
    logger.info(body)
    


# FeedBackを送信するを押した時の反応
@app.action("submit_user_feedback")
def handle_feedback_submission(ack, body, logger, client):
    ack()
    
    # 選択肢、入力内容を含んだ辞書を取得
    interaction_context = extract_incorrect_response_feedback(body, logger)
    
    
   
if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN_FOR_SOCKET_MODE"])
    handler.start()
