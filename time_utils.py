from datetime import datetime


def get_current_time(now):
    """現在時刻をyyyy/mm/dd（E）HH:mmの形式で返す関数（日本時間）"""
    weekday_str = ["月", "火", "水", "木", "金", "土", "日"][now.weekday()]
    return now.strftime(f"%Y/%m/%d（{weekday_str}）%H:%M")