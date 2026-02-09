"""
Privacy Filter
Ensures no sensitive data is sent to AI or stored
"""
import pandas as pd
from typing import List, Dict, Any

class PrivacyFilter:
    """
    Privacy-first data filter
    - Masks sensitive data
    - Limits data sent to AI
    - Never logs or stores
    """
    
    @staticmethod
    def filter_for_user(df: pd.DataFrame, user_identifier: str, assignee_column: str) -> pd.DataFrame:
        """
        Filter dataframe to show only user's rows
        
        Args:
            df: Full dataframe
            user_identifier: User name/email
            assignee_column: Column containing assignee info
            
        Returns:
            Filtered dataframe
        """
        if assignee_column and assignee_column in df.columns:
            # Case-insensitive partial match
            mask = df[assignee_column].astype(str).str.contains(
                user_identifier, 
                case=False, 
                na=False
            )
            return df[mask].copy()
        
        return df.copy()
    
    @staticmethod
    def prepare_for_ai(df: pd.DataFrame, max_rows: int = 3) -> Dict[str, Any]:
        """
        Prepare minimal data for AI analysis
        
        Args:
            df: DataFrame
            max_rows: Maximum rows to send
            
        Returns:
            Safe data dict for AI
        """
        sample = df.head(max_rows)
        
        return {
            "columns": df.columns.tolist(),
            "sample_data": sample.to_dict('records'),
            "total_rows": len(df)
        }
    
    @staticmethod
    def mask_sensitive_data(df: pd.DataFrame, columns_to_mask: List[str] = None) -> pd.DataFrame:
        """
        Mask sensitive columns for AI preview
        
        Args:
            df: DataFrame
            columns_to_mask: List of column names to mask
            
        Returns:
            Masked dataframe
        """
        masked_df = df.copy()
        
        # Auto-detect potential PII columns
        pii_keywords = ['email', 'phone', 'ssn', 'password', 'address']
        
        for col in masked_df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in pii_keywords):
                masked_df[col] = "***MASKED***"
            elif columns_to_mask and col in columns_to_mask:
                masked_df[col] = "***MASKED***"
        
        return masked_df
    
    @staticmethod
    def compute_safe_metrics(df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """
        Compute aggregate metrics (safe to share with AI)
        
        Args:
            df: DataFrame
            column: Column to analyze
            
        Returns:
            Aggregate metrics
        """
        if column not in df.columns:
            return {}
        
        metrics = {
            "unique_values": df[column].nunique(),
            "null_count": df[column].isnull().sum(),
            "total_count": len(df)
        }
        
        # Value counts (top 10 only)
        if df[column].dtype == 'object':
            value_counts = df[column].value_counts().head(10).to_dict()
            metrics["top_values"] = value_counts
        
        return metrics