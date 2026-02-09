"""
TRULY SMART Question Interpreter
Actually reads and understands your full data
"""
from typing import Dict, Any
from utils.llm_client import LLMClient
import pandas as pd
import time

class QuestionInterpreterAgent:
    """
    Intelligent chatbot that actually analyzes your data
    """
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
        self.last_call = 0
    
    def answer_question(
        self, 
        question: str,
        df: pd.DataFrame,
        column_mappings: Dict[str, str],
        available_dimensions: list
    ) -> str:
        """
        Answer ANY question by actually analyzing the data
        """
        
        # Rate limiting
        elapsed = time.time() - self.last_call
        if elapsed < 1:
            time.sleep(1 - elapsed)
        self.last_call = time.time()
        
        # Analyze data based on question
        q_lower = question.lower()
        
        # Extract relevant data
        data_context = self._extract_relevant_data(question, df, column_mappings)
        
        # Use LLM to understand and answer
        return self._intelligent_answer(question, data_context, df, column_mappings)
    
    def _extract_relevant_data(self, question, df, col_map):
        """
        Extract data relevant to the question
        """
        q_lower = question.lower()
        context = {
            'total_tasks': len(df),
            'columns': list(df.columns),
            'sample_data': []
        }
        
        # Check what user is asking about
        search_terms = []
        
        # Technology/component search
        tech_terms = ['frontend', 'backend', 'api', 'database', 'ui', 'mobile', 'web', 'design', 'testing']
        for term in tech_terms:
            if term in q_lower:
                search_terms.append(term)
        
        # If searching for specific terms, filter data
        if search_terms:
            filtered_df = df.copy()
            
            # Search across ALL columns for the term
            for term in search_terms:
                mask = pd.Series([False] * len(filtered_df))
                for col in filtered_df.columns:
                    mask |= filtered_df[col].astype(str).str.lower().str.contains(term, na=False)
                filtered_df = filtered_df[mask]
            
            context['filtered_count'] = len(filtered_df)
            context['search_terms'] = search_terms
            
            # Get sample of filtered data
            if len(filtered_df) > 0:
                context['filtered_tasks'] = filtered_df.to_dict('records')[:10]  # First 10 matching tasks
        
        # Status info
        status_col = col_map.get('status', 'none')
        if status_col != 'none' and status_col in df.columns:
            context['status_breakdown'] = df[status_col].value_counts().to_dict()
        
        # Get all unique values from key columns
        for concept, col_name in col_map.items():
            if col_name != 'none' and col_name in df.columns:
                unique_vals = df[col_name].unique()[:20]  # First 20 unique values
                context[f'{concept}_values'] = list(unique_vals)
        
        return context
    
    def _intelligent_answer(self, question, context, df, col_map):
        """
        Use LLM to generate intelligent answer based on actual data
        """
        
        # Build comprehensive prompt with actual data
        system_msg = """You are a smart data analyst. Answer the user's question based on their ACTUAL data provided.

Be specific and helpful. Use the exact data provided. If filtering by terms, tell them which tasks match."""

        # Prepare data summary
        data_summary = f"""Total Tasks: {context['total_tasks']}
Available Columns: {', '.join(context['columns'])}
"""
        
        if context.get('search_terms'):
            data_summary += f"\nSearching for: {', '.join(context['search_terms'])}"
            data_summary += f"\nMatching Tasks: {context.get('filtered_count', 0)}"
            
            if context.get('filtered_tasks'):
                data_summary += f"\n\nMatching Tasks Details:\n"
                for idx, task in enumerate(context['filtered_tasks'][:5], 1):
                    data_summary += f"\n{idx}. "
                    # Show relevant fields
                    for key, val in task.items():
                        if val and str(val).lower() != 'nan':
                            data_summary += f"{key}: {val}, "
        
        if context.get('status_breakdown'):
            data_summary += f"\n\nStatus Breakdown: {context['status_breakdown']}"
        
        prompt = f"""Question: "{question}"

User's Actual Data:
{data_summary}

Provide a helpful, specific answer based on the ACTUAL data above. If filtering, list the matching tasks."""

        try:
            result = self.llm.call_llm(prompt, system_msg)
            
            if result.get('error'):
                return self._fallback_answer(question, context, df, col_map)
            
            # Extract answer
            answer = result.get('answer') or result.get('response') or result.get('text') or str(result)
            
            # Clean up
            if answer.startswith('{'):
                answer = str(result)
            
            # Add context if it was a search
            if context.get('search_terms') and context.get('filtered_count'):
                if context['filtered_count'] == 0:
                    answer = f"I found **0 tasks** matching '{', '.join(context['search_terms'])}' in your data."
                else:
                    if len(answer) < 50:  # LLM gave short answer, enhance it
                        answer = f"I found **{context['filtered_count']} tasks** related to {', '.join(context['search_terms'])}.\n\n{answer}"
            
            return answer
            
        except Exception as e:
            return self._fallback_answer(question, context, df, col_map)
    
    def _fallback_answer(self, question, context, df, col_map):
        """
        Fallback for when LLM fails - still be smart about it
        """
        q_lower = question.lower()
        
        # Filtering questions
        if context.get('search_terms'):
            terms = context['search_terms']
            count = context.get('filtered_count', 0)
            
            if count == 0:
                return f"I found **0 tasks** matching '{', '.join(terms)}' in your {context['total_tasks']} tasks."
            
            answer = f"I found **{count} tasks** related to {', '.join(terms)}:\n\n"
            
            if context.get('filtered_tasks'):
                for idx, task in enumerate(context['filtered_tasks'][:5], 1):
                    title = task.get('Task Title') or task.get('Title') or task.get('Description') or 'Task'
                    status = task.get('Status') or task.get('State') or task.get('Current Status') or 'Unknown'
                    answer += f"{idx}. {title} - Status: {status}\n"
                
                if count > 5:
                    answer += f"\n... and {count - 5} more tasks"
            
            return answer
        
        # Status questions
        status_col = col_map.get('status', 'none')
        if 'status' in q_lower and status_col != 'none':
            breakdown = context.get('status_breakdown', {})
            if breakdown:
                answer = f"**Status Breakdown:**\n"
                for status, count in breakdown.items():
                    pct = round(count / context['total_tasks'] * 100, 1)
                    answer += f"• {status}: {count} ({pct}%)\n"
                return answer
        
        # Summary
        if 'summary' in q_lower:
            answer = f"**Summary of {context['total_tasks']} Tasks:**\n\n"
            if context.get('status_breakdown'):
                answer += "**Status:**\n"
                for status, count in list(context.get('status_breakdown', {}).items())[:5]:
                    answer += f"• {status}: {count}\n"
            return answer
        
        # Default
        return f"You have {context['total_tasks']} tasks. Try asking about specific areas like 'frontend', 'backend', or request a summary."