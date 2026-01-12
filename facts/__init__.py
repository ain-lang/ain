"""
AIN Facts Package
=================
시스템의 절대적 진리, 규칙, 로드맵 및 자아 정체성을 관리

모듈 구조:
- node.py: KnowledgeNode 클래스
- core.py: 기본 클래스 및 데이터 정의
- storage.py: 저장/로드 로직
- graph.py: 그래프 빌드 및 뷰
- snapshot.py: 시스템 스냅샷 생성
"""

from .node import KnowledgeNode
from .core import FactCoreBase
from .storage import StorageMixin
from .graph import GraphMixin
from .snapshot import SnapshotMixin


class FactCore(FactCoreBase, StorageMixin, GraphMixin, SnapshotMixin):
    """
    AIN의 Fact Core - 모든 믹스인을 통합한 완전한 클래스
    
    하위 호환성을 위해 기존 인터페이스 모두 유지
    """
    pass


__all__ = ['FactCore', 'KnowledgeNode']
