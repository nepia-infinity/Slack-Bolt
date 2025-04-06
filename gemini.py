from google import genai
from dotenv import load_dotenv
load_dotenv()
import os



def call_gemini(user_query: str = None):
    
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    prompt = "Slackアプリを通してユーザーからの質問を受け付けています。\n"
    prompt += "### 制約条件 ###\n"
    prompt += "- ユーザーからの質問に対して400文字以内で回答すること\n"
    prompt += "- 参照するURLを含む場合は <https******|サイト名> のように出力してください。\n"
    prompt += "- Slackアプリで使用する文章のため、URLは[サイト名](https******) では文字列になってしまいます。\n"
    prompt += "- そのため、URLは上記のフォーマットで出力しないでください。\n"
    prompt += "- URLは必ず1行ずつ出力してください。\n"
    prompt += "- 単語を強調する場合は必ず前後に半角スペースを入れ、単語をアスタリスク(*)で囲むこと。\n"
    prompt += "- （例）*Google*  *Gemini* \n"
    prompt += "- 社内用語や業界用語などが含まれる場合は必ず注釈を付けること。\n"
    prompt += "- 400字では到底説明が難しい場合は、詳細はこちらをご覧くださいと記載した上で、URLを転記してください。\n"
    prompt += f"質問: {user_query}\n"
    
    response = client.models.generate_content(model="gemini-2.0-flash",contents=[prompt])
    
    print("Gemini APIで生成中...\n")
    
    generated_text = response.candidates[0].content.parts[0].text
    modified_text = generated_text.replace("[", "<").replace("]", ">")
    print(f"{modified_text}\n\n")
    
    return modified_text



def main():
    user_query = "日本の首都はどこですか？"
    call_gemini(user_query)



if __name__ == "__main__":
    main()