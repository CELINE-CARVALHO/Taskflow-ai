"""
LLM Client with Rate Limit Handling
"""
import os
import json
import time
from groq import Groq
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHATBOT_API_KEY = os.getenv("CHATBOT_API_KEY")

class LLMClient:
    """
    LLM client with rate limit handling
    """
    
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found")
        
        self.client = Groq(api_key=self.api_key)
        # Use SMALLER, FASTER model to avoid rate limits
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        
    def call_llm(self, prompt: str, system_message: str = None, max_retries: int = 3) -> Dict[str, Any]:
        """
        Call LLM with retry logic
        """
        for attempt in range(max_retries):
            try:
                messages = []
                
                if system_message:
                    messages.append({"role": "system", "content": system_message})
                
                messages.append({"role": "user", "content": prompt})
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=500,  # REDUCED tokens to avoid rate limit
                    response_format={"type": "json_object"}
                )
                
                content = response.choices[0].message.content
                
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    return self._extract_json(content)
                    
            except Exception as e:
                error_str = str(e)
                
                # Rate limit error - wait and retry
                if "rate_limit" in error_str.lower() or "429" in error_str:
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                        print(f"⏳ Rate limit hit, waiting {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return {"error": "rate_limit", "message": "API rate limit reached"}
                
                # Other errors
                print(f"❌ LLM Error: {error_str}")
                return {"error": str(e)}
        
        return {"error": "Max retries exceeded"}
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text"""
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
        except:
            pass
        return {"error": "Could not parse JSON"}
    
    def test_connection(self) -> bool:
        """Test API"""
        try:
            response = self.call_llm(
                "Return JSON: {\"status\": \"ok\"}",
                "You are helpful. Respond with valid JSON."
            )
            return response.get("status") == "ok"
        except:
            return False