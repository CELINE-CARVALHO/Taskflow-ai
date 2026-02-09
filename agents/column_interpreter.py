"""
Column Interpreter Agent
Infers semantic meaning of columns without hardcoding
"""
from typing import Dict, Any
import pandas as pd
from utils.llm_client import LLMClient
from utils.privacy_filter import PrivacyFilter

class ColumnInterpreterAgent:
    """
    Interprets column meanings dynamically
    PRIVACY: Only sends column names and 3-5 sample rows
    """
    
    SYSTEM_MESSAGE = """You are interpreting a spreadsheet used to track work.

Identify which columns represent the following concepts:
- assignee: who the task is assigned to
- status: progress or state of the task
- errors: issues, mistakes, rejections, or problem count
- notes: comments or remarks
- title: task name or description
- date: when task was created or due
- priority: importance level

If a concept does not exist, return "none".

Return ONLY valid JSON in this format:

{
  "assignee": "<column name or 'none'>",
  "status": "<column name or 'none'>",
  "errors": "<column name or 'none'>",
  "notes": "<column name or 'none'>",
  "title": "<column name or 'none'>",
  "date": "<column name or 'none'>",
  "priority": "<column name or 'none'>"
}"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def interpret_columns(self, df: pd.DataFrame, sheet_name: str = "") -> Dict[str, str]:
        """
        Interpret column meanings
        
        Args:
            df: DataFrame to analyze
            sheet_name: Optional sheet name for context
            
        Returns:
            Dictionary mapping concepts to column names
        """
        # Prepare privacy-safe data
        safe_data = PrivacyFilter.prepare_for_ai(df, max_rows=5)
        
        prompt = f"""Analyze this spreadsheet:

Sheet: {sheet_name}

Columns: {', '.join(safe_data['columns'])}

Sample Rows (first 5):
{self._format_sample_data(safe_data['sample_data'])}

Which columns represent: assignee, status, errors, notes, title, date, priority?"""
        
        result = self.llm.call_llm(prompt, self.SYSTEM_MESSAGE)
        
        # Validate and clean result
        cleaned = {}
        for key in ['assignee', 'status', 'errors', 'notes', 'title', 'date', 'priority']:
            value = result.get(key, 'none')
            # Check if column actually exists
            if value != 'none' and value not in df.columns:
                cleaned[key] = 'none'
            else:
                cleaned[key] = value
        
        return cleaned
    
    def _format_sample_data(self, sample_data: list) -> str:
        """Format sample data for AI readability"""
        if not sample_data:
            return "No data"
        
        lines = []
        for i, row in enumerate(sample_data, 1):
            row_str = ", ".join([f"{k}: {v}" for k, v in row.items()])
            lines.append(f"  Row {i}: {row_str}")
        
        return "\n".join(lines)