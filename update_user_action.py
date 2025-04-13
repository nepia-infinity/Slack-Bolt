import logging, json, requests
from get_slack_messages import get_thread_messages, extract_question_and_answer
from build_block_kit import build_feedback_block_kit

logger = logging.getLogger(__name__)



def modified_feedback_blocks(body):
    original_attachments = body.get("message", {}).get("attachments", [])
    user_id = body.get("user", {}).get("id")
    
    """元のメッセージを加工し、肯定的なフィードバックを表示するブロックを生成"""
    if not original_attachments or not isinstance(original_attachments, list):
        logger.warning("Attachments が見つからないか、形式が不正です。")
        return None
    
    original_blocks = original_attachments[0].get("blocks", [])
    if not original_blocks:
        logger.warning("最初の attachment に blocks が見つかりません。")
        return None

    # アクションボタンを削除し、フィードバック確認用のコンテキストブロックを追加
    filtered_blocks = [block for block in original_blocks if block.get("type") != "actions"]
    filtered_blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn", 
                "text": f":white_check_mark: <@{user_id}> さんが「役に立った」と評価しました。"
            }
        ]
    })
    
    print(f"{json.dumps(filtered_blocks, indent=4, ensure_ascii=False)}\n")
    return filtered_blocks



def get_interaction_context(body: dict, user_query: str, answer: str) -> dict:
    """ユーザーのインタラクション情報を取得し、辞書形式で返す"""
    user_id = body.get("user", {}).get("id")
    thread_ts = body["container"].get("thread_ts")
    channel_id = body["container"].get("channel_id")

    interaction_context = {
        "thread_ts": thread_ts,
        "channel_id": channel_id,
        "user_id": user_id,
        "user_query": user_query,
        "answer": answer
    }

    print(f"{json.dumps(interaction_context, indent=4, ensure_ascii=False)}\n")
    return interaction_context



def show_feedback(client, body, is_useful):
    """フィードバック内容をSlackメッセージに反映"""
    
    # スレッド内容を取得
    messages = get_thread_messages(client, body)
    user_query, answer = extract_question_and_answer(messages)
    interaction_context = get_interaction_context(body, user_query, answer)
    
    # 内容を保存する
            
    response_url = body.get("response_url")
    
    if not response_url:
        logger.error("response_url が不足しています。")
        return

    try:
        if is_useful:
            
            # 役に立った場合、辞書に値を追加
            interaction_context["is_useful"] = True
            interaction_context["reason"] = '-'
            
            # 辞書型をExcelに保存する
            
            # :white_check_mark: 〇〇 さんが「役に立った」と評価しました。とメッセージの一部を改変する
            original_attachments = body.get("message", {}).get("attachments", [])
            update_payload = {
                "replace_original": True,
                "attachments": [{
                    "id": original_attachments[0].get("id", 1),
                    "color": original_attachments[0].get("color"),
                    "blocks": modified_feedback_blocks(body)
                }]
            }
            
            requests.post(response_url, json=update_payload).raise_for_status()
            logger.info(f"フィードバックが <@{body.get('user', {}).get('id')}> により送信されました。")
            
        else:
            # どこが間違っているかをユーザーに選んでもらうフォームを送信する
            requests.post(response_url, json=build_feedback_block_kit()).raise_for_status()
        
    except Exception as e:
        logger.error(f"メッセージ更新中にエラー発生: {e}", exc_info=True)
        requests.post(response_url, json={"replace_original": False, "text": "エラーが発生しました。"})
        


def acknowledge_feedback_submission(body, client, logger):
    
    # アクションボタンを削除し、フィードバック確認用のコンテキストブロックを追加
    original_blocks = body.get("message", {}).get("blocks", [])
    filtered_blocks = [block for block in original_blocks if block.get("type") != "actions"]
    
    # フィルタリングされたブロックに確認メッセージを追加
    filtered_blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": ":white_check_mark: FeedBackを送信しました！！"
            }
        ]
    })
    
    print(filtered_blocks)

    try:
        client.chat_update(
            channel=body["channel"]["id"],
            ts=body["message"]["ts"], 
            blocks=filtered_blocks,
            text="FeedBackを送信しました。"
        )
        
        logger.info("FeedBackが送信されました！！")

    except Exception as e:
        logger.error(f"メッセージの更新エラー: {e}")