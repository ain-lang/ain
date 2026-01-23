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

            # content가 None, 빈 문자열, whitespace-only인 경우 처리
            content = result["choices"][0]["message"].get("content")
            finish_reason = result["choices"][0].get("finish_reason", "unknown")
            usage = result.get("usage", {})

            # 빈 응답 체크 (None, "", "   " 모두 포함)
            if not content or not content.strip():
                # finish_reason별 상세 로깅
                reason_msg = {
                    "stop": "정상 완료인데 content 비어있음 (API 버그 가능성)",
                    "length": "최대 토큰 도달로 content 잘림",
                    "content_filter": "콘텐츠 필터링으로 차단됨",
                    "error": "API 내부 에러",
                }.get(finish_reason, f"알 수 없는 이유: {finish_reason}")

                print(f"⚠️ OpenRouter 빈 응답:")
                print(f"   - model: {self.model}")
                print(f"   - finish_reason: {finish_reason} ({reason_msg})")
                print(f"   - content type: {type(content).__name__}, repr: {repr(content)[:50]}")
                if usage:
                    print(f"   - 토큰: prompt={usage.get('prompt_tokens', '?')}, completion={usage.get('completion_tokens', '?')}")

                return {
                    "success": False,
                    "content": "",
                    "usage": usage,
                    "error": f"Empty content (finish_reason: {finish_reason}, {reason_msg})"
                }

            return {
                "success": True,
                "content": content,
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
