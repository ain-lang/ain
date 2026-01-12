"""
AIN Corpus Callosum Package
===========================
좌뇌(Fact Core)와 우뇌(Nexus) 사이의 정보 교환을 담당하는 브릿지

모듈 구조:
- core.py: 기본 초기화, 연결 관리
- hydration.py: 부팅 시 DB에서 기억 복원
- sync.py: 주기적 상태 동기화
- transform.py: Arrow 변환, Context Synthesis
"""

from .core import CorpusCallosumCore
from .hydration import HydrationMixin
from .sync import SyncMixin
from .transform import TransformMixin


class CorpusCallosum(CorpusCallosumCore, HydrationMixin, SyncMixin, TransformMixin):
    """
    AIN의 뇌량 (Corpus Callosum) - 모든 믹스인을 통합한 완전한 클래스
    
    하위 호환성을 위해 기존 인터페이스 모두 유지
    """
    pass


__all__ = ['CorpusCallosum']
