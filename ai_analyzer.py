from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import os
import tempfile
import time
import streamlit as st

class GeminiAnalyzer:
    def __init__(self, api_key, model_name="gemini-2.0-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def _is_retryable_error(self, exception):
        """Custom check for 429 errors in the new SDK."""
        msg = str(exception).lower()
        return "429" in msg or "resource" in msg or "exhausted" in msg

    @retry(
        retry=retry_if_exception_type(Exception),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        stop=stop_after_attempt(5)
    )
    def _generate_content_with_retry(self, contents, config):
        """
        Executes generation with automatic retry for Rate Limits (429).
        """
        return self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config
        )

    def analyze_pdf(self, pdf_bytes, filename="document.pdf"):
        """
        Uploads PDF to Gemini and performs analysis.
        Returns the text response.
        """
        # Create a temporary file to upload
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_file.write(pdf_bytes)
            tmp_path = tmp_file.name

        try:
            # 1. Upload File
            print(f"Uploading {filename} to Gemini...")
            # google-genai upload (use 'file=' instead of 'path=')
            uploaded_file = self.client.files.upload(
                file=tmp_path, 
                config=types.UploadFileConfig(display_name=filename)
            )
            
            # Wait for processing state
            while uploaded_file.state.name == "PROCESSING":
                time.sleep(2)
                uploaded_file = self.client.files.get(name=uploaded_file.name)
            
            if uploaded_file.state.name == "FAILED":
                # Detail the failure in the exception
                raise ValueError(f"Gemini file processing failed for {filename}. State: {uploaded_file.state.name}")

            # 2. Define System Prompt
            system_prompt = """
            あなたはプロの証券アナリストです。
            提供された決算資料（有価証券報告書または決算短信）に基づき、投資家向けの分析レポートを作成してください。
            
            出力は以下のセクションを含む構造化されたMarkdown形式のみとしてください。
            
            ## 1. エグゼクティブ・サマリー
            全体の内容を3行以内で簡潔に要約してください。ポジティブな要素とネガティブな要素の両方を含めてください。
            
            ## 2. 業績ハイライト
            売上高、営業利益、純利益などの主要数値の増減と、その主な要因（セグメント別の好不調など）を具体的に記述してください。
            
            ## 3. リスク分析
            経営陣が認識している主要なリスク、市場環境の懸念点、サプライチェーンの問題などを抽出してください。
            
            ## 4. 将来見通し
            次期の数値目標、会社側が発表している定性的な見通し、中期経営計画の進捗などをまとめてください。
            
            ## 5. キラリと光る点
            この企業の技術力、市場シェア、ユニークな新規事業、ESGへの取り組みなど、他社と差別化される特筆すべき強みを挙げてください。
            """

            # 3. Generate Content
            config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.2,
            )

            response = self._generate_content_with_retry(
                contents=[uploaded_file, "この資料を要約し、投資判断に重要な論点を整理してください。"],
                config=config
            )
            
            return response.text

        finally:
            # Cleanup local temp file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            # Note: We are not deleting the file from Gemini Cloud here.
