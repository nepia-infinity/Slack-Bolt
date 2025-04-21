import logging, json 
from typing import Dict, Optional
from time_utils import convert_thread_ts_to_unix




def get_user_input_data(body: Dict, logger: logging.Logger) -> str:
    """
    state_values からテキスト入力の値を取得します。

    Args:
        body: 辞書。
        logger: ロギング用のロガーインスタンス。

    Returns:
        入力されたテキスト。入力がない場合やエラー時は空文字列 ""。
    """
    
    state_values = body['state']['values']
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



def get_selected_item(body: Dict, logger: logging.Logger) -> tuple[Optional[str], Optional[str]]:
    """
    state_values から選択されたラジオボタンの value と text を取得します。

    Args:
        state_values: body['state']['values'] の辞書。
        logger: ロギング用のロガーインスタンス。

    Returns:
        (value, text) のタプル。見つからない場合やエラー時は (None, None)。
    """
    state_values = body['state']['values']
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



def recieve_user_feedback(body, logger):
    """
    ユーザーが選んだ選択肢と入力内容を取得する関数
    
    recieve_user_feedback
    ├── get_selected_item
    └── get_user_input_data
    
    """
    value, selected_item = get_selected_item(body, logger)
    user_input = get_user_input_data(body, logger)
    
    print(f"value: {value}, option: {selected_item}\n")
    print(f"ユーザーが入力した内容：\n{user_input}\n")
    
    return selected_item, user_input



def get_interaction_context(body: dict, user_query: str, answer: str) -> dict:
    """ユーザーのインタラクション情報を取得し、辞書形式で返す"""
    user_id = body.get("user", {}).get("id")
    thread_ts = body["container"].get("thread_ts")
    channel_id = body["container"].get("channel_id")    
    thread_ts_for_url = thread_ts.replace(".", "")

    interaction_context = {
        "thread_ts": thread_ts,
        "formatted_ts": convert_thread_ts_to_unix(thread_ts),
        "channel_id": channel_id,
        "thread_url": f"https://soralize.slack.com/archives/{channel_id}/p{thread_ts_for_url}",
        "user_id": user_id,
        "user_query": user_query,
        "gemini_response": answer,
        "is_useful": None,
        "selected_item": "-",
        "expected_response": "-"
    }

    print(f"{json.dumps(interaction_context, indent=4, ensure_ascii=False)}\n")
    return interaction_context



def extract_incorrect_response_feedback(body, logger):
    """
    ユーザーが「情報が正しくない」を選択した場合のフィードバックデータを抽出し、
    インタラクションコンテキストを作成する関数。

    Args:
        body (dict): Slackのアクションリクエストのbody。

    Returns:
        dict: インタラクションコンテキストを含む辞書。
    """
    
    option, user_input = recieve_user_feedback(body, logger)
    thread_ts = body["container"].get("thread_ts")
    
    # 保存したい内容を辞書型で取得
    interaction_context = {
        "thread_ts": thread_ts,
        "formatted_ts": convert_thread_ts_to_unix(thread_ts),
        "channel_id": body["container"]["channel_id"],
        "user_id": body["user"]["id"],
        "selected_item": option,
        "expected_response": user_input
    }
    
    print(f"{json.dumps(interaction_context, indent=4, ensure_ascii=False)}\n")
    return interaction_context