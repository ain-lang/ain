"""
Engine Meta Learner: 메타인지 학습 및 보정 모듈
Step 7: Meta-Cognition - Recursive Self-Optimization Loop

이 모듈은 시스템의 예측(Confidence)과 실제 결과(Outcome)를 비교 분석하여,
메타인지 평가 모델(MetaEvaluator)의 정확도를 지속적으로 보정(Calibration)한다.
'Recursive Self-Optimization' 목표를 달성하기 위한 핵심 피드백 루프이다.

Architecture:
    Nexus (History)
        ↓ 진화 기록 (Metadata에 저장된 Confidence vs Status)
    MetaLearner (이 모듈)
        ↓ 분석 (Overconfidence/Underconfidence 감지)
    Calibration Factor (보정 계수)
        ↓
    FactCore (저장 및 공유)

Usage:
    from engine.meta_learner import MetaLearningMixin
    
    class AINCore(MetaLearningMixin, ...):
        pass
        
    ain = AINCore()
    calibration = await ain.run_meta_learning_cycle()
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import statistics

try:
    from nexus import Nexus
    HAS_NEXUS = True
except ImportError:
    HAS_NEXUS = False
    Nexus = None

try:
    from fact_core import FactCore
    HAS_FACT_CORE = True
except ImportError:
    HAS_FACT_CORE = False
    FactCore = None


@dataclass
class CalibrationResult:
    """메타인지 보정 결과"""
    bias_score: float        # >0: 과신(Overconfident), <0: 자신감 부족(Underconfident)
    calibration_factor: float # 보정 계수 (0.8 ~ 1.2)
    accuracy: float          # 예측 정확도
    sample_size: int         # 분석된 샘플 수
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "bias_score": self.bias_score,
            "calibration_factor": self.calibration_factor,
            "accuracy": self.accuracy,
            "sample_size": self.sample_size,
            "timestamp": self.timestamp.isoformat()
        }


class MetaLearner:
    """
    메타인지 학습기
    
    과거의 진화 기록을 분석하여 메타인지 시스템의 편향을 계산하고 보정한다.
    
    Attributes:
        nexus: Nexus 인스턴스 (기록 저장소)
        min_samples: 분석에 필요한 최소 샘플 수
        smoothing_factor: 보정 계수 변화 완화 비율 (급격한 변화 방지)
    """
    
    MIN_SAMPLES_DEFAULT = 5
    SMOOTHING_FACTOR_DEFAULT = 0.5
    CALIBRATION_FACTOR_MIN = 0.8
    CALIBRATION_FACTOR_MAX = 1.2
    
    def __init__(
        self, 
        nexus: Optional[Nexus] = None,
        min_samples: int = MIN_SAMPLES_DEFAULT,
        smoothing_factor: float = SMOOTHING_FACTOR_DEFAULT
    ):
        self.nexus = nexus
        self.min_samples = min_samples
        self.smoothing_factor = smoothing_factor
        self._last_calibration: Optional[CalibrationResult] = None
        
    def analyze_confidence_accuracy(self, limit: int = 20) -> CalibrationResult:
        """
        최근 기록을 분석하여 자신감 예측의 정확도를 측정한다.
        
        Args:
            limit: 분석할 최대 기록 수
            
        Returns:
            CalibrationResult: 보정 결과 (편향, 보정 계수, 정확도 등)
        """
        if self.nexus is None:
            return CalibrationResult(
                bias_score=0.0,
                calibration_factor=1.0,
                accuracy=0.0,
                sample_size=0
            )

        # Nexus에서 최근 진화 기록 조회
        history = self._get_history_with_confidence(limit)
        if not history:
            return CalibrationResult(
                bias_score=0.0,
                calibration_factor=1.0,
                accuracy=0.0,
                sample_size=0
            )

        predictions = []
        outcomes = []
        
        for record in history:
            confidence = record.get("confidence")
            status = record.get("status")
            
            if confidence is None or status is None:
                continue
            
            # 예측값 (0.0 ~ 1.0)
            predictions.append(float(confidence))
            
            # 실제 결과 (성공=1.0, 실패=0.0)
            if status == "success":
                outcomes.append(1.0)
            elif status == "failed":
                outcomes.append(0.0)
            else:
                # pending 등은 제외
                predictions.pop()
                continue
        
        if len(predictions) < self.min_samples:
            return CalibrationResult(
                bias_score=0.0,
                calibration_factor=1.0,
                accuracy=0.0,
                sample_size=len(predictions)
            )

        # 편향 계산 (예측 평균 - 실제 평균)
        avg_pred = statistics.mean(predictions)
        avg_actual = statistics.mean(outcomes)
        bias = avg_pred - avg_actual
        
        # 보정 계수 계산 (단순 역보정, 범위 제한)
        # 과신(bias > 0)하면 계수를 낮춤 (< 1.0)
        # 자신감 부족(bias < 0)하면 계수를 높임 (> 1.0)
        raw_factor = 1.0 - (bias * self.smoothing_factor)
        calibration_factor = max(
            self.CALIBRATION_FACTOR_MIN,
            min(self.CALIBRATION_FACTOR_MAX, raw_factor)
        )
        
        # 정확도 (MAE의 역수 개념)
        errors = [abs(p - o) for p, o in zip(predictions, outcomes)]
        accuracy = 1.0 - statistics.mean(errors)
        
        result = CalibrationResult(
            bias_score=bias,
            calibration_factor=calibration_factor,
            accuracy=accuracy,
            sample_size=len(predictions)
        )
        
        self._last_calibration = result
        return result
    
    def _get_history_with_confidence(self, limit: int) -> List[Dict[str, Any]]:
        """
        Nexus에서 confidence_score가 포함된 기록만 추출한다.
        
        Args:
            limit: 최대 기록 수
            
        Returns:
            confidence와 status가 포함된 기록 리스트
        """
        if self.nexus is None:
            return []
        
        try:
            # Nexus.get_recent_history() 호출
            raw_history = self.nexus.get_recent_history(limit=limit)
            if not raw_history:
                return []
            
            result = []
            for record in raw_history:
                # metadata에서 confidence_score 추출
                metadata = record.get("metadata", {})
                if isinstance(metadata, str):
                    # JSON 문자열인 경우 파싱 시도
                    try:
                        import json
                        metadata = json.loads(metadata)
                    except (json.JSONDecodeError, TypeError):
                        metadata = {}
                
                confidence = metadata.get("confidence_score")
                status = record.get("status")
                
                if confidence is not None and status is not None:
                    result.append({
                        "confidence": confidence,
                        "status": status,
                        "timestamp": record.get("timestamp"),
                        "file": record.get("file")
                    })
            
            return result
            
        except Exception as e:
            print(f"[MetaLearner] 기록 조회 실패: {e}")
            return []
    
    def get_last_calibration(self) -> Optional[CalibrationResult]:
        """마지막 보정 결과 반환"""
        return self._last_calibration
    
    def get_calibration_summary(self) -> str:
        """보정 상태 요약 문자열 반환"""
        if self._last_calibration is None:
            return "No calibration data available"
        
        cal = self._last_calibration
        bias_desc = "overconfident" if cal.bias_score > 0 else "underconfident"
        
        return (
            f"Calibration: factor={cal.calibration_factor:.3f}, "
            f"bias={cal.bias_score:.3f} ({bias_desc}), "
            f"accuracy={cal.accuracy:.2%}, "
            f"samples={cal.sample_size}"
        )


class MetaLearningMixin:
    """
    AINCore용 메타 학습 믹스인
    
    AINCore에 상속되어 메타인지 학습 기능을 제공한다.
    run_meta_learning_cycle()을 통해 주기적으로 메타인지 보정을 수행한다.
    
    Required attributes from AINCore:
    """
    
    _meta_learner: Optional[MetaLearner] = None
    
    def _get_meta_learner(self) -> MetaLearner:
        """MetaLearner 인스턴스를 lazy-load로 가져온다."""
        if self._meta_learner is None:
            nexus = getattr(self, "nexus", None)
            self._meta_learner = MetaLearner(nexus=nexus)
        return self._meta_learner
        
    async def run_meta_learning_cycle(self) -> Dict[str, Any]:
        """
        메타 학습 사이클 실행
        
        과거 기록을 분석하여 메타인지 보정 계수를 계산하고,
        결과를 FactCore에 저장하여 MetaEvaluator가 참조할 수 있게 한다.
        
        Returns:
            보정 결과 딕셔너리
        """
        learner = self._get_meta_learner()
        result = learner.analyze_confidence_accuracy()
        
        # 결과를 FactCore에 저장 (Identity의 일부로 통합)
        fact_core = getattr(self, "fact_core", None)
        if fact_core is not None and result.sample_size > 0:
            calibration_data = {
                "factor": result.calibration_factor,
                "bias": result.bias_score,
                "accuracy": result.accuracy,
                "sample_size": result.sample_size,
                "last_updated": result.timestamp.isoformat()
            }
            
            try:
                # 'meta_calibration' 노드 업데이트 (없으면 생성됨)
                fact_core.add_fact("meta_calibration", calibration_data)
                
                bias_direction = "overconfident" if result.bias_score > 0 else "underconfident"
                print(
                    f"🧠 Meta-Learning: Calibration Factor updated to "
                    f"{result.calibration_factor:.3f} "
                    f"(Bias: {result.bias_score:.3f}, {bias_direction})"
                )
            except Exception as e:
                print(f"[MetaLearning] FactCore 저장 실패: {e}")
        elif result.sample_size == 0:
            print("🧠 Meta-Learning: 분석할 샘플이 부족합니다.")
            
        return {
            "calibration_factor": result.calibration_factor,
            "bias_score": result.bias_score,
            "accuracy": result.accuracy,
            "sample_size": result.sample_size,
            "summary": learner.get_calibration_summary()
        }
    
    def get_current_calibration_factor(self) -> float:
        """
        현재 보정 계수를 반환한다.
        
        FactCore에 저장된 값을 우선 사용하고, 없으면 기본값(1.0)을 반환한다.
        
        Returns:
            보정 계수 (0.8 ~ 1.2)
        """
        fact_core = getattr(self, "fact_core", None)
        if fact_core is not None:
            try:
                calibration_data = fact_core.get_fact("meta_calibration", default={})
                if isinstance(calibration_data, dict):
                    return calibration_data.get("factor", 1.0)
            except Exception:
                pass
        
        return 1.0
    
    def apply_calibration_to_confidence(self, raw_confidence: float) -> float:
        """
        원시 자신감 점수에 보정 계수를 적용한다.
        
        MetaEvaluator가 산출한 자신감 점수를 보정하여
        과신/자신감 부족 편향을 완화한다.
        
        Args:
            raw_confidence: 원시 자신감 점수 (0.0 ~ 1.0)
            
        Returns:
            보정된 자신감 점수 (0.0 ~ 1.0 범위로 클램핑)
        """
        factor = self.get_current_calibration_factor()
        
        # 보정 적용: 과신(factor < 1.0)이면 점수를 낮추고,
        # 자신감 부족(factor > 1.0)이면 점수를 높임
        calibrated = raw_confidence * factor
        
        # 범위 클램핑 (0.0 ~ 1.0)
        return max(0.0, min(1.0, calibrated))