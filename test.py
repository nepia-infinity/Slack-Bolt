import pandas as pd
import os


def main():
    data = {
        "thread_ts": "1744506064.018759",
        "channel_id": "C02B2S137FC",
        "user_id": "UQEHCN01E",
        "user_query": "教えてGemini　無色転生について教えて",
        "gemini_response": "<@UQEHCN01E> さん！お疲れ様です。\n*受付日時: 2025/04/13（日）10:01 * \n\n\n無職転生 ですね。\n\n*無職転生* は 、 理不尽な死を遂げた主人公が 、 剣と魔法の異世界で生まれ変わり  、 成長していく物語です 。 人生を後悔している主人公が 、 前世の記憶と経験を活かし 、 新たな世界で様々な困難に立ち向かい 、 生き抜く姿が描かれています 。\n\n詳細はこちらをご覧ください 。\n\n<https://mushokutensei.jp/>\n"
    }

    # 保存先を指定して保存できるが、同名のファイルがあると上書きされる
    output_directory = r"C:\Users\nepia\OneDrive\デスクトップ\Slack_Bolt\excel"
    excel_file_name = "feedback_data.xlsx"
    excel_file_path = os.path.join(output_directory, excel_file_name)

    df = pd.DataFrame([data])
    df.to_excel(excel_file_path, index=False)

    print(f"データが {excel_file_path} に保存されました。")
    
    
    
if __name__ == "__main__":
    main()