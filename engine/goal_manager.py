"""
Engine Goal Manager: 목표 관리 및 자율 수립 믹스인
Step 6: Intentionality - Engine과 IntentionCore를 연결하는 제어 로직

이 모듈은 AINCore에 상속되어 '전두엽' 기능을 수행한다.
스스로 로드맵을 읽고, Muse를 통해 당면한 목표를 생성하며,
IntentionCore를 통해 이를 추적한다.

Usage:
    # engine/__init__.py에서 AINCore 상속 목록에 추가
    from .goal_manager import GoalManagerMixin
    
    class AINCore(_AINCore, ..., GoalManagerMixin):
        pass
"""

import json
from typing import List, Dict, Any, Optional

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
    
    Attributes:
        intention: IntentionCore 인스턴스 (목표 저장소)
    """
    
    def init_intention_system(self):
        """
        Intention System 초기화
        
        AINCore의 __init__에서 호출되어 IntentionCore를 초기화한다.
        """
        if HAS_INTENTION:
            self.intention = IntentionCore()
            print("🎯 Intention System(전두엽) 활성화 완료")
        else:
            self.intention = None
            print("⚠️ Intention System 비활성화 (패키지 미설치)")

    async def ensure_active_goals(self) -> bool:
        """
        현재 활성화된 목표가 있는지 확인하고, 없다면 스스로 수립한다.
        
        Returns:
            bool: 목표가 새로 수립되었으면 True, 기존 목표 유지면 False
        """
        if not self.intention:
            return False
            
        # 1. 활성 목표 확인
        active_goals = self.intention.get_active_goals()
        if active_goals:
            print(f"📋 현재 활성 목표 {len(active_goals)}개 유지 중")
            return False
            
        print("🤔 활성 목표 부재. 로드맵 기반 목표 수립을 시작합니다...")
        
        # 2. 로드맵 컨텍스트 파악
        current_focus = self._extract_current_focus()
        
        # 3. Muse에게 목표 생성 요청
        new_goals = await self._dream_new_goals(current_focus)
        
        # 4. 목표 등록
        if new_goals:
            for goal_data in new_goals:
                goal_content = goal_data.get("content", str(goal_data))
                goal_priority = goal_data.get("priority", 5)
                
                self.intention.add_goal(
                    content=goal_content,
                    priority=goal_priority,
                    source="auto_generated",
                    metadata={"focus": current_focus}
                )
            
            print(f"✅ {len(new_goals)}개의 새 목표가 수립되었습니다.")
            return True
        
        return False
    
    def _extract_current_focus(self) -> str:
        """
        FactCore에서 현재 로드맵 단계를 추출한다.
        
        Returns:
            str: 현재 집중해야 할 단계 설명
        """
        current_focus = "Self-Evolution"
        
        if hasattr(self, "fact_core"):
            roadmap = self.fact_core.facts.get("roadmap", {})
            
            # current_focus 키가 있으면 직접 사용
            if "current_focus" in roadmap:
                return roadmap["current_focus"]
            
            # 없으면 in_progress 상태인 단계 찾기
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
    
    async def _dream_new_goals(self, current_focus: str) -> List[Dict[str, Any]]:
        """
        Muse(Dreamer)에게 새로운 목표 생성을 요청한다.
        
        Args:
            current_focus: 현재 로드맵 단계
            
        Returns:
            List[Dict]: 생성된 목표 리스트 (content, priority 포함)
        """
        if not hasattr(self, "muse"):
            print("⚠️ Muse 인스턴스 없음. 기본 목표 생성.")
            return self._generate_default_goals(current_focus)
        
        prompt = self._build_goal_generation_prompt(current_focus)
        
        try:
            response = self.muse._ask_dreamer(prompt)
            
            if not response:
                return self._generate_default_goals(current_focus)
            
            # JSON 파싱 시도
            goals = self._parse_goal_response(response)
            
            if goals:
                return goals
            else:
                return self._generate_default_goals(current_focus)
                
        except Exception as e:
            print(f"⚠️ 목표 생성 중 오류: {e}")
            return self._generate_default_goals(current_focus)
    
    def _build_goal_generation_prompt(self, current_focus: str) -> str:
        """
        목표 생성을 위한 프롬프트를 구성한다.
        
        Args:
            current_focus: 현재 로드맵 단계
            
        Returns:
            str: Dreamer에게 전달할 프롬프트
        """
        prompt_lines = [
            "너는 AIN의 목표 수립 모듈이다.",
            "",
            f"현재 로드맵 단계: {current_focus}",
            "",
            "위 단계를 달성하기 위한 구체적인 하위 기술 목표 3가지를 제안하라.",
            "",
            "반드시 다음 JSON 형식으로만 응답하라:",
            "[",
            '  {"content": "목표 1 설명", "priority": 8},',
            '  {"content": "목표 2 설명", "priority": 7},',
            '  {"content": "목표 3 설명", "priority": 6}',
            "]",
            "",
            "priority는 1-10 범위이며 높을수록 중요하다.",
        ]
        return "\n".join(prompt_lines)
    
    def _parse_goal_response(self, response: str) -> List[Dict[str, Any]]:
        """
        Dreamer 응답에서 목표 JSON을 파싱한다.
        
        Args:
            response: Dreamer의 응답 문자열
            
        Returns:
            List[Dict]: 파싱된 목표 리스트
        """
        if not response:
            return []
        
        # JSON 배열 추출 시도
        try:
            # 응답에서 [ ] 블록 찾기
            start_idx = response.find("[")
            end_idx = response.rfind("]")
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx + 1]
                goals = json.loads(json_str)
                
                if isinstance(goals, list):
                    # 유효성 검증
                    valid_goals = []
                    for g in goals:
                        if isinstance(g, dict) and "content" in g:
                            valid_goals.append({
                                "content": str(g.get("content", "")),
                                "priority": int(g.get("priority", 5))
                            })
                    return valid_goals
        except json.JSONDecodeError:
            pass
        except Exception:
            pass
        
        return []
    
    def _generate_default_goals(self, current_focus: str) -> List[Dict[str, Any]]:
        """
        Muse 응답 실패 시 기본 목표를 생성한다.
        
        Args:
            current_focus: 현재 로드맵 단계
            
        Returns:
            List[Dict]: 기본 목표 리스트
        """
        return [
            {
                "content": f"현재 단계({current_focus}) 코드 분석 및 이해",
                "priority": 7
            },
            {
                "content": "기존 테스트 케이스 실행 및 검증",
                "priority": 6
            },
            {
                "content": "다음 진화 방향 탐색",
                "priority": 5
            }
        ]
    
    def get_goal_status_report(self) -> str:
        """
        현재 목표 상태를 문자열 리포트로 반환한다.
        
        Returns:
            str: 목표 상태 리포트
        """
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
        """
        목표를 완료 상태로 변경한다.
        
        Args:
            goal_id: 완료할 목표 ID
            
        Returns:
            bool: 성공 여부
        """
        if not self.intention:
            return False
        
        success = self.intention.update_status(goal_id, GoalStatus.COMPLETED)
        
        if success:
            print(f"✅ 목표 완료: {goal_id}")
        
        return success
    
    def fail_goal(self, goal_id: str, reason: str = "") -> bool:
        """
        목표를 실패 상태로 변경한다.
        
        Args:
            goal_id: 실패한 목표 ID
            reason: 실패 사유
            
        Returns:
            bool: 성공 여부
        """
        if not self.intention:
            return False
        
        success = self.intention.update_status(goal_id, GoalStatus.FAILED)
        
        if success:
            print(f"❌ 목표 실패: {goal_id} - {reason}")
        
        return success