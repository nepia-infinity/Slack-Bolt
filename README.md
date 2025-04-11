![image](https://github.com/user-attachments/assets/1034b932-e2da-41a6-a959-9c711145a10a)
![image](https://github.com/user-attachments/assets/0075a8e1-6c63-4938-91db-9d2da2de1336)


概要
このSlackアプリケーションは、メンションないし、教えてGeminiというキーワードに応答し、
GoogleのGemini APIを活用して質問に対する回答を生成します。
Socket Modeを使用しているため、外部公開されたサーバーを必要とせず、ローカル環境下でも利用可能です。

主な機能
- メンション応答:
- 特定のキーワードによる応答
- スレッドへの返信

動作環境
- Python 3.8以上
- Slackワークスペースへのアクセス権 (アプリのインストール権限)
- Google Cloud プロジェクトおよび Gemini API の有効化
- 必要なPythonライブラリ (slack_bolt, google-generativeai, python-dotenv)

Activate
```
# カレントディレクトリを移動
cd "C:\Users\nepia\OneDrive\デスクトップ\Slack_Bolt"

# 実行ポリシーを現在のプロセスに対して Bypass に設定
# (すべてのスクリプトを実行可能にする - 注意が必要)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 仮想環境のアクティベートスクリプトを実行
.venv\Scripts\Activate.ps1

```

