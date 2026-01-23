"""
Engine Goal Executor: 목표 실행 및 확인 로직
Step 6: Intentionality - ensure_active_goal 구현

이 모듈은 GoalManagerMixin에서 호출되어 실제 목표 확인 및 생성 로직을 수행한다.
대형 파일(goal_manager.py) 수정 없이 새 모듈로 기능을 확장한다.

Usage:
    from engine.goal_executor import GoalExecutor
    
    executor = GoalExecutor(intention_core, fact_core, muse)
    executor.ensure_active_goal()
"""

import re
from typing import Optional, List, Dict, Any, TYPE_CHECKING

from .goal_prompts import NEXT_GOAL_PROMPT, PRIORITY_PROMPT, COMPLETION_CHECK_PROMPT

if TYPE_CHECKING:
    from intention.core import IntentionCore
    from fact_core import FactCore
    from muse import Muse

# GoalStatus import (get_goals_by_status 사용)
try:
    from intention.core import GoalStatus
except ImportError:
    GoalStatus = None


class GoalExecutor:
    """
    목표 실행기
    
    IntentionCore, FactCore, Muse를 연결하여 자율적 목표 수립을 수행한다.
    이 클래스는 GoalManagerMixin의 ensure_active_goal() 로직을 캡슐화한다.
    
    Attributes:
        intention: IntentionCore 인스턴스 (목표 저장소)
        fact_core: FactCore 인스턴스 (로드맵 제공)
        muse: Muse 인스턴스 (LLM 추론)
    """
    
    def __init__(
        self, 
        intention: "IntentionCore", 
        fact_core: "FactCore", 
        muse: "Muse"
    ):
        self.intention = intention
        self.fact_core = fact_core
        self.muse = muse
    
    def ensure_active_goal(self) -> Optional[str]:
        """
        활성 목표가 있는지 확인하고, 없으면 새로 생성한다.
        
        Returns:
            현재 활성 목표의 ID (새로 생성된 경우 새 ID)
            목표 생성 실패 시 None
        """
        active_goals = self.intention.get_active_goals(limit=1)
        
        if active_goals:
            goal = active_goals[0]
            print(f"🎯 현재 목표: {goal.content}")
            return goal.id
        
        print("🤔 활성 목표 없음. 새 목표를 생성합니다...")
        return self._generate_new_goal()
    
    def _generate_new_goal(self) -> Optional[str]:
        """
        Muse(Dreamer)를 통해 새로운 목표를 생성한다.
        
        Returns:
            생성된 목표의 ID, 실패 시 None
        """
        roadmap_text = self._get_roadmap_context()
        
        prompt = NEXT_GOAL_PROMPT.format(roadmap_text=roadmap_text)
        
        try:
            response = self.muse._ask_dreamer(prompt)
            
            if not response:
                print("⚠️ Dreamer 응답 없음. 기본 목표를 설정합니다.")
                return self._set_default_goal()
            
            goal_content = self._parse_goal_response(response)
            
            if goal_content:
                goal_id = self.intention.add_goal(
                    content=goal_content,
                    priority=7,
                    metadata={"source": "auto_generated"}
                )
                print(f"✨ 새 목표 생성: {goal_content}")
                return goal_id
            else:
                print("⚠️ 목표 파싱 실패. 기본 목표를 설정합니다.")
                return self._set_default_goal()
                
        except Exception as e:
            print(f"❌ 목표 생성 실패: {e}")
            return self._set_default_goal()
    
    def _get_roadmap_context(self) -> str:
        """로드맵 컨텍스트를 가져온다."""
        try:
            if hasattr(self.fact_core, 'get_formatted_roadmap'):
                return self.fact_core.get_formatted_roadmap()
            
            if hasattr(self.fact_core, 'facts'):
                roadmap = self.fact_core.facts.get('roadmap', {})
                current_focus = roadmap.get('current_focus', 'Step 6: Intentionality')
                return f"현재 진행 중: {current_focus}"
            
            return "Step 6: Intentionality - 자율적 목표 설정 시스템 구현"
        except Exception as e:
            print(f"⚠️ 로드맵 로드 실패: {e}")
            return "Step 6: Intentionality"
    
    def _parse_goal_response(self, response: str) -> Optional[str]:
        """
        Dreamer 응답에서 목표를 추출한다.
        
        Args:
            response: Dreamer의 응답 텍스트
        
        Returns:
            추출된 목표 내용, 실패 시 None
        """
        patterns = [
            r'NEXT_GOAL:\s*(.+?)(?:\n|$)',
            r'목표:\s*(.+?)(?:\n|$)',
            r'Goal:\s*(.+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, response, re.IGNORECASE)
            if match:
                goal = match.group(1).strip()
                goal = goal.strip('[]"\'')
                if len(goal) > 10:
                    return goal
        
        lines = response.strip().split('\n')
        for line in lines:
            line = line.strip()
            if len(line) > 20 and not line.startswith('#'):
                return line
        
        return None
    
    def _set_default_goal(self) -> str:
        """기본 목표를 설정한다."""
        default_content = "Step 6 Intentionality 시스템 안정화 및 테스트"
        goal_id = self.intention.add_goal(
            content=default_content,
            priority=5,
            metadata={"source": "default_fallback"}
        )
        print(f"📌 기본 목표 설정: {default_content}")
        return goal_id
    
    def check_goal_completion(self, goal_id: str) -> bool:
        """
        목표 달성 여부를 확인한다.
        
        Args:
            goal_id: 확인할 목표의 ID
        
        Returns:
            달성 여부 (True/False)
        """
        goal = self.intention.get_goal(goal_id)
        if not goal:
            return False
        
        return goal.status == "completed"
    
    def get_goal_summary(self) -> str:
        """현재 목표 상태 요약을 반환한다."""
        active = self.intention.get_active_goals(limit=3)
        # get_pending_goals 대신 get_goals_by_status 사용
        pending_status = GoalStatus.PENDING.value if GoalStatus else "pending"
        pending = self.intention.get_goals_by_status(pending_status)[:3]
        
        summary_parts = ["=== 🎯 목표 현황 ==="]
        
        if active:
            summary_parts.append("\n[진행 중]")
            for g in active:
                summary_parts.append(f"  • {g.content} (우선순위: {g.priority})")
        else:
            summary_parts.append("\n[진행 중] 없음")
        
        if pending:
            summary_parts.append("\n[대기 중]")
            for g in pending:
                summary_parts.append(f"  • {g.content}")
        
        return "\n".join(summary_parts)


def create_goal_executor(
    intention: "IntentionCore",
    fact_core: "FactCore", 
    muse: "Muse"
) -> GoalExecutor:
    """GoalExecutor 팩토리 함수"""
    return GoalExecutor(intention, fact_core, muse)