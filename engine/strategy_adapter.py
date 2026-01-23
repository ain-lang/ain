"""
Engine Strategy Adapter: 전략 조정 모듈
Step 7: Meta-Cognition - Strategy Adjustment

이 모듈은 메타인지 평가 결과(효율성, 에러율, 복잡도 등)를 입력받아
시스템이 취해야 할 최적의 운영 모드(Strategy Mode)와 파라미터를 결정한다.

MetaCognitionMixin이나 MetaEvaluator 같은 대형 파일을 직접 수정하지 않고,
전략 판단 로직만 전담하는 소형 모듈로 설계되었다.

Architecture:
    MetaEvaluator (평가 수행)
        ↓ efficacy_score, error_count, complexity
    StrategyAdapter (이 모듈)
        ↓ StrategyMode, tuning_params
    AINCore (파라미터 적용)

Usage:
    from engine.strategy_adapter import StrategyAdapter, StrategyMode
    
    adapter = StrategyAdapter()
    mode = adapter.evaluate_mode(efficacy_score=0.85, error_count=1, complexity="medium")
    params = adapter.get_tuning_params(mode)
"""

from enum import Enum
from typing import Dict, Any


class StrategyMode(Enum):
    """
    시스템 운영 모드 열거형
    
    각 모드는 시스템의 현재 상태에 따라 자동으로 선택되며,
    진화 주기, 모델 파라미터, 검증 강도 등에 영향을 미친다.
    """
    NORMAL = "normal"
    # 기본 상태: 균형 잡힌 접근
    # - 표준 진화 주기
    # - 기본 temperature
    # - 일반적인 검증 수준
    
    ACCELERATED = "accelerated"
    # 높은 성공률, 자신감 상승 상태
    # - 진화 주기 단축 (더 빠른 시도)
    # - 약간 높은 temperature (과감한 시도)
    # - 검증 간소화
    
    CAUTIOUS = "cautious"
    # 잦은 에러, 낮은 효율성 상태
    # - 진화 주기 연장 (신중한 접근)
    # - 낮은 temperature (보수적 생성)
    # - 검증 강화
    
    DEEP_REFLECTION = "deep_reflection"
    # 복잡한 문제 직면 상태
    # - 진화 주기 대폭 연장
    # - 매우 낮은 temperature (정밀한 추론)
    # - 독백 빈도 증가
    # - 다단계 검증


