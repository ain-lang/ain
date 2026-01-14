"""
AIN Engine Package
==================
AINCore를 모듈화하여 분리한 패키지

모듈 구조:
- core.py: 기본 초기화, 컴포넌트 관리
- sync.py: DB 동기화
- evolution.py: 진화 로직
- handlers.py: 명령어 처리
- introspect.py: 자기 성찰 (Legacy)
- consolidation.py: 기억 응고화 (Step 5)
- loop.py: 메인 루프
"""

from .core import AINCore as _AINCore, DREAMER_MODEL, CODER_MODEL, DEFAULT_INTERVAL
from .sync import SyncMixin
from .evolution import EvolutionMixin
from .handlers import HandlersMixin
from .introspect import IntrospectMixin
from .consciousness import ConsciousnessMixin
from .consolidation import MemoryConsolidator, get_consolidator
from .loop import run_engine


class AINCore(_AINCore, SyncMixin, EvolutionMixin, HandlersMixin, IntrospectMixin, ConsciousnessMixin):
    """
    AIN의 핵심 엔진 - 모든 믹스인을 통합한 완전한 클래스

    하위 호환성을 위해 기존 인터페이스 모두 유지
    """
    pass


__all__ = [
    'AINCore', 
    'run_engine', 
    'DREAMER_MODEL', 
    'CODER_MODEL', 
    'DEFAULT_INTERVAL',
    'MemoryConsolidator',
    'get_consolidator'
]
