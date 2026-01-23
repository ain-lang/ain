"""
Engine Goal Manager: 목표 관리 및 자율 수립 믹스인
Step 6: Intentionality - Engine과 IntentionCore를 연결하는 제어 로직

이 모듈은 AINCore에 상속되어 '전두엽' 기능을 수행한다.
스스로 로드맵을 읽고, Muse를 통해 당면한 목표를 생성하며,
IntentionCore를 통해 이를 추적한다.
"""

from typing import List, Dict, Any

from .goal_generator import dream_new_goals

# Intention Core 임포트
try:
    from intention.core import IntentionCore, GoalStatus
    HAS_INTENTION = True
except ImportError:
    HAS_INTENTION = False
    print("⚠️ Intention 패키지 로드 실패. 목표 관리 시스템 비활성화.")


class GoalManagerMixin:
    """
    목표 관리 믹스인

    AINCore에 상속되어 '전두엽' 기능을 수행한다.
    스스로 로드맵을 읽고, Muse를 통해 당면한 목표를 생성하며,
    IntentionCore를 통해 이를 추적한다.
    """

    def init_intention_system(self):
        """Intention System 초기화"""
        if HAS_INTENTION:
            self.intention = IntentionCore()
            print("🎯 Intention System(전두엽) 활성화 완료")
        else:
            self.intention = None
            print("⚠️ Intention System 비활성화 (패키지 미설치)")

    async def ensure_active_goals(self) -> bool:
        """현재 활성화된 목표가 있는지 확인하고, 없다면 스스로 수립한다."""
        if not self.intention:
            return False

        active_goals = self.intention.get_active_goals()
        if active_goals:
            print(f"📋 현재 활성 목표 {len(active_goals)}개 유지 중")
            return False

        print("🤔 활성 목표 부재. 로드맵 기반 목표 수립을 시작합니다...")

        current_focus = self._extract_current_focus()
        new_goals = await dream_new_goals(self, current_focus)

        if new_goals:
            for goal_data in new_goals:
                goal_content = goal_data.get("content", str(goal_data))
                goal_priority = goal_data.get("priority", 5)

                self.intention.add_goal(
                    content=goal_content,
                    priority=goal_priority,
                    metadata={"focus": current_focus, "source": "auto_generated"}
                )

            print(f"✅ {len(new_goals)}개의 새 목표가 수립되었습니다.")
            return True

        return False

    def _extract_current_focus(self) -> str:
        """FactCore에서 현재 로드맵 단계를 추출한다."""
        current_focus = "Self-Evolution"

        if hasattr(self, "fact_core"):
            roadmap = self.fact_core.facts.get("roadmap", {})

            if "current_focus" in roadmap:
                return roadmap["current_focus"]

            for phase_name, phase_data in roadmap.items():
                if isinstance(phase_data, dict):
                    for step_name, step_data in phase_data.items():
                        if isinstance(step_data, dict):
                            status = step_data.get("status", "")
                            if status == "in_progress":
                                desc = step_data.get("desc", step_name)
                                current_focus = f"{step_name}: {desc}"
                                break

        return current_focus

    def get_goal_status_report(self) -> str:
        """현재 목표 상태를 문자열 리포트로 반환한다."""
        if not self.intention:
            return "🎯 Intention System 비활성화"

        active_goals = self.intention.get_active_goals()
        pending_goals = self.intention.get_goals_by_status(GoalStatus.PENDING)
        completed_goals = self.intention.get_goals_by_status(GoalStatus.COMPLETED)

        lines = [
            "🎯 **Goal Status Report**",
            f"- Active: {len(active_goals)}",
            f"- Pending: {len(pending_goals)}",
            f"- Completed: {len(completed_goals)}",
        ]

        if active_goals:
            lines.append("")
            lines.append("**Current Active Goals:**")
            for i, goal in enumerate(active_goals[:3], 1):
                content = goal.content[:50] + "..." if len(goal.content) > 50 else goal.content
                lines.append(f"  {i}. [{goal.priority}] {content}")

        return "\n".join(lines)

    def complete_goal(self, goal_id: str) -> bool:
        """목표를 완료 상태로 변경한다."""
        if not self.intention:
            return False

        success = self.intention.update_status(goal_id, GoalStatus.COMPLETED)

        if success:
            print(f"✅ 목표 완료: {goal_id}")

        return success

    def fail_goal(self, goal_id: str, reason: str = "") -> bool:
        """목표를 실패 상태로 변경한다."""
        if not self.intention:
            return False

        success = self.intention.update_status(goal_id, GoalStatus.FAILED)

        if success:
            print(f"❌ 목표 실패: {goal_id} - {reason}")

        return success