class StrategyAdapter:
    """
    전략 조정기
    
    메타인지 평가 결과를 바탕으로 시스템의 운영 전략을 결정한다.
    이 클래스는 상태를 갖지 않는 순수 함수형 설계를 따른다.
    
    평가 기준:
    """
    
    # 임계값 설정
    HIGH_EFFICACY_THRESHOLD = 0.75
    LOW_EFFICACY_THRESHOLD = 0.4
    HIGH_ERROR_THRESHOLD = 3
    
    # 모드별 튜닝 파라미터 정의
    _TUNING_PARAMS: Dict[StrategyMode, Dict[str, Any]] = {
        StrategyMode.NORMAL: {
            "interval_multiplier": 1.0,
            "temperature": 0.7,
            "burst_limit": 5,
            "validation_level": "standard",
            "monologue_interval": 3600,
            "description": "균형 잡힌 기본 모드"
        },
        StrategyMode.ACCELERATED: {
            "interval_multiplier": 0.5,
            "temperature": 0.8,
            "burst_limit": 10,
            "validation_level": "light",
            "monologue_interval": 3600,
            "description": "높은 자신감, 빠른 진화 모드"
        },
        StrategyMode.CAUTIOUS: {
            "interval_multiplier": 2.0,
            "temperature": 0.5,
            "burst_limit": 2,
            "validation_level": "strict",
            "monologue_interval": 2400,
            "description": "신중한 접근, 검증 강화 모드"
        },
        StrategyMode.DEEP_REFLECTION: {
            "interval_multiplier": 3.0,
            "temperature": 0.3,
            "burst_limit": 1,
            "validation_level": "multi_stage",
            "monologue_interval": 1200,
            "description": "깊은 성찰, 복잡한 문제 해결 모드"
        }
    }
    
    def evaluate_mode(
        self,
        efficacy_score: float,
        error_count: int = 0,
        complexity: str = "medium"
    ) -> StrategyMode:
        """
        평가 지표를 바탕으로 최적의 전략 모드를 결정한다.
        
        Args:
            efficacy_score: 자기 효율성 점수 (0.0 ~ 1.0)
            error_count: 최근 에러 발생 횟수
            complexity: 작업 복잡도 ("low", "medium", "high")
        
        Returns:
            결정된 StrategyMode
        
        Decision Logic:
            1. 복잡도가 high이면 → DEEP_REFLECTION
            2. 에러가 많으면 → CAUTIOUS
            3. 효율성이 높으면 → ACCELERATED
            4. 효율성이 낮으면 → CAUTIOUS
            5. 그 외 → NORMAL
        """
        # 입력값 정규화
        efficacy_score = max(0.0, min(1.0, efficacy_score))
        complexity = complexity.lower() if isinstance(complexity, str) else "medium"
        
        # 1. 복잡도 기반 판단 (최우선)
        if complexity == "high":
            return StrategyMode.DEEP_REFLECTION
        
        # 2. 에러 기반 판단
        if error_count >= self.HIGH_ERROR_THRESHOLD:
            return StrategyMode.CAUTIOUS
        
        # 3. 효율성 기반 판단
        if efficacy_score >= self.HIGH_EFFICACY_THRESHOLD:
            # 높은 효율성 + 낮은 에러 → 가속
            if error_count <= 1:
                return StrategyMode.ACCELERATED
            else:
                return StrategyMode.NORMAL
        
        if efficacy_score <= self.LOW_EFFICACY_THRESHOLD:
            return StrategyMode.CAUTIOUS
        
        # 4. 기본값
        return StrategyMode.NORMAL
    
    def get_tuning_params(self, mode: StrategyMode) -> Dict[str, Any]:
        """
        모드에 따른 시스템 튜닝 파라미터를 반환한다.
        
        Args:
            mode: 전략 모드
        
        Returns:
            튜닝 파라미터 딕셔너리:
        """
        if mode not in self._TUNING_PARAMS:
            return self._TUNING_PARAMS[StrategyMode.NORMAL]
        
        return self._TUNING_PARAMS[mode].copy()
    
    def get_mode_description(self, mode: StrategyMode) -> str:
        """모드에 대한 설명을 반환한다."""
        params = self.get_tuning_params(mode)
        return params.get("description", "알 수 없는 모드")
    
    def suggest_action(
        self,
        efficacy_score: float,
        error_count: int = 0,
        complexity: str = "medium"
    ) -> Dict[str, Any]:
        """
        현재 상태를 분석하여 권장 행동을 제안한다.
        
        Args:
            efficacy_score: 자기 효율성 점수
            error_count: 최근 에러 횟수
            complexity: 작업 복잡도
        
        Returns:
            권장 행동 딕셔너리:
        """
        mode = self.evaluate_mode(efficacy_score, error_count, complexity)
        params = self.get_tuning_params(mode)
        
        # 결정 근거 생성
        reasoning_parts = []
        if complexity == "high":
            reasoning_parts.append("복잡한 작업 감지")
        if error_count >= self.HIGH_ERROR_THRESHOLD:
            reasoning_parts.append(f"에러 {error_count}회 발생")
        if efficacy_score >= self.HIGH_EFFICACY_THRESHOLD:
            reasoning_parts.append(f"높은 효율성({efficacy_score:.2f})")
        elif efficacy_score <= self.LOW_EFFICACY_THRESHOLD:
            reasoning_parts.append(f"낮은 효율성({efficacy_score:.2f})")
        
        reasoning = " + ".join(reasoning_parts) if reasoning_parts else "일반 상태"
        
        # 구체적 권장 행동 생성
        actions = self._generate_actions(mode, efficacy_score, error_count)
        
        return {
            "mode": mode,
            "mode_name": mode.value,
            "params": params,
            "reasoning": reasoning,
            "actions": actions
        }
    
    def _generate_actions(
        self,
        mode: StrategyMode,
        efficacy_score: float,
        error_count: int
    ) -> list:
        """모드에 따른 구체적 행동 목록 생성"""
        actions = []
        
        if mode == StrategyMode.ACCELERATED:
            actions.append("진화 주기를 단축하여 빠른 반복을 시도하라")
            actions.append("새로운 기능 구현에 과감하게 도전하라")
        
        elif mode == StrategyMode.CAUTIOUS:
            actions.append("진화 전 충분한 검토를 수행하라")
            if error_count > 0:
                actions.append(f"최근 {error_count}회 에러의 패턴을 분석하라")
            actions.append("작은 단위로 나누어 점진적으로 진화하라")
        
        elif mode == StrategyMode.DEEP_REFLECTION:
            actions.append("문제를 여러 하위 문제로 분해하라")
            actions.append("각 단계에서 중간 결과를 검증하라")
            actions.append("독백을 통해 사고 과정을 명확히 하라")
        
        else:  # NORMAL
            actions.append("현재 로드맵 목표에 집중하라")
            actions.append("균형 잡힌 속도로 진화를 진행하라")
        
        return actions


def get_strategy_adapter() -> StrategyAdapter:
    """StrategyAdapter 인스턴스를 반환한다."""
    return StrategyAdapter()