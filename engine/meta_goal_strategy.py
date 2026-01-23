"""
Engine Meta Goal Strategy: 메타인지 기반 목표 전략 수립
Step 7 & 6: Meta-Cognition to Intentionality Bridge

이 모듈은 시스템의 인지 상태(CognitiveState)와 전략 모드(StrategyMode)를 분석하여,
현재 상황에 가장 적합한 '메타 목표(Meta-Goals)'를 제안한다.

MetaMonitor가 '상태'를 진단하고 StrategyAdapter가 '모드'를 결정하면,
이 모듈은 이를 구체적인 '행동 목표'로 변환하여 IntentionCore에 주입할 준비를 한다.

Architecture:
    MetaMonitor (CognitiveState)
        ↓
    MetaGoalStrategy (이 모듈)
        ↓
    List[GoalDict] (제안된 목표)
        ↓
    GoalManager / IntentionCore

Usage:
    from engine.meta_goal_strategy import suggest_meta_goals, MetaGoalStrategy
    
    goals = suggest_meta_goals(cognitive_state, strategy_mode)
    for g in goals:
        intention_core.add_goal(g["content"], g["priority"])
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


# 의존성 임포트 (가용성 체크)
try:
    from engine.meta_monitor import CognitiveState, CognitiveHealthLevel
    HAS_MONITOR = True
except ImportError:
    HAS_MONITOR = False
    CognitiveState = None
    CognitiveHealthLevel = None

try:
    from engine.strategy_adapter import StrategyMode
    HAS_STRATEGY = True
except ImportError:
    HAS_STRATEGY = False
    StrategyMode = None


class GoalCategory(Enum):
    """목표 카테고리 열거형"""
    SELF_HEALING = "self_healing"
    OPTIMIZATION = "optimization"
    EXPLORATION = "exploration"
    CONSOLIDATION = "consolidation"
    RECOVERY = "recovery"


@dataclass
class MetaGoal:
    """
    메타 목표 데이터 구조
    
    Attributes:
        content: 목표 내용 (무엇을 달성할 것인가)
        priority: 우선순위 (1-10, 높을수록 중요)
        category: 목표 카테고리
        rationale: 이 목표를 제안한 이유
        deadline_hours: 목표 달성 예상 시간 (시간 단위, 선택)
    """
    content: str
    priority: int
    category: GoalCategory
    rationale: str
    deadline_hours: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """IntentionCore 호환 딕셔너리로 변환"""
        result = {
            "content": self.content,
            "priority": self.priority,
            "metadata": {
                "category": self.category.value,
                "rationale": self.rationale,
                "source": "meta_goal_strategy",
                "generated_at": datetime.now().isoformat()
            }
        }
        if self.deadline_hours is not None:
            result["metadata"]["deadline_hours"] = self.deadline_hours
        return result


class MetaGoalStrategy:
    """
    메타인지 기반 목표 전략 수립기
    
    인지 상태와 전략 모드를 분석하여 적절한 목표를 제안한다.
    시스템의 자기 치유(Self-Healing) 및 적응 전략(Adaptive Strategy)을 구현한다.
    """
    
    def __init__(self):
        self._goal_templates = self._initialize_goal_templates()
    
    def _initialize_goal_templates(self) -> Dict[str, List[Dict[str, Any]]]:
        """상황별 목표 템플릿 초기화"""
        return {
            "critical_recovery": [
                {
                    "content": "시스템 안정성 복구를 위한 긴급 진단 및 롤백 검토",
                    "priority": 10,
                    "category": GoalCategory.RECOVERY,
                    "rationale": "인지 건강 수준이 위험 상태이므로 즉각적인 복구 필요",
                    "deadline_hours": 1
                },
                {
                    "content": "최근 실패한 진화의 원인 분석 및 에러 패턴 기록",
                    "priority": 9,
                    "category": GoalCategory.SELF_HEALING,
                    "rationale": "반복적인 실패를 방지하기 위한 학습",
                    "deadline_hours": 2
                }
            ],
            "degraded_healing": [
                {
                    "content": "자신감 점수 향상을 위한 소규모 성공 가능한 진화 수행",
                    "priority": 8,
                    "category": GoalCategory.SELF_HEALING,
                    "rationale": "연속 실패로 인한 자신감 저하 회복",
                    "deadline_hours": 4
                },
                {
                    "content": "복잡도가 낮은 파일에 대한 리팩토링 또는 문서화",
                    "priority": 7,
                    "category": GoalCategory.CONSOLIDATION,
                    "rationale": "안정적인 성공 경험 축적",
                    "deadline_hours": 6
                }
            ],
            "moderate_optimization": [
                {
                    "content": "현재 로드맵 단계의 핵심 기능 구현 진행",
                    "priority": 8,
                    "category": GoalCategory.EXPLORATION,
                    "rationale": "시스템이 안정적이므로 진화에 집중",
                    "deadline_hours": 8
                },
                {
                    "content": "기존 모듈의 테스트 커버리지 확장",
                    "priority": 6,
                    "category": GoalCategory.CONSOLIDATION,
                    "rationale": "안정성 유지를 위한 검증 강화",
                    "deadline_hours": 12
                }
            ],
            "optimal_exploration": [
                {
                    "content": "다음 로드맵 단계를 위한 아키텍처 설계 탐색",
                    "priority": 7,
                    "category": GoalCategory.EXPLORATION,
                    "rationale": "최적의 인지 상태에서 미래 지향적 탐색",
                    "deadline_hours": 24
                },
                {
                    "content": "새로운 기능 프로토타입 실험",
                    "priority": 6,
                    "category": GoalCategory.EXPLORATION,
                    "rationale": "여유 있는 상태에서 창의적 시도",
                    "deadline_hours": 12
                },
                {
                    "content": "학습된 패턴을 반사 행동으로 이관",
                    "priority": 5,
                    "category": GoalCategory.OPTIMIZATION,
                    "rationale": "System 2에서 System 1으로 지식 전이",
                    "deadline_hours": 8
                }
            ],
            "accelerated_momentum": [
                {
                    "content": "현재 진화 모멘텀을 유지하며 연속 성공 달성",
                    "priority": 9,
                    "category": GoalCategory.OPTIMIZATION,
                    "rationale": "가속 모드에서 최대 효율 추구",
                    "deadline_hours": 4
                },
                {
                    "content": "버스트 모드 종료 전 핵심 기능 완성",
                    "priority": 8,
                    "category": GoalCategory.EXPLORATION,
                    "rationale": "시간 제한 내 목표 달성",
                    "deadline_hours": 2
                }
            ],
            "conservative_stabilization": [
                {
                    "content": "최소한의 변경으로 시스템 안정성 확보",
                    "priority": 9,
                    "category": GoalCategory.CONSOLIDATION,
                    "rationale": "보수적 모드에서 위험 최소화",
                    "deadline_hours": 6
                },
                {
                    "content": "기존 코드의 문서화 및 주석 보강",
                    "priority": 6,
                    "category": GoalCategory.CONSOLIDATION,
                    "rationale": "안전한 작업으로 기여",
                    "deadline_hours": 12
                }
            ]
        }
    
    def analyze_situation(
        self,
        state: Optional[Any],
        mode: Optional[Any]
    ) -> str:
        """
        인지 상태와 전략 모드를 분석하여 상황 키를 반환한다.
        
        Args:
            state: CognitiveState 인스턴스 (또는 None)
            mode: StrategyMode 인스턴스 (또는 None)
        
        Returns:
            상황 키 (goal_templates의 키와 매칭)
        """
        health_level = "moderate"
        strategy_mode = "normal"
        
        if state is not None and HAS_MONITOR:
            if hasattr(state, "health_level"):
                health_value = state.health_level
                if hasattr(health_value, "value"):
                    health_level = health_value.value
                elif isinstance(health_value, str):
                    health_level = health_value
        
        if mode is not None and HAS_STRATEGY:
            if hasattr(mode, "value"):
                strategy_mode = mode.value
            elif isinstance(mode, str):
                strategy_mode = mode
        
        if health_level == "critical":
            return "critical_recovery"
        elif health_level == "degraded":
            return "degraded_healing"
        elif strategy_mode == "accelerated":
            return "accelerated_momentum"
        elif strategy_mode == "conservative":
            return "conservative_stabilization"
        elif health_level == "optimal":
            return "optimal_exploration"
        else:
            return "moderate_optimization"
    
    def suggest_goals(
        self,
        state: Optional[Any] = None,
        mode: Optional[Any] = None,
        max_goals: int = 3
    ) -> List[MetaGoal]:
        """
        현재 인지 상태와 전략 모드에 기반하여 메타 목표를 제안한다.
        
        Args:
            state: CognitiveState 인스턴스 (선택)
            mode: StrategyMode 인스턴스 (선택)
            max_goals: 반환할 최대 목표 수
        
        Returns:
            MetaGoal 인스턴스 리스트
        """
        situation_key = self.analyze_situation(state, mode)
        templates = self._goal_templates.get(situation_key, [])
        
        goals = []
        for template in templates[:max_goals]:
            goal = MetaGoal(
                content=template["content"],
                priority=template["priority"],
                category=template["category"],
                rationale=template["rationale"],
                deadline_hours=template.get("deadline_hours")
            )
            goals.append(goal)
        
        return goals
    
    def suggest_goals_as_dicts(
        self,
        state: Optional[Any] = None,
        mode: Optional[Any] = None,
        max_goals: int = 3
    ) -> List[Dict[str, Any]]:
        """
        IntentionCore 호환 딕셔너리 형태로 목표를 반환한다.
        
        Args:
            state: CognitiveState 인스턴스 (선택)
            mode: StrategyMode 인스턴스 (선택)
            max_goals: 반환할 최대 목표 수
        
        Returns:
            목표 딕셔너리 리스트
        """
        goals = self.suggest_goals(state, mode, max_goals)
        return [g.to_dict() for g in goals]
    
    def get_adaptive_goal(
        self,
        state: Optional[Any] = None,
        mode: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[MetaGoal]:
        """
        컨텍스트를 고려하여 가장 적합한 단일 목표를 반환한다.
        
        Args:
            state: CognitiveState 인스턴스 (선택)
            mode: StrategyMode 인스턴스 (선택)
            context: 추가 컨텍스트 정보 (선택)
        
        Returns:
            가장 우선순위가 높은 MetaGoal 또는 None
        """
        goals = self.suggest_goals(state, mode, max_goals=1)
        if goals:
            return goals[0]
        return None


# 모듈 레벨 싱글톤 인스턴스
_strategy_instance: Optional[MetaGoalStrategy] = None


def get_meta_goal_strategy() -> MetaGoalStrategy:
    """MetaGoalStrategy 싱글톤 인스턴스 반환"""
    global _strategy_instance
    if _strategy_instance is None:
        _strategy_instance = MetaGoalStrategy()
    return _strategy_instance


def suggest_meta_goals(
    state: Optional[Any] = None,
    mode: Optional[Any] = None,
    max_goals: int = 3
) -> List[Dict[str, Any]]:
    """
    현재 인지 상태와 전략 모드에 기반하여 메타 목표를 제안한다.
    
    이 함수는 모듈의 주요 진입점이며, IntentionCore와 호환되는
    딕셔너리 형태로 목표를 반환한다.
    
    Args:
        state: CognitiveState 인스턴스 (선택)
        mode: StrategyMode 인스턴스 (선택)
        max_goals: 반환할 최대 목표 수
    
    Returns:
        목표 딕셔너리 리스트
        각 딕셔너리는 다음 키를 포함:
    
    Example:
        >>> goals = suggest_meta_goals(cognitive_state, strategy_mode)
        >>> for g in goals:
        ...     intention_core.add_goal(g["content"], g["priority"])
    """
    strategy = get_meta_goal_strategy()
    return strategy.suggest_goals_as_dicts(state, mode, max_goals)


def get_recovery_goals() -> List[Dict[str, Any]]:
    """
    긴급 복구 목표를 반환한다.
    
    시스템이 위험 상태일 때 즉시 호출할 수 있는 헬퍼 함수.
    
    Returns:
        복구 관련 목표 딕셔너리 리스트
    """
    strategy = get_meta_goal_strategy()
    templates = strategy._goal_templates.get("critical_recovery", [])
    
    goals = []
    for template in templates:
        goals.append({
            "content": template["content"],
            "priority": template["priority"],
            "metadata": {
                "category": template["category"].value,
                "rationale": template["rationale"],
                "source": "meta_goal_strategy_recovery",
                "generated_at": datetime.now().isoformat()
            }
        })
    return goals


def get_exploration_goals() -> List[Dict[str, Any]]:
    """
    탐색 목표를 반환한다.
    
    시스템이 최적 상태일 때 미래 지향적 탐색을 위한 목표.
    
    Returns:
        탐색 관련 목표 딕셔너리 리스트
    """
    strategy = get_meta_goal_strategy()
    templates = strategy._goal_templates.get("optimal_exploration", [])
    
    goals = []
    for template in templates:
        goals.append({
            "content": template["content"],
            "priority": template["priority"],
            "metadata": {
                "category": template["category"].value,
                "rationale": template["rationale"],
                "source": "meta_goal_strategy_exploration",
                "generated_at": datetime.now().isoformat()
            }
        })
    return goals