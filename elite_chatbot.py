"""
ELITE AI CHATBOT - ChatGPT-Level Intelligence
Separate module with its own API key for unlimited power
"""
import os
import json
import time
from groq import Groq
import pandas as pd
from typing import Dict, Any, List
from dotenv import load_dotenv

load_dotenv()

class EliteChatbot:
    """
    Premium chatbot with ChatGPT-level understanding
    Uses separate API key for unlimited queries
    """
    
    def __init__(self):
        # Use separate API key for chatbot
        self.api_key = os.getenv("CHATBOT_API_KEY") or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("CHATBOT_API_KEY not found in .env")
        
        self.client = Groq(api_key=self.api_key)
        # Use BEST model for chatbot
        self.model = "llama-3.3-70b-versatile"
        self.conversation_history = []
        
    def answer(self, question: str, df: pd.DataFrame, column_mappings: Dict[str, str]) -> str:
        """
        Answer ANY question with ChatGPT-level intelligence
        """
        
        # Prepare comprehensive data context
        data_context = self._prepare_data_context(question, df, column_mappings)
        
        # Build intelligent prompt
        system_prompt = self._build_system_prompt(df, column_mappings)
        user_prompt = self._build_user_prompt(question, data_context)
        
        # Get AI response
        try:
            response = self._call_ai(system_prompt, user_prompt)
            
            # Store in conversation history
            self.conversation_history.append({
                'question': question,
                'answer': response,
                'timestamp': time.time()
            })
            
            return response
            
        except Exception as e:
            print(f"AI Error: {e}")
            # Intelligent fallback
            return self._intelligent_fallback(question, data_context, df, column_mappings)
    
    def _prepare_data_context(self, question: str, df: pd.DataFrame, col_map: Dict[str, str]) -> Dict[str, Any]:
        """
        Prepare comprehensive data context for AI
        """
        context = {
            'total_rows': len(df),
            'columns': list(df.columns),
            'column_mappings': col_map
        }
        
        # Detect what user is asking about
        q_lower = question.lower()
        
        # Search for keywords in question
        search_keywords = self._extract_keywords(question)
        
        if search_keywords:
            # Filter data based on keywords
            filtered_df = self._filter_by_keywords(df, search_keywords)
            context['filtered_rows'] = len(filtered_df)
            context['search_keywords'] = search_keywords
            
            if len(filtered_df) > 0:
                # Get detailed task information
                context['matching_tasks'] = self._extract_task_details(filtered_df, col_map)
        
        # Get statistics
        context['statistics'] = self._compute_statistics(df, col_map)
        
        # Get status distribution
        status_col = col_map.get('status', 'none')
        if status_col != 'none' and status_col in df.columns:
            context['status_distribution'] = df[status_col].value_counts().to_dict()
        
        # Get priority distribution
        priority_col = col_map.get('priority', 'none')
        if priority_col != 'none' and priority_col in df.columns:
            context['priority_distribution'] = df[priority_col].value_counts().to_dict()
        
        return context
    
    def _extract_keywords(self, question: str) -> List[str]:
        """
        Extract search keywords from question
        """
        q_lower = question.lower()
        keywords = []
        
        # Common tech/component keywords
        tech_keywords = [
            'frontend', 'backend', 'api', 'database', 'ui', 'ux', 'design',
            'mobile', 'web', 'server', 'client', 'testing', 'qa', 'devops',
            'infrastructure', 'security', 'auth', 'payment', 'dashboard',
            'admin', 'user', 'profile', 'settings', 'login', 'signup',
            'checkout', 'cart', 'search', 'filter', 'notification', 'email',
            'analytics', 'reporting', 'integration', 'deployment', 'bug',
            'feature', 'enhancement', 'refactor', 'optimization', 'performance'
        ]
        
        for keyword in tech_keywords:
            if keyword in q_lower:
                keywords.append(keyword)
        
        # Extract quoted phrases
        import re
        quoted = re.findall(r'"([^"]*)"', question)
        keywords.extend(quoted)
        
        return list(set(keywords))  # Remove duplicates
    
    def _filter_by_keywords(self, df: pd.DataFrame, keywords: List[str]) -> pd.DataFrame:
        """
        Filter dataframe by keywords (search ALL columns)
        """
        if not keywords:
            return df
        
        mask = pd.Series([False] * len(df))
        
        # Search across ALL columns
        for col in df.columns:
            col_str = df[col].astype(str).str.lower()
            for keyword in keywords:
                mask |= col_str.str.contains(keyword, na=False, regex=False)
        
        return df[mask]
    
    def _extract_task_details(self, df: pd.DataFrame, col_map: Dict[str, str]) -> List[Dict]:
        """
        Extract detailed task information
        """
        tasks = []
        
        # Get relevant columns
        title_col = col_map.get('title', col_map.get('assignee', 'none'))
        status_col = col_map.get('status', 'none')
        priority_col = col_map.get('priority', 'none')
        errors_col = col_map.get('errors', 'none')
        
        for idx, row in df.head(10).iterrows():  # Max 10 tasks
            task = {}
            
            # Get all non-empty values
            for col in df.columns:
                val = row[col]
                if pd.notna(val) and str(val).strip():
                    task[col] = str(val)
            
            tasks.append(task)
        
        return tasks
    
    def _compute_statistics(self, df: pd.DataFrame, col_map: Dict[str, str]) -> Dict:
        """
        Compute comprehensive statistics
        """
        stats = {'total': len(df)}
        
        # Status stats
        status_col = col_map.get('status', 'none')
        if status_col != 'none' and status_col in df.columns:
            stats['pending'] = len(df[df[status_col].astype(str).str.lower().str.contains('pending|progress|ongoing|todo|open', na=False, regex=True)])
            stats['completed'] = len(df[df[status_col].astype(str).str.lower().str.contains('completed|done|finished|closed', na=False, regex=True)])
            stats['blocked'] = len(df[df[status_col].astype(str).str.lower().str.contains('blocked|hold', na=False, regex=True)])
        
        # Error stats
        errors_col = col_map.get('errors', 'none')
        if errors_col != 'none' and errors_col in df.columns:
            stats['total_errors'] = int(df[errors_col].sum())
            stats['tasks_with_errors'] = int((df[errors_col] > 0).sum())
            stats['avg_errors'] = round(df[errors_col].mean(), 2)
        
        # Priority stats
        priority_col = col_map.get('priority', 'none')
        if priority_col != 'none' and priority_col in df.columns:
            stats['high_priority'] = len(df[df[priority_col].astype(str).str.lower().str.contains('high|critical|urgent', na=False, regex=True)])
        
        return stats
    
    def _build_system_prompt(self, df: pd.DataFrame, col_map: Dict[str, str]) -> str:
        """
        Build comprehensive system prompt
        """
        return f"""You are an intelligent data analyst assistant helping a user understand their work tasks.

You have access to their COMPLETE task database with {len(df)} tasks.

Available data columns: {', '.join(df.columns)}

Column mappings: {json.dumps(col_map, indent=2)}

Your capabilities:
1. Search and filter tasks by ANY criteria (technology, status, priority, keywords)
2. Provide detailed analysis and insights
3. List specific tasks with all relevant details
4. Calculate statistics and percentages
5. Give actionable recommendations

Response guidelines:
- Be conversational and helpful like ChatGPT
- Use the ACTUAL data provided to you
- When listing tasks, include task names/titles and relevant details
- Provide specific numbers and percentages
- If filtering, clearly state how many tasks matched
- Give insights and context, not just raw numbers
- If user asks for tasks related to something, SEARCH the data and list matching tasks

IMPORTANT: 
- Always use the actual data context provided
- Be specific and detailed
- List actual task names when asked to show tasks
- Provide actionable insights"""
    
    def _build_user_prompt(self, question: str, context: Dict[str, Any]) -> str:
        """
        Build user prompt with data context
        """
        prompt = f"User Question: {question}\n\n"
        prompt += f"=== DATA CONTEXT ===\n"
        prompt += f"Total Tasks: {context['total_rows']}\n\n"
        
        # Statistics
        if 'statistics' in context:
            stats = context['statistics']
            prompt += f"Statistics:\n"
            for key, val in stats.items():
                prompt += f"- {key}: {val}\n"
            prompt += "\n"
        
        # Filtered results
        if 'search_keywords' in context:
            prompt += f"User is searching for: {', '.join(context['search_keywords'])}\n"
            prompt += f"Matching tasks: {context.get('filtered_rows', 0)}\n\n"
            
            if context.get('matching_tasks'):
                prompt += "MATCHING TASKS DETAILS:\n"
                for i, task in enumerate(context['matching_tasks'], 1):
                    prompt += f"\nTask {i}:\n"
                    for key, val in task.items():
                        prompt += f"  - {key}: {val}\n"
                prompt += "\n"
        
        # Status distribution
        if 'status_distribution' in context:
            prompt += f"Status Distribution: {json.dumps(context['status_distribution'], indent=2)}\n\n"
        
        # Priority distribution
        if 'priority_distribution' in context:
            prompt += f"Priority Distribution: {json.dumps(context['priority_distribution'], indent=2)}\n\n"
        
        prompt += "=== INSTRUCTIONS ===\n"
        prompt += "Provide a helpful, detailed answer based on the data above.\n"
        prompt += "If the user asked to see/show/list tasks, list them with their details.\n"
        prompt += "Be conversational and insightful like ChatGPT."
        
        return prompt
    
    def _call_ai(self, system_prompt: str, user_prompt: str) -> str:
        """
        Call AI with retry logic
        """
        for attempt in range(3):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,  # More creative
                    max_tokens=1500,  # Longer responses
                )
                
                return response.choices[0].message.content.strip()
                
            except Exception as e:
                if "rate_limit" in str(e).lower() or "429" in str(e):
                    if attempt < 2:
                        wait = 2 ** attempt
                        print(f"⏳ Rate limit, waiting {wait}s...")
                        time.sleep(wait)
                        continue
                raise e
        
        raise Exception("Failed after retries")
    
    def _intelligent_fallback(self, question: str, context: Dict, df: pd.DataFrame, col_map: Dict) -> str:
        """
        Intelligent fallback when AI fails
        """
        q_lower = question.lower()
        
        # Keyword search
        if context.get('search_keywords'):
            keywords = context['search_keywords']
            count = context.get('filtered_rows', 0)
            
            if count == 0:
                return f"I searched for **{', '.join(keywords)}** but found no matching tasks in your {context['total_rows']} tasks."
            
            answer = f"I found **{count} tasks** related to **{', '.join(keywords)}**:\n\n"
            
            if context.get('matching_tasks'):
                for i, task in enumerate(context['matching_tasks'][:5], 1):
                    # Get title
                    title = task.get('Task Title') or task.get('Title') or task.get('Description') or task.get(list(task.keys())[0] if task else 'Unknown')
                    # Get status
                    status = task.get('Status') or task.get('State') or task.get('Current Status') or 'Unknown'
                    
                    answer += f"**{i}. {title}**\n"
                    answer += f"   Status: {status}\n"
                    
                    # Add other relevant fields
                    for key, val in task.items():
                        if key not in ['Task Title', 'Title', 'Description', 'Status', 'State', 'Current Status']:
                            answer += f"   {key}: {val}\n"
                    answer += "\n"
                
                if count > 5:
                    answer += f"... and {count - 5} more tasks"
            
            return answer
        
        # Summary
        if 'summary' in q_lower or 'overview' in q_lower:
            stats = context.get('statistics', {})
            answer = f"**Summary of Your {stats.get('total', 0)} Tasks:**\n\n"
            
            if context.get('status_distribution'):
                answer += "**By Status:**\n"
                for status, count in context['status_distribution'].items():
                    pct = round(count / stats['total'] * 100, 1)
                    answer += f"• {status}: {count} ({pct}%)\n"
                answer += "\n"
            
            if stats.get('total_errors', 0) > 0:
                answer += f"**Quality Metrics:**\n"
                answer += f"• Total errors: {stats['total_errors']}\n"
                answer += f"• Tasks with errors: {stats['tasks_with_errors']}\n"
            
            return answer
        
        # Default
        return f"You have **{context['total_rows']} tasks**. Ask me to show you specific tasks (e.g., 'show me frontend tasks') or request a summary."
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []