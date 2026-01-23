"""
AIN의 Fact Core (Symbolic Graph):
시스템의 절대적 진리, 규칙, 로드맵 및 자아 정체성을 관리한다.

모듈화된 facts 패키지를 사용합니다.

하위 호환성:
- from fact_core import FactCore, KnowledgeNode  # 기존 방식
- from facts import FactCore, KnowledgeNode      # 새로운 방식
"""

# facts 패키지에서 re-export
from facts import FactCore, KnowledgeNode

__all__ = ['FactCore', 'KnowledgeNode']
