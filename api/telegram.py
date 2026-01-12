"""
Telegram Bot API Helper
"""

import requests
from .keys import get_telegram_config

class TelegramBot:
    """텔레그램 봇 클라이언트"""
    
    BASE_URL = "https://api.telegram.org/bot"
    
    def __init__(self):
        config = get_telegram_config()
        self.token = config["token"]
        self.chat_id = config["chat_id"]
        self.enabled = bool(self.token and self.chat_id)
    
    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """
        메시지 전송 (마크다운 실패 시 일반 텍스트로 재시도)
        """
        if not self.enabled:
            return False
        
        url = f"{self.BASE_URL}{self.token}/sendMessage"
        
        # 텍스트 길이 제한 (Telegram 4096자 제한)
        if len(text) > 3900:
            text = text[:3900] + "\n... (메시지 잘림)"
        
        # 마크다운 특수문자 이스케이프 (문제 방지)
        def escape_markdown(s: str) -> str:
            """마크다운 특수문자 이스케이프"""
            chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in chars:
                s = s.replace(char, '\\' + char)
            return s
        
        payload = {
            "chat_id": self.chat_id,
            "text": f"🤖 AIN: {text}",
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            # 마크다운 파싱 에러 시 일반 텍스트로 재시도
            if response.status_code != 200:
                # parse_mode 제거하고 재시도
                payload_plain = {
                    "chat_id": self.chat_id,
                    "text": f"🤖 AIN: {text}",
                    "disable_web_page_preview": True
                }
                response = requests.post(url, json=payload_plain, timeout=10)
            
            return response.status_code == 200
        except Exception as e:
            print(f"⚠️ 텔레그램 전송 실패: {e}")
            return False
    
    def get_updates(self, offset: int = 0, timeout: int = 10) -> list:
        """업데이트(메시지) 가져오기"""
        if not self.enabled:
            return []
        
        url = f"{self.BASE_URL}{self.token}/getUpdates"
        params = {"offset": offset + 1, "timeout": timeout}
        
        try:
            response = requests.get(url, params=params, timeout=timeout + 10)
            if response.status_code == 200:
                return response.json().get("result", [])
        except:
            pass
        return []
    
    def filter_my_messages(self, updates: list) -> list:
        """내 chat_id로 온 메시지만 필터링"""
        messages = []
        for update in updates:
            if "message" in update and "text" in update["message"]:
                if str(update["message"]["chat"]["id"]) == str(self.chat_id):
                    messages.append({
                        "update_id": update["update_id"],
                        "text": update["message"]["text"]
                    })
        return messages
