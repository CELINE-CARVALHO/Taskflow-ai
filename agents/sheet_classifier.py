"""
Sheet Classifier Agent
Determines if a sheet is relevant and what type it is
"""
from typing import Dict, Any
import pandas as pd
from utils.llm_client import LLMClient
from utils.privacy_filter import PrivacyFilter

class SheetClassifierAgent:
    """
    Classifies sheets to determine relevance
    PRIVACY: Only sends sheet name, columns, and 3 sample rows
    """
    
    SYSTEM_MESSAGE = """You are analyzing a Google Sheets workbook.

Your task:
1. Decide whether this sheet is relevant for tracking work, tasks, issues, or progress.
2. Identify what type of data the sheet contains.

Return ONLY valid JSON in this format:

{
  "relevant": true or false,
  "sheet_type": "task_tracking" or "issue_tracking" or "report" or "summary" or "irrelevant",
  "description": "short explanation"
}

Do not guess.
If the sheet does not look useful, mark relevant=false."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def classify_sheet(self, sheet_name: str, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Classify a single sheet
        
        Args:
            sheet_name: Name of the sheet
            df: DataFrame containing sheet data
            
        Returns:
            Classification result
        """
        # Prepare privacy-safe data
        safe_data = PrivacyFilter.prepare_for_ai(df, max_rows=3)
        
        prompt = f"""Analyze this sheet:

Sheet Name: {sheet_name}

Columns: {', '.join(safe_data['columns'])}

Sample Rows (first 3):
{self._format_sample_data(safe_data['sample_data'])}

Total Rows: {safe_data['total_rows']}

Is this sheet relevant for work tracking? What type is it?"""
        
        result = self.llm.call_llm(prompt, self.SYSTEM_MESSAGE)
        
        # Add metadata
        result['sheet_name'] = sheet_name
        result['num_rows'] = len(df)
        result['num_columns'] = len(df.columns)
        
        return result
    
    def _format_sample_data(self, sample_data: list) -> str:
        """Format sample data for AI readability"""
        if not sample_data:
            return "No data"
        
        lines = []
        for i, row in enumerate(sample_data, 1):
            row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
            lines.append(f"  Row {i}: {row_str}")
        
        return "\n".join(lines)