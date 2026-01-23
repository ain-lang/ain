"""
Engine Goal Evaluator: 목표 달성 여부 평가 모듈
Step 6: Intentionality - 진화 후 목표 완료 검증

이 모듈은 진화가 완료된 후 현재 활성 목표가 실제로 달성되었는지
평가하는 '자기 검증' 기능을 제공한다.

GoalManagerMixin이 진화 직후 호출하여 목표 상태를 업데이트한다.

Architecture:
    EvolutionMixin (진화 실행)
        ↓ 진화 완료
    GoalEvaluator (이 모듈)
        ↓ Muse에게 평가 요청
    IntentionCore (상태 업데이트)

Usage:
    from engine.goal_evaluator import GoalEvaluator
    
    evaluator = GoalEvaluator(intention_core, muse, nexus)
    result = evaluator.evaluate_goal_completion(goal, evolution_result)
"""

import re
from typing import Dict, Any, Optional, TYPE_CHECKING

from .goal_prompts import COMPLETION_CHECK_PROMPT

if TYPE_CHECKING:
    from intention.core import IntentionCore, Goal
    from muse import Muse
    from nexus import Nexus


class EvaluationResult:
    """
    목표 평가 결과 데이터 클래스
    
    Attributes:
        status: 평가된 상태 (completed, in_progress, blocked, failed)
        reason: 판단 근거
        confidence: 평가 신뢰도 (0.0 ~ 1.0)
        raw_response: LLM 원본 응답
    """
    
    def __init__(
        self,
        status: str = "in_progress",
        reason: str = "",
        confidence: float = 0.5,
        raw_response: str = ""
    ):
        self.status = status
        self.reason = reason
        self.confidence = confidence
        self.raw_response = raw_response
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "status": self.status,
            "reason": self.reason,
            "confidence": self.confidence,
            "raw_response": self.raw_response[:200] if self.raw_response else ""
        }
    
    @property
    def is_completed(self) -> bool:
        """목표 완료 여부"""
        return self.status == "completed"
    
    @property
    def is_blocked(self) -> bool:
        """목표 차단 여부"""
        return self.status == "blocked"


