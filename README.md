# EDINET AI Analyst (v2 API)

証券コードを入力するだけで、日本の公的開示システム「EDINET」から最新の決算資料を自動取得し、Google Gemini (LLM) がプロの証券アナリストの視点で要約・分析を行うStreamlitアプリケーションです。

## 🚀 主な機能

- **書類自動検索**: 証券コード（4桁）から、最新の有価証券報告書、四半期報告書、または半期報告書を自動特定。
- **PDF自動取得**: EDINET API v2 を使用して、公式の開示PDFを直接ダウンロード。
- **AI分析レポート**: Gemini 2.0 / 3.0 (Flash/Pro) を使用し、以下の項目を構造化レポートとして出力。
    - エグゼクティブ・サマリー
    - 業績ハイライト
    - リスク分析
    - 将来見通し
    - キラリと光る点（強み・特徴）
- **デバッグ機能**: APIの疎通確認やキャッシュクリア機能を搭載。

## 🔑 必要なAPIキーの取得方法

このアプリの利用には、以下の2種類のAPIキーが必要です。どちらも無料で取得可能です。

### 1. Google Gemini API Key
AIによる分析に使用します。
1. [Google AI Studio](https://aistudio.google.com/) にアクセスし、Googleアカウントでログイン。
2. 左メニューの **"Get API key"** をクリック。
3. **"Create API key"** をクリックしてキーを発行・コピーします。

### 2. EDINET API Key (サブスクリプションキー)
開示書類の検索・取得に使用します。
1. [EDINET API 認証管理システム](https://api.edinet-fsa.go.jp/api/v2/auth/login) にアクセス。
2. **「新規登録」** からアカウントを作成します。
3. ログイン後、マイページに表示される **「サブスクリプションキー」** をコピーします。

## 🛠 セットアップ (ローカル実行)

### 1. 環境構築 (Python 3.12 推奨)
```bash
git clone <your-repo-url>
cd edinet-ai-analyst

# 仮想環境の作成
python3.12 -m venv venv
source venv/bin/activate

# 依存ライブラリのインストール
pip install -r requirements.txt
```

### 2. アプリの起動
```bash
streamlit run app.py
```

## 🌐 デプロイ (Streamlit Community Cloud)

1. GitHubにリポジトリをプッシュします。
2. [Streamlit Cloud](https://share.streamlit.io/) にログインし、"New app" からリポジトリを連携します。
3. `Main file path` に `app.py` を指定してデプロイします。

## ⚠️ 注意事項・免責事項

- **投資判断について**: 本アプリが生成するレポートはAIによる自動生成であり、正確性を保証するものではありません。実際の投資判断は、必ず一次情報（有価証券報告書等）を確認の上、自己責任で行ってください。
- **データ利用**: Gemini API の無料枠（Free Tier）を使用する場合、入力したデータがモデルの改善に利用される可能性があります。機密情報の取り扱いにはご注意ください。
- **レート制限**: 各APIには1分間あたりのリクエスト数制限があります。エラーが発生した場合は、少し時間を置いてから再試行してください。

---
Powered by [EDINET API](https://api.edinet-fsa.go.jp/) & [Google Gemini](https://ai.google.dev/)
