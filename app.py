import streamlit as st
import edinet_client
import ai_analyzer
import io
import sys
import pandas as pd

# Page Config
st.set_page_config(
    page_title="EDINET AI Analyst",
    page_icon="📈",
    layout="wide"
)

# Title and Intro
st.title("📈 EDINET AI Analyst (v2 API)")
st.markdown("""
日本の全上場企業の **有価証券報告書・四半期報告書・半期報告書** をEDINETから自動取得し、
**Google Gemini** が要約・分析します。
""")

# --- Sidebar ---
with st.sidebar:
    st.header("API設定")
    
    gemini_api_key = st.text_input("Gemini API Key", type="password", help="aistudio.google.com")
    edinet_api_key = st.text_input("EDINET API Key", type="password", help="api.edinet-fsa.go.jp (v2)")
    
    st.divider()
    st.header("分析設定")
    
    ticker_input = st.text_input("証券コード (4桁)", placeholder="例: 9110")
    
    lookback_days = st.selectbox(
        "検索期間 (過去)",
        options=[30, 90, 180, 365],
        index=1,
        help="指定した期間分、提出書類を遡って検索します。"
    )
    
    include_semiannual = st.checkbox("半期報告書も対象に含める", value=True, help="一部の企業（9110など）は四半期報告書の代わりに半期報告書を提出します。")
    
    model_option = st.selectbox(
        "Gemini モデル",
        (
            "gemini-3-flash-preview",
            "gemini-2.0-flash", 
            "gemini-1.5-flash",
            "Custom Input"
        ),
        index=0
    )
    
    if model_option == "Custom Input":
        model_name = st.text_input("モデル名", value="gemini-2.0-flash")
    else:
        model_name = model_option
        
    analyze_btn = st.button("分析開始", type="primary", disabled=not (gemini_api_key and edinet_api_key and ticker_input))

    st.divider()
    st.header("デバッグ & メンテナンス")
    
    if st.button("キャッシュをクリア"):
        st.cache_data.clear()
        st.success("キャッシュを削除しました。")
        
    if st.button("EDINET疎通テスト (2025-11-12)"):
        if not edinet_api_key:
            st.error("EDINET API Keyを入力してください")
        else:
            st.write("接続テスト実行中...")
            try:
                # Use a temp client for debug
                debug_client = edinet_client.EdinetClient(api_key=edinet_api_key)
                res = debug_client.debug_connection_test("2025-11-12")
                
                st.subheader("疎通テスト結果")
                st.write(f"Status Code: {res['status_code']}")
                st.write(f"URL: {res['url']}")
                
                if res['exception']:
                    st.error(f"Exception: {res['exception']}")
                
                with st.expander("Response Headers"):
                    st.json(res['headers'])
                
                with st.expander("JSON Metadata"):
                    st.json(res['json_metadata'])

                # Find 9110 in the raw data
                if res['json_data'] and isinstance(res['json_data'], dict):
                    results = res['json_data'].get('results', [])
                    st.write(f"Total Results: {len(results)}")
                    
                    hits = [d for d in results if d.get('secCode') and str(d.get('secCode')).startswith('9110')]
                    st.write(f"Hit count for '9110': {len(hits)}")
                    if hits:
                        st.json(hits)
                else:
                    st.error("JSON Data invalid or missing")
                    
            except Exception as e:
                st.error(f"Test failed: {e}")

# --- Main Logic ---

if analyze_btn:
    if not ticker_input.isdigit() or len(ticker_input) != 4:
        st.error("証券コードは4桁の数字で入力してください。")
    else:
        # Initialize Client with EDINET Key
        ed_client = edinet_client.EdinetClient(api_key=edinet_api_key)
        
        st.info(f"証券コード {ticker_input} の直近書類を検索中 ({lookback_days}日前まで)...")
        
        # Search directly by ticker in daily lists
        latest_doc, debug_logs = ed_client.search_latest_document(
            ticker_input, 
            lookback_days=lookback_days,
            include_semiannual=include_semiannual
        )
        
        if not latest_doc:
            st.error(f"過去 {lookback_days} 日以内に、指定された条件で書類が見つかりませんでした。")
            with st.expander("詳細デバッグ情報 (APIログ)"):
                st.write(f"- 検索対象証券コード: {ticker_input} (先頭一致)")
                st.write(f"- 対象 docTypeCode: 120, 140" + (", 160" if include_semiannual else ""))
                
                # Show failures as a dataframe or list
                if debug_logs:
                    st.write("直近のAPIレスポンス状況:")
                    df_log = pd.DataFrame(debug_logs)
                    st.dataframe(df_log)
                else:
                    st.write("ログがありません。")
        else:
            doc_desc = latest_doc.get('docDescription', '不明な書類')
            submit_date = latest_doc.get('submitDateTime', '')
            doc_id = latest_doc.get('docID')
            filer_name = latest_doc.get('filerName', '不明な提出者')
            doc_type_code = latest_doc.get('docTypeCode', 'N/A')
            
            st.success(f"書類が見つかりました: {filer_name}")
            st.subheader(f"📄 {doc_desc}")
            st.caption(f"提出日: {submit_date} | DocID: {doc_id} | TypeCode: {doc_type_code}")
            
            # Download PDF
            with st.spinner("PDFをダウンロード・展開中..."):
                pdf_bytes = ed_client.download_pdf(doc_id)
                
            if not pdf_bytes:
                st.error("PDFの取得に失敗しました。")
            else:
                st.success(f"PDF取得完了 ({len(pdf_bytes)/1024/1024:.2f} MB)")
                
                # Analyze with Gemini
                st.divider()
                st.subheader("🤖 AI分析レポート")
                
                with st.spinner(f"{model_name} が分析中..."):
                    try:
                        analyzer = ai_analyzer.GeminiAnalyzer(api_key=gemini_api_key, model_name=model_name)
                        report = analyzer.analyze_pdf(pdf_bytes, filename=f"{ticker_input}_{doc_id}.pdf")
                        
                        st.markdown(report)
                        
                        st.download_button(
                            label="レポートを保存",
                            data=report,
                            file_name=f"report_{ticker_input}.md",
                            mime="text/markdown"
                        )
                        
                    except Exception as e:
                        st.error(f"AI分析エラー: {e}")

# Footer
st.divider()
st.caption("Data Source: EDINET API v2 | Powered by Google Gemini")
