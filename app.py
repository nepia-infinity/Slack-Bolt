from gemini import call_gemini
import logging, os, pytz
from datetime import datetime, time
from slack_sdk import WebClient
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler



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
        generate_block_kit(text),
        thread_ts=thread_ts
    )


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



def generate_block_kit(text):
    block_kit = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": ":gemini-ai: Geminiによる回答結果",
                    "emoji": True
                }
            }
        ],
        "attachments": [
            {
                "color": "4285f4",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": text
                        }
                    }
                ]
            }
        ]
    }
    return block_kit
    
    
    
if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN_FOR_SOCKET_MODE"])
    handler.start()
