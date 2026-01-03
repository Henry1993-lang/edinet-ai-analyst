import requests
import io
import zipfile
import time
from datetime import datetime, timedelta
import streamlit as st

# Suppress SSL warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class EdinetClient:
    def __init__(self, api_key):
        self.base_url = "https://api.edinet-fsa.go.jp/api/v2"
        self.api_key = api_key
        self.headers = {
            "User-Agent": "EdinetAIAnalyst/1.0",
            "Accept": "application/json"
        }

    def search_latest_document(self, ticker, lookback_days=90, include_semiannual=True):
        """
        Scans daily document lists backwards to find the latest Report.
        Filters by docTypeCode (not formCode).
        
        Targets:
        - 120: Annual Report (有価証券報告書)
        - 140: Quarterly Report (四半期報告書)
        - 160: Semi-annual Report (半期報告書) [Optional]
        """
        # Define target docTypeCodes
        target_codes = {'120', '140'}
        if include_semiannual:
            target_codes.add('160')
            
        today = datetime.now()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Debug info container
        debug_logs = []
        
        for i in range(lookback_days):
            target_date = today - timedelta(days=i)
            date_str = target_date.strftime('%Y-%m-%d')
            
            # Progress update
            progress_bar.progress((i + 1) / lookback_days)
            status_text.text(f"Scanning: {date_str} ...")
            
            url = f"{self.base_url}/documents.json"
            params = {
                'date': date_str,
                'type': 2,
                'Subscription-Key': self.api_key
            }
            
            try:
                res = requests.get(url, params=params, headers=self.headers, timeout=10, verify=False)
                
                if res.status_code == 200:
                    data = res.json()
                    
                    # Check metadata status if available
                    metadata = data.get('metadata', {})
                    if metadata.get('status') and metadata.get('status') != '200':
                        # Valid JSON but API internal error or empty
                        continue
                        
                    results = data.get('results', [])
                    if not results:
                        continue
                        
                    # Filter logic
                    for doc in results:
                        # 1. Check Ticker (secCode) - Match first 4 digits
                        sec_code = doc.get('secCode')
                        if not sec_code or str(sec_code)[:4] != str(ticker):
                            continue
                            
                        # 2. Check PDF Flag
                        if doc.get('pdfFlag') != '1':
                            continue
                        
                        # 3. Check Withdrawal Status (0: Normal, 1: Withdrawn)
                        # Not always present, but safe to check
                        if doc.get('withdrawalStatus') == '1':
                            continue

                        # 4. Check docTypeCode
                        doc_type_code = doc.get('docTypeCode')
                        if doc_type_code not in target_codes:
                            continue
                            
                        # 5. Exclude corrections (訂正)
                        doc_desc = doc.get('docDescription', '')
                        if '訂正' in doc_desc:
                            continue
                            
                        # Found a match!
                        progress_bar.empty()
                        status_text.empty()
                        return doc
                        
                elif res.status_code == 404:
                    continue
                else:
                    time.sleep(0.5)
                    
            except Exception as e:
                time.sleep(0.5)
                continue
                
        progress_bar.empty()
        status_text.empty()
        return None

    def download_pdf(self, doc_id):
        """Downloads the PDF (extracting from ZIP if needed)."""
        url = f"{self.base_url}/documents/{doc_id}"
        params = {
            'type': 2,
            'Subscription-Key': self.api_key
        }
        
        try:
            res = requests.get(url, params=params, headers=self.headers, timeout=60, stream=True, verify=False)
            res.raise_for_status()
            
            content_type = res.headers.get('Content-Type', '')
            
            # Direct PDF
            if 'application/pdf' in content_type:
                return res.content
            
            # ZIP containing PDF
            if 'application/zip' in content_type or 'application/octet-stream' in content_type:
                with zipfile.ZipFile(io.BytesIO(res.content)) as z:
                    # Find largest PDF
                    pdfs = [n for n in z.namelist() if n.lower().endswith('.pdf')]
                    if not pdfs:
                        return None
                    
                    # Sort by size desc
                    pdfs.sort(key=lambda n: z.getinfo(n).file_size, reverse=True)
                    target_file = pdfs[0]
                    
                    with z.open(target_file) as f:
                        return f.read()
            
            return None
            
        except Exception as e:
            st.error(f"Download Error: {e}")
            return None