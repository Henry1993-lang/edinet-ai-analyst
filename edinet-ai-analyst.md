
# Project: EDINET Disclosure Assistant (Streamlit App)

## 1. 概要
日本の公的開示システム「EDINET API」を使用して、指定された銘柄（証券コード）の直近の決算資料（有価証券報告書または決算短信）を自動取得し、Google Gemini APIを用いてその内容を分析・要約するStreamlitアプリケーションを構築する。

## 2. 制約条件・技術スタック
* **Frontend:** Streamlit
* **Language:** Python 3.10+
* **LLM:** Google Gemini API
    * **Model:** `gemini-1.5-flash` (または利用可能な最新のFlashモデル)
    * **Reason:** 無料枠での利用と、Long Context（長文一括処理）によるAPIコール節約のため。
* **Data Source:** EDINET API v2
* **Key Constraints:**
    * **One-Shot Analysis:** API利用制限（Rate Limit）を回避するため、チャット形式ではなく、PDF全体を1回のリクエストで送信し、必要な分析項目（要約、リスク、予測など）を一度にJSON形式等で出力させる設計とすること。
    * **No Vector DB:** RAG（Vector Search）は構築せず、GeminiのLong Contextウィンドウ（1M+ tokens）を活かしてPDFをそのままプロンプトに含める。

## 3. 機能要件

### A. 銘柄コード処理
* ユーザーは「7203」のような4桁の証券コードを入力する。
* アプリは起動時に（またはキャッシュから）EDINETの「EDINETコードリスト」を読み込み、証券コードをEDINETコード（例: E02144）に変換する。

### B. 資料取得 (EDINET API)
1.  **書類一覧取得:** 指定されたEDINETコードに基づき、直近の提出書類リストを取得する（`/list` エンドポイント）。
2.  **フィルタリング:**
    * `docDescription` や `formCode` を使用して、「有価証券報告書」または「決算短信」のいずれか最新のものを特定する。
    * 優先順位: 最新の有報 > 最新の四半期報 > 最新の決算短信
3.  **PDFダウンロード:** 該当書類のPDFを取得する（`/document` エンドポイント, type=2）。
    * *Note:* EDINET APIはzipを返す場合があるため、適切に解凍してPDFを取り出す処理を含めること。

### C. AI分析 (Gemini API)
* 取得したPDFバイナリを `google-generativeai` ライブラリを使用してアップロード・処理する。
* 以下のプロンプトを用いて分析を実行する（System Promptとして定義）。
    * **Role:** プロの証券アナリスト
    * **Output:** 以下のセクションを含む構造化されたレポート
        1.  **エグゼクティブ・サマリー:** 3行で簡潔に（ポジティブ/ネガティブ要素を含む）。
        2.  **業績ハイライト:** 売上・利益の増減とその主な要因。
        3.  **リスク分析:** 経営陣が認識している主要なリスクや懸念事項。
        4.  **将来見通し:** 次期の数値目標や定性的な見通し。
        5.  **キラリと光る点:** 技術力、シェア、新規事業など、特筆すべき強み。

### D. UI (Streamlit)
* **サイドバー:**
    * Gemini API Key 入力欄（セキュリティのため、コードに直書きせずUIから入力させる）。
    * 銘柄コード入力欄。
    * 「分析開始」ボタン。
* **メインエリア:**
    * 分析中はスピナー等で進捗を表示。
    * 結果はMarkdownで見やすく整形して表示。
    * 取得した元PDFへのリンク（EDINETの公開URL）があれば表示。

## 4. ファイル構成案
実装時の参考ファイル構成：

```text
project_root/
├── app.py                # Streamlitメインロジック
├── edinet_client.py      # EDINET APIとの通信、コード変換、PDF取得・抽出ロジック
├── ai_analyzer.py        # Gemini APIとの通信、プロンプト定義
├── requirements.txt      # 依存ライブラリ (streamlit, google-generativeai, requests, pandas, pypdf, etc.)
└── .gitignore

###5. 実装への指示
* エラーハンドリングを重視すること（該当する書類が見つからない場合、APIキーが無効な場合など）。
* EDINETコードリストは容量が大きいため、初回のみダウンロードし、ローカルにキャッシュする（csvまたはpickle）仕組みを入れると望ましい。
* コードは可読性を高く保ち、各関数にドキュメンテーション文字列を付与すること。

***