class GoalEvaluator:
    """
    목표 달성 평가기
    
    진화 결과를 분석하여 현재 활성 목표가 달성되었는지 판단한다.
    Muse(Dreamer)에게 평가를 요청하고, 결과를 파싱하여
    IntentionCore의 목표 상태를 업데이트한다.
    
    Attributes:
        intention: IntentionCore 인스턴스 (목표 저장소)
        muse: Muse 인스턴스 (LLM 추론)
        nexus: Nexus 인스턴스 (진화 기록 조회)
    """
    
    def __init__(
        self,
        intention: "IntentionCore",
        muse: "Muse",
        nexus: "Nexus"
    ):
        self.intention = intention
        self.muse = muse
        self.nexus = nexus
        
        self._evaluation_count = 0
        self._completion_count = 0
    
    def evaluate_goal_completion(
        self,
        goal: "Goal",
        evolution_result: Dict[str, Any]
    ) -> EvaluationResult:
        """
        목표 달성 여부 평가
        
        Args:
            goal: 평가할 목표 객체
            evolution_result: 진화 실행 결과 딕셔너리
                - success: 진화 성공 여부
                - action: 수행된 액션
                - files_modified: 수정된 파일 목록
        
        Returns:
            EvaluationResult: 평가 결과
        """
        self._evaluation_count += 1
        
        if not goal:
            return EvaluationResult(
                status="failed",
                reason="평가할 목표가 없습니다.",
                confidence=1.0
            )
        
        if not evolution_result.get("success", False):
            return EvaluationResult(
                status="in_progress",
                reason="진화가 실패하여 목표 진행 상태 유지",
                confidence=0.8
            )
        
        recent_history = self._get_recent_evolution_history()
        
        prompt = self._build_evaluation_prompt(goal, recent_history)
        
        response = self._ask_dreamer(prompt)
        
        result = self._parse_evaluation_response(response)
        
        if result.is_completed:
            self._completion_count += 1
            self._update_goal_status(goal, "completed", result.reason)
        elif result.is_blocked:
            self._update_goal_status(goal, "failed", result.reason)
        
        return result
    
    def _get_recent_evolution_history(self, limit: int = 5) -> str:
        """최근 진화 기록 조회"""
        try:
            history = self.nexus.get_recent_history(limit=limit)
            if not history:
                return "최근 진화 기록 없음"
            
            lines = []
            for record in history:
                timestamp = record.get("timestamp", "")[:19]
                action = record.get("action", "Unknown")
                file = record.get("file", "unknown")
                desc = record.get("description", "")[:100]
                status = record.get("status", "unknown")
                
                lines.append(f"- [{timestamp}] {action} {file}: {desc} ({status})")
            
            return "\n".join(lines)
        except Exception as e:
            print(f"⚠️ 진화 기록 조회 실패: {e}")
            return "진화 기록 조회 실패"
    
    def _build_evaluation_prompt(self, goal: "Goal", recent_history: str) -> str:
        """평가용 프롬프트 생성"""
        goal_content = goal.content if hasattr(goal, 'content') else str(goal)
        
        prompt = COMPLETION_CHECK_PROMPT.format(
            goal_content=goal_content,
            recent_history=recent_history
        )
        
        return prompt
    
    def _ask_dreamer(self, prompt: str) -> str:
        """Dreamer에게 평가 요청"""
        try:
            if hasattr(self.muse, '_ask_dreamer'):
                return self.muse._ask_dreamer(prompt)
            
            result = self.muse.dreamer_client.chat([
                {"role": "system", "content": "너는 AIN의 목표 평가 모듈이다. 목표 달성 여부를 객관적으로 판단하라."},
                {"role": "user", "content": prompt}
            ])
            
            if result.get("success"):
                return result.get("content", "")
            
            return ""
        except Exception as e:
            print(f"⚠️ Dreamer 평가 요청 실패: {e}")
            return ""
    
    def _parse_evaluation_response(self, response: str) -> EvaluationResult:
        """LLM 응답 파싱"""
        if not response:
            return EvaluationResult(
                status="in_progress",
                reason="평가 응답 없음",
                confidence=0.3,
                raw_response=""
            )
        
        status = "in_progress"
        reason = ""
        confidence = 0.5
        
        status_match = re.search(
            r'STATUS:\s*(completed|in_progress|blocked|failed)',
            response,
            re.IGNORECASE
        )
        if status_match:
            status = status_match.group(1).lower()
            confidence = 0.8
        
        reason_match = re.search(
            r'REASON:\s*(.+?)(?=\n\n|\n[A-Z]|$)',
            response,
            re.IGNORECASE | re.DOTALL
        )
        if reason_match:
            reason = reason_match.group(1).strip()
        
        if not reason:
            lines = response.strip().split('\n')
            for line in lines:
                if line.strip() and not line.startswith('STATUS'):
                    reason = line.strip()[:200]
                    break
        
        return EvaluationResult(
            status=status,
            reason=reason,
            confidence=confidence,
            raw_response=response
        )
    
    def _update_goal_status(self, goal: "Goal", status: str, reason: str):
        """IntentionCore에 목표 상태 업데이트 요청"""
        try:
            from intention.core import GoalStatus
            
            status_map = {
                "completed": GoalStatus.COMPLETED,
                "failed": GoalStatus.FAILED,
                "in_progress": GoalStatus.ACTIVE,
                "blocked": GoalStatus.FAILED
            }
            
            goal_status = status_map.get(status, GoalStatus.ACTIVE)
            
            if hasattr(self.intention, 'update_status'):
                self.intention.update_status(goal.id, goal_status)
                print(f"🎯 목표 상태 업데이트: {goal.id} → {status}")
            
            if hasattr(self.intention, 'add_note'):
                self.intention.add_note(goal.id, f"평가 결과: {reason}")
                
        except Exception as e:
            print(f"⚠️ 목표 상태 업데이트 실패: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """평가 통계 반환"""
        return {
            "total_evaluations": self._evaluation_count,
            "completions": self._completion_count,
            "completion_rate": (
                self._completion_count / max(self._evaluation_count, 1)
            ) * 100
        }


def get_goal_evaluator(
    intention: "IntentionCore",
    muse: "Muse",
    nexus: "Nexus"
) -> GoalEvaluator:
    """
    GoalEvaluator 인스턴스 생성 헬퍼
    
    Args:
        intention: IntentionCore 인스턴스
        muse: Muse 인스턴스
        nexus: Nexus 인스턴스
    
    Returns:
        GoalEvaluator 인스턴스
    """
    return GoalEvaluator(intention, muse, nexus)