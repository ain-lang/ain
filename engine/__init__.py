"""
AIN Engine Package
==================
AINCore를 모듈화하여 분리한 패키지

모듈 구조:
"""

from .core import AINCore as _AINCore, DREAMER_MODEL, CODER_MODEL, DEFAULT_INTERVAL
from .sync import SyncMixin
from .evolution import EvolutionMixin
from .handlers import HandlersMixin
from .introspect import IntrospectMixin
from .consciousness import ConsciousnessMixin
from .consolidation import MemoryConsolidator, get_consolidator
from .goal_manager import GoalManagerMixin
from .meta_cognition import MetaCognitionMixin
from .cognitive_auditor import CognitiveAuditorMixin
from .intuition import IntuitionMixin
from .temporal import TemporalAwarenessMixin
from .resource_monitor import ResourceAwarenessMixin
from .unified_consciousness import UnifiedConsciousnessMixin
from .reflex_learning_mixin import ReflexLearningMixin
from .creativity import CreativityMixin
from .loop import run_engine


class AINCore(
    _AINCore,
    SyncMixin,
    EvolutionMixin,
    HandlersMixin,
    IntrospectMixin,
    ConsciousnessMixin,
    GoalManagerMixin,
    MetaCognitionMixin,
    CognitiveAuditorMixin,
    IntuitionMixin,
    TemporalAwarenessMixin,
    ResourceAwarenessMixin,
    UnifiedConsciousnessMixin,
    ReflexLearningMixin,
    CreativityMixin
):
    """
    AIN의 핵심 엔진 클래스
    
    모든 기능적 Mixin을 상속받아 단일 인터페이스를 제공합니다.
    
    Inheritance Order:
    1. Core (State & Init)
    2. Functional Mixins (Sync, Evolution, Handlers...)
    3. Cognitive Mixins (Meta, Intuition, Temporal, Resource, Consciousness)
    4. Learning Mixins (ReflexLearning)
    5. Creative Mixins (Creativity) - Step 12
    
    Step 8 Integration:
      지식을 이양하는 학습 사이클을 실행할 수 있음
    
    Step 11 Integration:
      DecisionGate가 자원 상태에 따라 경로를 선택할 수 있음
    
    Step 12 Integration:
      CreativityMixin을 통해 brainstorm(), blend_concepts(), scamper() 메서드 사용 가능
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