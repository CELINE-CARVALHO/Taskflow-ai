"""
Dashboard Builder Agent
Decides what metrics and visualizations to show
"""
from typing import Dict, Any, List
import pandas as pd
from utils.llm_client import LLMClient

class DashboardBuilderAgent:
    """
    Designs dashboard layout based on data structure
    PRIVACY: Only receives column mappings and aggregate counts
    """
    
    SYSTEM_MESSAGE = """You are designing a dashboard for a working professional.

Your task:
1. Decide what metrics are useful
2. Decide what charts (if any) make sense
3. Decide what table view is helpful

Return ONLY valid JSON in this format:

{
  "title": "Dashboard title",
  "metrics": [
    { "label": "Total Tasks", "intent": "count" },
    { "label": "Pending Tasks", "intent": "condition" }
  ],
  "charts": [
    { "type": "bar" or "pie", "dimension": "status" or "errors" or "priority" }
  ],
  "table": {
    "show": true or false,
    "focus": "pending" or "all" or "issues"
  }
}

Do not include UI code.
Do not reference column names directly."""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def build_dashboard_config(
        self, 
        sheet_type: str,
        column_mappings: Dict[str, str],
        total_rows: int,
        sheet_name: str = ""
    ) -> Dict[str, Any]:
        """
        Generate dashboard configuration
        
        Args:
            sheet_type: Type of sheet (task_tracking, issue_tracking, etc.)
            column_mappings: Mapping of concepts to column names
            total_rows: Total number of rows
            sheet_name: Name of the sheet
            
        Returns:
            Dashboard configuration
        """
        # Prepare context for AI
        available_dimensions = [k for k, v in column_mappings.items() if v != 'none']
        
        prompt = f"""Design a dashboard for this sheet:

Sheet: {sheet_name}
Type: {sheet_type}
Total Rows: {total_rows}

Available Data Dimensions:
{', '.join(available_dimensions)}

What metrics, charts, and table views would be most useful?"""
        
        result = self.llm.call_llm(prompt, self.SYSTEM_MESSAGE)
        
        # Store column mappings for later use
        result['column_mappings'] = column_mappings
        
        return result
    
    def compute_metrics(
        self, 
        df: pd.DataFrame, 
        metrics_config: List[Dict],
        column_mappings: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """
        Compute actual metric values (Python does computation, not AI)
        
        Args:
            df: Filtered user dataframe
            metrics_config: Metrics from dashboard config
            column_mappings: Column name mappings
            
        Returns:
            List of computed metrics
        """
        computed = []
        
        for metric in metrics_config:
            intent = metric.get('intent', 'count')
            label = metric.get('label', 'Metric')
            
            if intent == 'count':
                value = len(df)
            elif intent == 'condition':
                # Try to find pending/in-progress items
                status_col = column_mappings.get('status', 'none')
                if status_col != 'none' and status_col in df.columns:
                    # Count non-completed items
                    pending_keywords = ['pending', 'in progress', 'ongoing', 'todo', 'open']
                    mask = df[status_col].astype(str).str.lower().apply(
                        lambda x: any(kw in x for kw in pending_keywords)
                    )
                    value = mask.sum()
                else:
                    value = 0
            else:
                value = 0
            
            computed.append({
                'label': label,
                'value': value
            })
        
        return computed