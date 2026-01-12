"""
OpenRouter API Client
blitz 프로젝트 형식 기반 안정적인 LLM 호출
"""

import requests
from .keys import get_openrouter_key

class OpenRouterClient:
    """OpenRouter API 클라이언트"""
    
    ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
    
    def __init__(self, model: str = "google/gemini-3.0-flash"):
        self.model = model
        self.api_key = get_openrouter_key()
    
    def chat(
        self,
        messages: list[dict],
        max_tokens: int = 4096,
        temperature: float = 0.7,
        timeout: int = 60
    ) -> dict:
        """
        채팅 완료 요청
        
        Args:
            messages: [{"role": "system"|"user"|"assistant", "content": "..."}]
            max_tokens: 최대 토큰 수
            temperature: 창의성 (0.0 ~ 1.0)
            timeout: 타임아웃 (초)
        
        Returns:
            {"success": bool, "content": str, "usage": dict, "error": str|None}
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/ain-lang/ain",
            "X-Title": "AIN",
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        try:
            response = requests.post(
                self.ENDPOINT,
                headers=headers,
                json=data,
                timeout=timeout
            )
            result = response.json()
            
            if "choices" not in result:
                return {
                    "success": False,
                    "content": "",
                    "usage": {},
                    "error": f"API Error: {result}"
                }
            
            return {
                "success": True,
                "content": result["choices"][0]["message"]["content"],
                "usage": result.get("usage", {}),
                "error": None
            }
            
        except requests.Timeout:
            return {"success": False, "content": "", "usage": {}, "error": "Request timeout"}
        except Exception as e:
            return {"success": False, "content": "", "usage": {}, "error": str(e)}
    
    def simple_chat(self, system_prompt: str, user_message: str, **kwargs) -> str:
        """간단한 채팅 (system + user 메시지)"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        result = self.chat(messages, **kwargs)
        return result["content"] if result["success"] else f"Error: {result['error']}"
