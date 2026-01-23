"""
Engine Meta-Cognition: Step 7 - 메타인지
========================================
자신의 사고 과정을 관찰하고 평가하는 능력.
"생각에 대해 생각하기" - 인지 과정의 자기 모니터링.
"""
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from engine.meta_cycle import MetaCycle, CycleReport


class MetaCognitionMixin:
    """
    메타인지 믹스인 - AINCore에 메타인지 능력 부여

    메타인지란:

    Integration:
    """

    _meta_cycle_instance: Optional["MetaCycle"] = None

    @property
    def _meta_cycle(self) -> "MetaCycle":
        """MetaCycle 인스턴스를 Lazy Loading으로 제공"""
        if self._meta_cycle_instance is None:
            from engine.meta_cycle import MetaCycle
            self._meta_cycle_instance = MetaCycle()
        return self._meta_cycle_instance

    def _reflect_on_thinking(self) -> Dict[str, Any]:
        """
        최근 사고 과정을 성찰한다.

        MetaCycle을 통해 현재 상태를 평가하고 전략을 조정한다.

        Returns:
            성찰 결과 (패턴, 편향, 개선점, 전략 모드 등)
        """
        context = self._gather_meta_context()
        
        try:
            report = self._meta_cycle.process_cycle(context)
            
            self._apply_cycle_report(report)
            
            return self._report_to_dict(report)
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "context_gathered": bool(context)
            }

    def _gather_meta_context(self) -> Dict[str, Any]:
        """메타인지 평가를 위한 컨텍스트를 수집한다."""
        context = {
            "timestamp": None,
            "roadmap_status": {},
            "recent_evolutions": [],
            "recent_errors": [],
            "memory_stats": {},
            "current_interval": getattr(self, "current_interval", 3600),
            "burst_mode": getattr(self, "burst_mode", False),
        }

        try:
            from datetime import datetime
            context["timestamp"] = datetime.now().isoformat()
        except Exception:
            pass

        if hasattr(self, "fact_core"):
            try:
                context["roadmap_status"] = {
                    "current_focus": self.fact_core.get_fact(
                        "roadmap", "current_focus", default="unknown"
                    )
                }
            except Exception:
                pass

        if hasattr(self, "nexus"):
            try:
                context["recent_evolutions"] = self.nexus.get_recent_history(limit=5)
            except Exception:
                pass

            try:
                if hasattr(self.nexus, "vector_memory"):
                    vm = self.nexus.vector_memory
                    if hasattr(vm, "_lance_connected"):
                        context["memory_stats"]["lance_connected"] = vm._lance_connected
            except Exception:
                pass

        try:
            from utils.error_memory import get_error_memory
            em = get_error_memory()
            if hasattr(em, "get_recent_errors"):
                context["recent_errors"] = em.get_recent_errors(limit=3)
            elif hasattr(em, "errors"):
                all_errors = []
                for file_errors in em.errors.values():
                    all_errors.extend(file_errors[-2:])
                context["recent_errors"] = all_errors[:5]
        except Exception:
            pass

        return context

    def _apply_cycle_report(self, report: "CycleReport") -> None:
        """CycleReport 결과를 시스템 상태에 반영한다."""
        if report is None:
            return

        tuning = getattr(report, "tuning_params", {})
        
        if "interval_multiplier" in tuning:
            base_interval = getattr(self, "current_interval", 3600)
            new_interval = int(base_interval * tuning["interval_multiplier"])
            new_interval = max(1800, min(7200, new_interval))
            if hasattr(self, "current_interval"):
                self.current_interval = new_interval

        recommended_mode = getattr(report, "recommended_mode", None)
        if recommended_mode is not None:
            mode_name = recommended_mode.value if hasattr(recommended_mode, "value") else str(recommended_mode)
            if mode_name == "accelerated" and hasattr(self, "burst_mode"):
                pass
            elif mode_name == "conservative" and hasattr(self, "burst_mode"):
                self.burst_mode = False

    def _report_to_dict(self, report: "CycleReport") -> Dict[str, Any]:
        """CycleReport를 딕셔너리로 변환한다."""
        if report is None:
            return {"status": "no_report"}

        result = {
            "status": "success",
            "efficacy_score": getattr(report, "efficacy_score", 0.0),
            "confidence": getattr(report, "confidence", 0.0),
            "tuning_params": getattr(report, "tuning_params", {}),
            "suggestions": getattr(report, "suggestions", []),
            "timestamp": getattr(report, "timestamp", None),
        }

        recommended_mode = getattr(report, "recommended_mode", None)
        if recommended_mode is not None:
            result["recommended_mode"] = (
                recommended_mode.value 
                if hasattr(recommended_mode, "value") 
                else str(recommended_mode)
            )

        return result

    def _evaluate_decision_quality(self, decision: str, outcome: Optional[str] = None) -> float:
        """
        결정의 질을 평가한다.

        Args:
            decision: 내린 결정
            outcome: 결과 (있는 경우)

        Returns:
            품질 점수 (0.0 ~ 1.0)
        """
        if not decision:
            return 0.3

        base_score = 0.5

        positive_keywords = ["success", "완료", "개선", "fix", "implement"]
        negative_keywords = ["fail", "error", "실패", "오류", "crash"]

        decision_lower = decision.lower()
        for kw in positive_keywords:
            if kw in decision_lower:
                base_score += 0.1

        for kw in negative_keywords:
            if kw in decision_lower:
                base_score -= 0.1

        if outcome:
            outcome_lower = outcome.lower()
            if "success" in outcome_lower or "완료" in outcome_lower:
                base_score += 0.2
            elif "fail" in outcome_lower or "실패" in outcome_lower:
                base_score -= 0.2

        return max(0.0, min(1.0, base_score))

    def _identify_knowledge_gaps(self) -> list:
        """
        자신의 지식 공백을 식별한다.
        "모르는 것을 안다" - 메타인지의 핵심

        Returns:
            알지 못하는 것들의 목록
        """
        gaps = []

        if hasattr(self, "fact_core"):
            try:
                roadmap = self.fact_core.get_fact("roadmap", default={})
                for phase_key, phase_data in roadmap.items():
                    if not isinstance(phase_data, dict):
                        continue
                    if not phase_key.startswith("phase_"):
                        continue
                    for step_key, step_data in phase_data.items():
                        if not isinstance(step_data, dict):
                            continue
                        status = step_data.get("status", "")
                        if status in ["pending", "in_progress"]:
                            desc = step_data.get("desc", step_key)
                            gaps.append(f"미완료 단계: {desc}")
            except Exception:
                gaps.append("로드맵 분석 불가")

        try:
            from utils.error_memory import get_error_memory
            em = get_error_memory()
            if hasattr(em, "errors"):
                for filename, errors in em.errors.items():
                    if len(errors) >= 3:
                        gaps.append(f"반복 오류 파일: {filename}")
        except Exception:
            pass

        if not gaps:
            gaps.append("현재 식별된 지식 공백 없음")

        return gaps

    def _assess_confidence(self, statement: str) -> Dict[str, Any]:
        """
        특정 판단/진술에 대한 확신도를 평가한다.
        "얼마나 확실한지 아는 것" - 메타인지의 핵심

        Args:
            statement: 평가할 진술

        Returns:
            {
                "confidence": 0.0~1.0,
                "reasoning": "확신/불확신 이유",
                "known_factors": [...],
                "unknown_factors": [...]
            }
        """
        if not statement:
            return {
                "confidence": 0.0,
                "reasoning": "빈 진술",
                "known_factors": [],
                "unknown_factors": ["진술 내용 없음"]
            }

        known_factors = []
        unknown_factors = []
        confidence = 0.5

        certain_words = ["반드시", "확실히", "항상", "절대", "definitely", "always"]
        uncertain_words = ["아마", "maybe", "perhaps", "possibly", "might"]

        statement_lower = statement.lower()

        for word in certain_words:
            if word in statement_lower:
                known_factors.append(f"확신 표현 포함: {word}")
                confidence += 0.1

        for word in uncertain_words:
            if word in statement_lower:
                unknown_factors.append(f"불확실 표현 포함: {word}")
                confidence -= 0.1

        if hasattr(self, "nexus") and hasattr(self.nexus, "retrieve_relevant_memories"):
            try:
                memories = self.nexus.retrieve_relevant_memories(statement, limit=3)
                if memories:
                    known_factors.append(f"관련 기억 {len(memories)}개 발견")
                    confidence += 0.1 * min(len(memories), 3)
                else:
                    unknown_factors.append("관련 기억 없음")
                    confidence -= 0.1
            except Exception:
                unknown_factors.append("기억 검색 실패")

        confidence = max(0.0, min(1.0, confidence))

        if confidence >= 0.7:
            reasoning = "높은 확신: 관련 지식과 경험이 충분함"
        elif confidence >= 0.4:
            reasoning = "중간 확신: 일부 정보는 있으나 불확실한 요소 존재"
        else:
            reasoning = "낮은 확신: 관련 지식 부족 또는 불확실성 높음"

        return {
            "confidence": round(confidence, 2),
            "reasoning": reasoning,
            "known_factors": known_factors,
            "unknown_factors": unknown_factors
        }