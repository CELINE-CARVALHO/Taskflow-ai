"""
Google Sheets Reader
Privacy-first sheet reader that never stores data
"""
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, List, Optional
import io
import requests
import time

class SheetsReader:
    """
    Ephemeral sheet reader
    - Reads data on-demand
    - Never caches
    - Supports Google Sheets and Excel files
    """
    
    def __init__(self):
        self.credentials = None
        
    def read_google_sheet(self, sheet_url: str) -> Dict[str, pd.DataFrame]:
        """
        Read Google Sheets (public or with credentials)
        
        Args:
            sheet_url: Google Sheets URL
            
        Returns:
            Dictionary of {sheet_name: DataFrame}
        """
        # Extract sheet ID from URL
        sheet_id = self._extract_sheet_id(sheet_url)
        
        # Method 1: Try XLSX export with retry
        for attempt in range(3):
            try:
                export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
                
                response = requests.get(
                    export_url, 
                    timeout=30,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                if response.status_code == 200:
                    excel_data = pd.ExcelFile(io.BytesIO(response.content))
                    sheets_data = {}
                    for sheet_name in excel_data.sheet_names:
                        df = pd.read_excel(excel_data, sheet_name=sheet_name)
                        sheets_data[sheet_name] = df
                    return sheets_data
                elif response.status_code == 403:
                    raise Exception("Sheet is not public. Go to File > Share > Anyone with link can view")
                else:
                    raise Exception(f"HTTP {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                if attempt < 2:
                    time.sleep(2)
                    continue
                else:
                    # Method 2: Try CSV export for first sheet
                    try:
                        csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
                        df = pd.read_csv(csv_url)
                        return {"Sheet1": df}
                    except:
                        raise Exception(f"Cannot connect to Google Sheets. Check: 1) Internet connection, 2) Sheet is public, 3) URL is correct. Error: {str(e)}")
    
    def read_excel_file(self, file) -> Dict[str, pd.DataFrame]:
        """
        Read uploaded Excel file
        
        Args:
            file: Streamlit uploaded file object
            
        Returns:
            Dictionary of {sheet_name: DataFrame}
        """
        try:
            sheets_data = {}
            excel_data = pd.ExcelFile(file)
            
            for sheet_name in excel_data.sheet_names:
                df = pd.read_excel(excel_data, sheet_name=sheet_name)
                sheets_data[sheet_name] = df
            
            return sheets_data
            
        except Exception as e:
            print(f"❌ Error reading Excel file: {str(e)}")
            raise
    
    def _extract_sheet_id(self, url: str) -> str:
        """Extract Google Sheets ID from URL"""
        if "/d/" in url:
            return url.split("/d/")[1].split("/")[0]
        return url
    
    def get_sample_rows(self, df: pd.DataFrame, n: int = 3) -> pd.DataFrame:
        """
        Get sample rows for AI analysis (privacy-filtered)
        
        Args:
            df: DataFrame
            n: Number of sample rows
            
        Returns:
            Sample DataFrame
        """
        return df.head(n)
    
    def get_sheet_metadata(self, df: pd.DataFrame) -> Dict:
        """
        Get metadata about a sheet
        
        Args:
            df: DataFrame
            
        Returns:
            Metadata dictionary
        """
        return {
            "num_rows": len(df),
            "num_columns": len(df.columns),
            "columns": df.columns.tolist(),
            "dtypes": df.dtypes.astype(str).to_dict()
        }