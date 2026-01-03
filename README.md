# EDINET AI Analyst (v2 API)

証券コードを入力するだけで、日本の公的開示システム「EDINET」から最新の決算資料を自動取得し、Google Gemini (LLM) がプロの証券アナリストの視点で要約・分析を行うアプリケーションです。

## 💡 アプリの使いかた（PC・スマホ共通）

デプロイ済みのURLにアクセスするだけで利用可能です。

### 1. 準備：APIキーの入力
アプリを開いたら、まず設定メニュー（サイドバー）にAPIキーを入力してください。
- **PCの場合**: 画面左側に設定メニューが表示されています。
- **スマホの場合**: 画面左上の **「＞」マーク** をタップすると設定メニューが開きます。

以下の2つのキーを貼り付けてください：
1. **Gemini API Key**: AI分析に使用
2. **EDINET API Key**: 書類取得に使用

### 2. 分析の実行
1. **証券コード**: 分析したい企業の4桁のコード（例: `7203` トヨタ、`9110` NSユナイテッド海運など）を入力。
2. **検索期間**: 遡る期間を選択（通常は90日でOK）。
3. **分析開始**: ボタンを押して数十秒待つと、AIレポートが生成されます。

---

## 🔑 必要なAPIキーの取得方法（初回のみ）

どちらも無料で数分で取得可能です。

### 1. Google Gemini API Key
[Google AI Studio](https://aistudio.google.com/) にアクセスし、**"Get API key"** から発行してください。

### 2. EDINET API Key (サブスクリプションキー)
[EDINET API 認証管理システム](https://api.edinet-fsa.go.jp/api/v2/auth/login) にてアカウント作成後、マイページからコピーしてください。

---

## ⚠️ 注意事項・免責事項
- **投資判断について**: 本アプリのレポートはAIによる自動生成であり、正確性を保証しません。必ず一次情報（有価証券報告書等）を確認し、自己責任で投資判断を行ってください。
- **データ利用**: Gemini API の無料枠を使用する場合、入力データがモデル改善に利用される可能性があります。
- **レート制限**: 短時間に連続で実行すると、APIの制限により一時的にエラーになる場合があります。

---

## 🛠 開発者向け情報（オプション）

ローカル環境での実行や、独自のデプロイを行いたい場合は以下を参照してください。

<details>
<summary><b>ローカルでのセットアップ手順</b></summary>

### 環境構築 (Python 3.12 推奨)
```bash
git clone <your-repo-url>
cd edinet-ai-analyst
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 起動
```bash
streamlit run app.py
```
</details>

<details>
<summary><b>デプロイ手順 (Streamlit Cloud)</b></summary>

1. GitHubにプッシュ。
2. [Streamlit Cloud](https://share.streamlit.io/) でリポジトリを連携。
3. `Main file path` に `app.py` を指定。
4. Python 3.12 を選択してデプロイ。
</details>

---
Powered by [EDINET API](https://api.edinet-fsa.go.jp/) & [Google Gemini](https://ai.google.dev/)
