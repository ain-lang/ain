"""
API Keys 중앙 관리
⚠️ 모든 키는 환경변수에서 로드 (프로덕션 안전)
"""

import os

# === API Keys ===

def get_openrouter_key() -> str:
    """OpenRouter API Key"""
    return os.getenv("OPENROUTER_API_KEY", "")

def get_github_token() -> str:
    """GitHub Personal Access Token"""
    return os.getenv("GITHUB_TOKEN", "")

def get_telegram_config() -> dict:
    """Telegram Bot 설정"""
    return {
        "token": os.getenv("TELEGRAM_TOKEN", ""),
        "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
    }

# === Config Values ===

def get_config() -> dict:
    """시스템 설정값"""
    return {
        "dreamer_model": "google/gemini-3-pro-preview", # [CRITICAL] DO NOT DOWNGRADE
        "coder_model": "anthropic/claude-opus-4.5",       # [CRITICAL] DO NOT DOWNGRADE
        "opus_45_model": "anthropic/claude-opus-4.5", 
        "repo_name": os.getenv("REPO_NAME", ""),
                "evolution_interval": 3600,  # 1시간으로 절대 고정 (환경변수 무시)
        "redis_url": os.getenv("REDIS_URL", ""),
    }

# === Validation ===

def validate_required_keys() -> tuple[bool, list[str]]:
    """필수 환경변수 검증"""
    required = ["OPENROUTER_API_KEY", "GITHUB_TOKEN", "TELEGRAM_TOKEN", "REPO_NAME"]
    missing = [key for key in required if not os.getenv(key)]
    return len(missing) == 0, missing
