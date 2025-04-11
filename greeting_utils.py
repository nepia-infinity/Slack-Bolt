from datetime import datetime, time



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