import requests
import io
import zipfile
import time
from datetime import datetime, timedelta
import streamlit as st

class EdinetClient:
    def __init__(self, api_key):
        self.base_url = "https://api.edinet-fsa.go.jp/api/v2"
        self.api_key = api_key
        self.headers = {
            "User-Agent": "EdinetAIAnalyst/1.0",
            "Accept": "application/json"
        }

    def debug_connection_test(self, date_str):
        """
        Directly hits documents.json for a specific date to test connectivity.
        Returns a dict with status, headers, and sample data.
        """
        url = f"{self.base_url}/documents.json"
        params = {
            'date': date_str,
            'type': 2,
            'Subscription-Key': self.api_key
        }
        
        try:
            # Explicitly verify=True (default) to catch SSL issues
            res = requests.get(url, params=params, headers=self.headers, timeout=10)
            
            result = {
                "status_code": res.status_code,
                "url": res.url, # Mask key if possible, but strictly this is debug
                "headers": dict(res.headers),
                "exception": None,
                "json_data": None,
                "json_metadata": None
            }
            
            try:
                data = res.json()
                result["json_data"] = data
                result["json_metadata"] = data.get('metadata')
            except Exception as e:
                result["json_data"] = f"Failed to parse JSON: {e}"
                
            return result
            
        except Exception as e:
            return {
                "status_code": "EXCEPTION",
                "url": url,
                "exception": str(e)
            }

    def search_latest_document(self, ticker, lookback_days=90, include_semiannual=True):
        """
        Scans daily document lists backwards.
        Returns (document, debug_logs).
        document is None if not found.
        debug_logs is a list of dicts describing what happened each day.
        """
        target_codes = {'120', '140'}
        if include_semiannual:
            target_codes.add('160')
            
        today = datetime.now()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        logs = [] # List to store debug info per day
        
        for i in range(lookback_days):
            target_date = today - timedelta(days=i)
            date_str = target_date.strftime('%Y-%m-%d')
            
            progress_bar.progress((i + 1) / lookback_days)
            status_text.text(f"Scanning: {date_str} ...")
            
            url = f"{self.base_url}/documents.json"
            params = {
                'date': date_str,
                'type': 2,
                'Subscription-Key': self.api_key
            }
            
            day_log = {"date": date_str, "status": "init", "details": ""}
            
            try:
                # Removed verify=False
                res = requests.get(url, params=params, headers=self.headers, timeout=10)
                day_log["status"] = res.status_code
                
                if res.status_code == 200:
                    try:
                        data = res.json()
                        metadata = data.get('metadata', {})
                        meta_status = metadata.get('status')
                        day_log["metadata_status"] = meta_status
                        
                        if meta_status and meta_status != '200':
                            day_log["details"] = f"API Error: {metadata.get('message')}"
                            logs.append(day_log)
                            continue
                            
                        results = data.get('results', [])
                        
                        # Debug: count total results
                        day_log["total_docs"] = len(results)
                        
                        # Filter logic
                        match_found = False
                        for doc in results:
                            sec_code = doc.get('secCode')
                            # Check ticker match
                            if sec_code and str(sec_code)[:4] == str(ticker):
                                # We found a ticker match! Now check other conditions
                                pdf_flag = doc.get('pdfFlag')
                                doc_type = doc.get('docTypeCode')
                                description = doc.get('docDescription', '')
                                withdrawn = doc.get('withdrawalStatus')
                                
                                # Detailed log for matched ticker
                                day_log["details"] = f"Ticker matched. Type={doc_type}, PDF={pdf_flag}, Desc={description}"
                                
                                if pdf_flag != '1':
                                    continue
                                if withdrawn == '1':
                                    continue
                                if doc_type not in target_codes:
                                    continue
                                if '訂正' in description:
                                    continue
                                
                                # Found match
                                progress_bar.empty()
                                status_text.empty()
                                return doc, logs # Return success
                            
                        if not match_found:
                            # Only log detail if we didn't find even a ticker match, to save space? 
                            # Or just say "No ticker match"
                            if day_log.get("details") == "":
                                day_log["details"] = "No matching ticker found"
                                
                    except ValueError as e:
                        day_log["details"] = f"JSON Parse Error: {e}"
                        
                elif res.status_code == 404:
                    day_log["details"] = "404 Not Found (Holiday?)"
                else:
                    day_log["details"] = f"HTTP Error {res.status_code}"
                    time.sleep(1) # Backoff
            
            except Exception as e:
                day_log["status"] = "EXCEPTION"
                day_log["details"] = str(e)
                time.sleep(1)
            
            logs.append(day_log)
            # Limit log size? Keep all for now since lookback is user defined, but maybe tail if huge?
            
        progress_bar.empty()
        status_text.empty()
        return None, logs

    def download_pdf(self, doc_id):
        """Downloads the PDF (extracting from ZIP if needed)."""
        url = f"{self.base_url}/documents/{doc_id}"
        params = {
            'type': 2,
            'Subscription-Key': self.api_key
        }
        
        try:
            # Removed verify=False
            res = requests.get(url, params=params, headers=self.headers, timeout=60, stream=True)
            res.raise_for_status()
            
            content_type = res.headers.get('Content-Type', '')
            
            if 'application/pdf' in content_type:
                return res.content
            
            if 'application/zip' in content_type or 'application/octet-stream' in content_type:
                with zipfile.ZipFile(io.BytesIO(res.content)) as z:
                    pdfs = [n for n in z.namelist() if n.lower().endswith('.pdf')]
                    if not pdfs:
                        return None
                    pdfs.sort(key=lambda n: z.getinfo(n).file_size, reverse=True)
                    target_file = pdfs[0]
                    with z.open(target_file) as f:
                        return f.read()
            return None
        except Exception as e:
            st.error(f"Download Error: {e}")
            return None
