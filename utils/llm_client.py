"""
LLM Client with Rate Limit Handling
"""
import os

# 🔥 MUST come FIRST — before groq / httpx is imported
for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(k, None)

import json
import time
from typing import Dict, Any
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found")

        self.client = Groq(api_key=self.api_key)
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    def call_llm(
        self,
        prompt: str,
        system_message: str = None,
        max_retries: int = 3
    ) -> Dict[str, Any]:

        for attempt in range(max_retries):
            try:
                messages = []
                if system_message:
                    messages.append(
                        {"role": "system", "content": system_message}
                    )
                messages.append(
                    {"role": "user", "content": prompt}
                )

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=500,
                    response_format={"type": "json_object"},
                )

                content = response.choices[0].message.content
                return json.loads(content)

            except Exception as e:
                if "rate" in str(e).lower() and attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                    continue
                return {"error": str(e)}

        return {"error": "Max retries exceeded"}

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from text"""
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
        except Exception:
            pass
        return {"error": "Could not parse JSON"}

    def test_connection(self) -> bool:
        """Test API"""
        try:
            response = self.call_llm(
                'Return JSON: {"status": "ok"}',
                "You are helpful. Respond with valid JSON."
            )
            return response.get("status") == "ok"
        except Exception:
            return False
