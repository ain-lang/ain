"""
AIN Core Engine - The Heart of AI-Native System
================================================
모듈화된 engine 패키지를 사용하여 AINCore를 제공합니다.

하위 호환성:
- from ain_engine import AINCore  # 기존 방식
- from engine import AINCore      # 새로운 방식
"""

# engine 패키지에서 모든 것을 re-export
from engine import AINCore, run_engine, DREAMER_MODEL, CODER_MODEL, DEFAULT_INTERVAL

__all__ = ['AINCore', 'run_engine', 'DREAMER_MODEL', 'CODER_MODEL', 'DEFAULT_INTERVAL']


if __name__ == "__main__":
    run_engine()
