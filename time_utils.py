from datetime import datetime
import pytz


def get_current_time(now):
    """現在時刻をyyyy/mm/dd（E）HH:mmの形式で返す関数（日本時間）"""
    weekday_str = ["月", "火", "水", "木", "金", "土", "日"][now.weekday()]
    return now.strftime(f"%Y/%m/%d（{weekday_str}）%H:%M")



def convert_thread_ts_to_unix(thread_ts):
    """Slackのスレッドタイムスタンプ (thread_ts) を日本時間の YYYY/MM/DD HH:MM:SS 形式の文字列に変換します。

    Args:
        thread_ts (str): Slackのスレッドタイムスタンプ (例: "1681234567.890123").

    Returns:
        str: 日本時間の YYYY/MM/DD HH:MM:SS 形式の文字列。
             変換に失敗した場合は None を返します。
    """
    try:
        # 小数点で分割して秒とマイクロ秒を取得
        seconds_str, microseconds_str = thread_ts.split('.')
        seconds = int(seconds_str)

        # Unix タイムスタンプ（秒）を UTC の datetime オブジェクトに変換
        utc_datetime = datetime.fromtimestamp(seconds)

        # UTC から日本時間 (JST) に変換
        jst_timezone = pytz.timezone('Asia/Tokyo')
        jst_datetime = utc_datetime.astimezone(jst_timezone)

        # 日本時間の datetime オブジェクトを指定の形式にフォーマット
        formatted_jst = jst_datetime.strftime('%Y/%m/%d %H:%M:%S')

        print(f"日本時間（YYYY/MM/DD HH:MM:SS）：{formatted_jst}")
        return formatted_jst

    except ValueError:
        print(f"エラー: 無効な Slack スレッドタイムスタンプ形式です: {thread_ts}")
        return None


