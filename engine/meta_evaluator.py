"""
Engine Meta Evaluator: 자기 효율성 평가 모듈
Step 7: Meta-Cognition - Self-Efficacy Evaluation

이 모듈은 AIN이 자신의 현재 상태, 최근 성과, 기억의 명확성을 바탕으로
'자신감(Confidence)'과 '효율성(Efficacy)'을 수치적으로 평가하는 로직을 담고 있다.
대형 파일인 meta_cognition.py의 부담을 줄이기 위해 분리되었다.

Architecture:
    MetaCognitionMixin (engine/meta_cognition.py)
        ↓ 호출
    MetaEvaluator (이 모듈)
        ↓ 분석
    confidence_score, status, reasoning 반환

Usage:
    from engine.meta_evaluator import MetaEvaluator
    
    evaluator = MetaEvaluator()
    result = evaluator.evaluate_efficacy(recent_history, relevant_memories)
    strategy = evaluator.suggest_strategy(result["confidence_score"])
"""

from typing import List, Dict, Any, Optional


class MetaEvaluator:
    """
    메타 인지 평가자
    
    입력된 컨텍스트를 기반으로 현재 작업의 성공 확률(Confidence)을 예측한다.
    이 클래스는 MetaCognitionMixin에서 호출되어 자기 효율성 평가를 수행한다.
    
    평가 기준:
    1. 최근 성공 모멘텀 (Recent Success Momentum)
    2. 기억 연관성 (Memory Relevance)
    3. 복잡도 페널티 (Complexity Penalty)
    """

    # 대형 파일 임계값 (줄 수)
    LARGE_FILE_THRESHOLD = 200
    
    # 보호된 파일 목록
    PROTECTED_FILES = frozenset([
        "main.py", "api/keys.py", "api/github.py", 
        ".ainprotect", "overseer.py"
    ])

    def evaluate_efficacy(
        self, 
        recent_history: List[Dict[str, Any]], 
        relevant_memories: List[Dict[str, Any]],
        target_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        자기 효율성 평가 수행
        
        Args:
            recent_history: 최근 진화 기록 리스트 (최대 5개 권장)
            relevant_memories: 현재 상황과 연관된 벡터 기억 리스트
            target_file: 수정 대상 파일 (복잡도 평가용, 선택)
            
        Returns:
            {
                "confidence_score": float (0.0 ~ 1.0),
                "status": str (high_efficacy, uncertain, low_efficacy),
                "reasoning": str,
                "factors": dict (세부 평가 요소)
            }
        """
        score = 0.5  # 기본 점수 (중립)
        reasons = []
        factors = {
            "success_momentum": 0.0,
            "memory_relevance": 0.0,
            "complexity_penalty": 0.0
        }

        # 1. 최근 성공 모멘텀 평가
        momentum_score, momentum_reason = self._evaluate_success_momentum(recent_history)
        score += momentum_score
        factors["success_momentum"] = momentum_score
        reasons.append(momentum_reason)

        # 2. 기억 연관성 평가 (경험 유무)
        memory_score, memory_reason = self._evaluate_memory_relevance(relevant_memories)
        score += memory_score
        factors["memory_relevance"] = memory_score
        reasons.append(memory_reason)

        # 3. 복잡도 페널티 (대상 파일이 있는 경우)
        if target_file:
            penalty_score, penalty_reason = self._evaluate_complexity_penalty(target_file)
            score += penalty_score
            factors["complexity_penalty"] = penalty_score
            reasons.append(penalty_reason)

        # 4. 점수 클램핑 (0.1 ~ 1.0 범위)
        score = max(0.1, min(1.0, score))
        
        # 5. 상태 결정
        status = self._determine_status(score)

        return {
            "confidence_score": round(score, 2),
            "status": status,
            "reasoning": " | ".join(reasons),
            "factors": factors
        }

    def _evaluate_success_momentum(
        self, 
        recent_history: List[Dict[str, Any]]
    ) -> tuple:
        """최근 진화 성공률 기반 모멘텀 평가"""
        if not recent_history:
            return 0.0, "최근 기록 없음(중립)"
        
        recent_count = len(recent_history)
        success_count = sum(
            1 for h in recent_history 
            if h.get("status") == "success"
        )
        success_rate = success_count / recent_count
        
        if success_rate >= 0.8:
            return 0.2, f"높은 성공률({success_rate:.0%}, {success_count}/{recent_count})"
        elif success_rate >= 0.6:
            return 0.1, f"양호한 성공률({success_rate:.0%})"
        elif success_rate >= 0.4:
            return 0.0, f"보통 성공률({success_rate:.0%})"
        else:
            return -0.2, f"낮은 성공률({success_rate:.0%}) - 주의 필요"

    def _evaluate_memory_relevance(
        self, 
        relevant_memories: List[Dict[str, Any]]
    ) -> tuple:
        """유사 기억 존재 여부 평가"""
        if not relevant_memories:
            return -0.1, "유사한 과거 경험 부재(불확실성)"
        
        memory_count = len(relevant_memories)
        
        # 거리(distance) 기반 품질 평가 (낮을수록 유사)
        high_quality_count = sum(
            1 for m in relevant_memories 
            if m.get("distance", 1.0) < 0.5
        )
        
        if high_quality_count >= 2:
            return 0.2, f"고품질 유사 경험 {high_quality_count}건 존재"
        elif memory_count >= 3:
            return 0.15, f"유사 경험 {memory_count}건 존재"
        elif memory_count >= 1:
            return 0.1, f"관련 경험 {memory_count}건 존재"
        else:
            return 0.0, "관련 경험 미미"

    def _evaluate_complexity_penalty(self, target_file: str) -> tuple:
        """대상 파일의 복잡도에 따른 페널티 평가"""
        import os
        
        # 보호된 파일 체크
        normalized = target_file.lstrip("./").replace("\\", "/")
        basename = os.path.basename(normalized)
        
        if normalized in self.PROTECTED_FILES or basename in self.PROTECTED_FILES:
            return -0.3, f"보호된 파일({basename}) - 수정 위험"
        
        # 파일 크기 체크
        if os.path.exists(target_file):
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    line_count = sum(1 for _ in f)
                
                if line_count > self.LARGE_FILE_THRESHOLD:
                    return -0.15, f"대형 파일({line_count}줄) - 컨텍스트 제한 주의"
                elif line_count > 100:
                    return -0.05, f"중간 크기 파일({line_count}줄)"
                else:
                    return 0.05, f"소형 파일({line_count}줄) - 수정 용이"
            except Exception:
                return 0.0, "파일 크기 확인 불가"
        else:
            return 0.1, "새 파일 생성 - 충돌 위험 낮음"

    def _determine_status(self, score: float) -> str:
        """점수에 따른 상태 결정"""
        if score >= 0.7:
            return "high_efficacy"
        elif score >= 0.4:
            return "uncertain"
        else:
            return "low_efficacy"

    def suggest_strategy(self, confidence_score: float) -> str:
        """
        점수에 따른 행동 전략 제안
        
        Args:
            confidence_score: 효율성 점수 (0.0 ~ 1.0)
            
        Returns:
            전략 문자열 (aggressive, balanced, cautious)
        """
        if confidence_score >= 0.8:
            return "aggressive"  # 적극적 진화 (대담한 시도)
        elif confidence_score >= 0.5:
            return "balanced"    # 균형잡힌 접근
        else:
            return "cautious"    # 보수적 접근 (작은 수정, 검증 강화)

    def get_strategy_description(self, strategy: str) -> str:
        """전략에 대한 상세 설명 반환"""
        descriptions = {
            "aggressive": (
                "적극적 진화 모드: 대담한 구조 변경, 새 기능 추가, "
                "복잡한 리팩토링 시도 가능"
            ),
            "balanced": (
                "균형 모드: 중간 규모 변경, 기존 패턴 따르기, "
                "테스트 가능한 범위 내 진화"
            ),
            "cautious": (
                "보수적 모드: 최소한의 변경, 새 모듈 분리 우선, "
                "기존 코드 직접 수정 자제, 검증 강화"
            )
        }
        return descriptions.get(strategy, "알 수 없는 전략")


def get_meta_evaluator() -> MetaEvaluator:
    """MetaEvaluator 인스턴스 반환 (싱글톤 아님, 필요시 확장)"""
    return MetaEvaluator()