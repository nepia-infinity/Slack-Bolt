import os, logging
from typing import Optional, List, Dict, Tuple
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()



def get_thread_messages(client: WebClient, channel_id: str, thread_ts: str) -> list | None:
    """
    指定されたチャンネルとスレッドタイムスタンプを使用して、
    スレッド内のメッセージを取得します。

    Args:
        client: 初期化済みの slack_sdk.WebClient インスタンス。
        channel_id: スレッドが存在するチャンネルのID。
        thread_ts: スレッドの親メッセージのタイムスタンプ。

    Returns:
        スレッド内のメッセージのリスト (成功した場合)。
        メッセージ取得に失敗した場合は None。
        各メッセージは辞書形式です。
        リストの最初の要素が親メッセージになります。
    """
    try:
        response = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
        )

        if response.get("ok"):
            messages = response.get("messages", [])
            channel_name = get_channel_name(client, channel_id)
            logger.info(f"チャンネル名:{channel_name} スレッドから{len(messages)} 件のメッセージを取得しました ")
            
            print(messages)
            return messages
        
        else:
            error_message = response.get("error", "Unknown error")
            logger.error(f"メッセージの取得に失敗しました。\n{error_message}")
            return None

    except SlackApiError as e:
        logger.error(f"{e.response['error']}", exc_info=True)
        return None
    
    except Exception as e:
        logger.error(f"{e}", exc_info=True)
        return None



def get_channel_name(client: WebClient, channel_id: str) -> str:
    """
    チャンネルIDからチャンネル名を取得します。
    取得できない場合はチャンネルIDをそのまま返します。
    """
    try:
        info_response = client.conversations_info(channel=channel_id)
        if info_response.get("ok") and info_response.get("channel"):
            return info_response["channel"].get("name", channel_id)
        
        else:
            logger.warning(f"Could not retrieve channel info for {channel_id}: {info_response.get('error')}")
            return channel_id
        
    except SlackApiError as e:
        logger.warning(f"Error fetching channel name for {channel_id}: {e.response['error']}")
        return channel_id
    
    except Exception as e:
        logger.warning(f"An unexpected error occurred fetching channel name for {channel_id}: {e}")
        return channel_id
    
    

def extract_question_and_answer(messages: Optional[List[Dict]]) -> Tuple[Optional[str], Optional[str]]:
    """
    Slackメッセージリストから質問と回答テキストを抽出（簡潔版）。
    回答は messages[1]["attachments"][0]["blocks"][1]["text"]["text"] から取得します。

    Args:
        messages: Slackメッセージの辞書のリスト。

    Returns:
        (質問テキスト, 回答テキスト) のタプル。見つからない場合は None。
    """
    user_query =messages[0].get("text") if messages else None
    gemini_answer = None

    try:
        if len(messages) > 1:
            attachments = messages[1].get("attachments")
            if isinstance(attachments, list) and len(attachments) > 0:
                gemini_answer = attachments[0]["blocks"][1]["text"]["text"]
    except (IndexError, KeyError, TypeError):
        pass  # 予期しない構造の場合はエラーを無視

    return user_query, gemini_answer



def main():
    channel_id = "C02B2S137FC"
    thread_ts = "1744364673.361239"
    client = WebClient(token=os.environ["SLACK_BOT_TOKEN_FOR_SOCKET_MODE"])
    get_thread_messages(client, channel_id, thread_ts)
    return



if __name__ == "__main__":
    main()
