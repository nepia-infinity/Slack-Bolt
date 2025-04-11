import logging, os, pytz, json, requests
from typing import Dict, Optional


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



def recieve_user_feedback(state_values, logger):
    value, selected_item = get_selected_item(state_values, logger)
    user_input = get_user_input_data(state_values, logger)
    
    print(f"value: {value}, option: {selected_item}\n")
    print(f"ユーザーが入力した内容：\n{user_input}\n")
    
    return selected_item, user_input