"""
Intention Core: 자율적 목표 관리 시스템
Step 6: Intentionality - AIN의 '전두엽(Frontal Lobe)' 역할

이 모듈은 AIN이 스스로 목표를 설정하고 관리할 수 있도록
Goal 객체와 IntentionCore 매니저를 제공한다.

Features:

Usage:
    from intention import IntentionCore, Goal
    
    core = IntentionCore()
    goal_id = core.add_goal("Step 6 완성하기", priority=9)
    active_goals = core.get_active_goals(limit=3)
    core.update_status(goal_id, "completed")
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional


class GoalStatus(Enum):
    """목표 상태 열거형"""
    PENDING = "pending"      # 대기 중
    ACTIVE = "active"        # 진행 중
    COMPLETED = "completed"  # 완료됨
    FAILED = "failed"        # 실패함
    DEFERRED = "deferred"    # 연기됨


@dataclass
class Goal:
    """
    목표(Goal) 데이터 구조
    
    AIN이 달성하고자 하는 단일 목표를 표현한다.
    
    Attributes:
        id: 고유 식별자 (UUID)
        content: 목표 내용 (무엇을 달성할 것인가)
        priority: 우선순위 (1-10, 높을수록 중요)
        status: 현재 상태 (pending/active/completed/failed/deferred)
        created_at: 생성 시각 (ISO 8601)
        deadline: 마감일 (선택, ISO 8601)
        metadata: 추가 메타데이터 (태그, 관련 파일 등)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    content: str = ""
    priority: int = 5
    status: str = GoalStatus.PENDING.value
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    deadline: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환 (JSON 직렬화용)"""
        return {
            "id": self.id,
            "content": self.content,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at,
            "deadline": self.deadline,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Goal":
        """딕셔너리에서 Goal 객체 생성"""
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            content=data.get("content", ""),
            priority=data.get("priority", 5),
            status=data.get("status", GoalStatus.PENDING.value),
            created_at=data.get("created_at", datetime.now().isoformat()),
            deadline=data.get("deadline"),
            metadata=data.get("metadata", {})
        )
    
    def is_actionable(self) -> bool:
        """이 목표가 현재 실행 가능한 상태인지 확인"""
        return self.status in [GoalStatus.PENDING.value, GoalStatus.ACTIVE.value]


class IntentionCore:
    """
    목표 관리 핵심 클래스
    
    AIN의 '전두엽' 역할을 수행하며, 목표의 생성, 조회,
    상태 변경, 영구 저장을 담당한다.
    
    Attributes:
        state_file: 목표 상태 저장 파일 경로
        goals: 현재 로드된 목표 목록
    """
    
    DEFAULT_STATE_FILE = "intention_state.json"
    MAX_GOALS = 100  # 최대 목표 수 (메모리 보호)
    
    def __init__(self, state_file: str = None):
        """
        IntentionCore 초기화
        
        Args:
            state_file: 상태 저장 파일 경로 (기본: intention_state.json)
        """
        self.state_file = state_file or self.DEFAULT_STATE_FILE
        self.goals: List[Goal] = []
        self._load()
        print(f"🎯 IntentionCore 초기화 완료 (목표 {len(self.goals)}개 로드)")
    
    def _load(self) -> bool:
        """저장된 목표 상태 로드"""
        if not os.path.exists(self.state_file):
            return False
        
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return False
                
                data = json.loads(content)
                goals_data = data.get("goals", [])
                
                self.goals = [Goal.from_dict(g) for g in goals_data]
                return True
                
        except json.JSONDecodeError as e:
            print(f"⚠️ IntentionCore: JSON 파싱 실패 - {e}")
            return False
        except Exception as e:
            print(f"⚠️ IntentionCore: 로드 실패 - {e}")
            return False
    
    def _save(self) -> bool:
        """현재 목표 상태를 파일에 저장"""
        try:
            data = {
                "version": "1.0",
                "updated_at": datetime.now().isoformat(),
                "goals": [g.to_dict() for g in self.goals]
            }
            
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"❌ IntentionCore: 저장 실패 - {e}")
            return False
    
    def add_goal(
        self, 
        content: str, 
        priority: int = 5,
        deadline: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        새 목표 등록
        
        Args:
            content: 목표 내용
            priority: 우선순위 (1-10, 기본 5)
            deadline: 마감일 (ISO 8601 형식, 선택)
            metadata: 추가 메타데이터 (선택)
        
        Returns:
            생성된 목표의 ID
        """
        if len(self.goals) >= self.MAX_GOALS:
            oldest_completed = self._find_oldest_completed()
            if oldest_completed:
                self.goals.remove(oldest_completed)
                print(f"♻️ 오래된 완료 목표 제거: {oldest_completed.id}")
            else:
                print(f"⚠️ 목표 수 한도 도달 ({self.MAX_GOALS}개)")
                return ""
        
        priority = max(1, min(10, priority))
        
        goal = Goal(
            content=content,
            priority=priority,
            status=GoalStatus.PENDING.value,
            deadline=deadline,
            metadata=metadata or {}
        )
        
        self.goals.append(goal)
        self._save()
        
        print(f"🎯 새 목표 등록: [{goal.id}] {content[:30]}... (P{priority})")
        return goal.id
    
    def _find_oldest_completed(self) -> Optional[Goal]:
        """가장 오래된 완료 목표 찾기"""
        completed = [g for g in self.goals if g.status == GoalStatus.COMPLETED.value]
        if not completed:
            return None
        return min(completed, key=lambda g: g.created_at)
    
    def get_goal(self, goal_id: str) -> Optional[Goal]:
        """ID로 목표 조회"""
        for goal in self.goals:
            if goal.id == goal_id:
                return goal
        return None
    
    def get_active_goals(self, limit: int = 5) -> List[Goal]:
        """
        우선순위 높은 미완료 목표 반환
        
        Args:
            limit: 반환할 최대 목표 수
        
        Returns:
            우선순위 내림차순으로 정렬된 활성 목표 목록
        """
        actionable = [g for g in self.goals if g.is_actionable()]
        
        sorted_goals = sorted(
            actionable,
            key=lambda g: (-g.priority, g.created_at)
        )
        
        return sorted_goals[:limit]
    
    def get_goals_by_status(self, status: str) -> List[Goal]:
        """특정 상태의 목표들 반환"""
        return [g for g in self.goals if g.status == status]
    
    def update_status(self, goal_id: str, new_status: str) -> bool:
        """
        목표 상태 변경
        
        Args:
            goal_id: 목표 ID
            new_status: 새 상태 (pending/active/completed/failed/deferred)
        
        Returns:
            성공 여부
        """
        valid_statuses = [s.value for s in GoalStatus]
        if new_status not in valid_statuses:
            print(f"⚠️ 유효하지 않은 상태: {new_status}")
            return False
        
        goal = self.get_goal(goal_id)
        if not goal:
            print(f"⚠️ 목표를 찾을 수 없음: {goal_id}")
            return False
        
        old_status = goal.status
        goal.status = new_status
        self._save()
        
        status_emoji = {
            "pending": "⏳",
            "active": "🔄",
            "completed": "✅",
            "failed": "❌",
            "deferred": "⏸️"
        }
        emoji = status_emoji.get(new_status, "📌")
        print(f"{emoji} 목표 상태 변경: [{goal_id}] {old_status} → {new_status}")
        
        return True
    
    def update_priority(self, goal_id: str, new_priority: int) -> bool:
        """목표 우선순위 변경"""
        goal = self.get_goal(goal_id)
        if not goal:
            return False
        
        new_priority = max(1, min(10, new_priority))
        goal.priority = new_priority
        self._save()
        
        print(f"📊 목표 우선순위 변경: [{goal_id}] → P{new_priority}")
        return True
    
    def remove_goal(self, goal_id: str) -> bool:
        """목표 삭제"""
        goal = self.get_goal(goal_id)
        if not goal:
            return False
        
        self.goals.remove(goal)
        self._save()
        
        print(f"🗑️ 목표 삭제: [{goal_id}] {goal.content[:20]}...")
        return True
    
    def get_summary(self) -> Dict[str, Any]:
        """목표 상태 요약 반환"""
        status_counts = {}
        for status in GoalStatus:
            count = len([g for g in self.goals if g.status == status.value])
            status_counts[status.value] = count
        
        active_goals = self.get_active_goals(limit=3)
        top_priorities = [
            {"id": g.id, "content": g.content[:50], "priority": g.priority}
            for g in active_goals
        ]
        
        return {
            "total_goals": len(self.goals),
            "status_breakdown": status_counts,
            "top_priorities": top_priorities,
            "actionable_count": len([g for g in self.goals if g.is_actionable()])
        }
    
    def get_formatted_summary(self) -> str:
        """사람이 읽기 쉬운 요약 문자열 반환"""
        summary = self.get_summary()
        
        lines = [
            "=== 🎯 AIN Intention Summary ===",
            f"총 목표: {summary['total_goals']}개",
            f"실행 가능: {summary['actionable_count']}개",
            "",
            "[상태별 분포]"
        ]
        
        status_emoji = {
            "pending": "⏳",
            "active": "🔄", 
            "completed": "✅",
            "failed": "❌",
            "deferred": "⏸️"
        }
        
        for status, count in summary["status_breakdown"].items():
            emoji = status_emoji.get(status, "📌")
            lines.append(f"  {emoji} {status}: {count}")
        
        if summary["top_priorities"]:
            lines.append("")
            lines.append("[우선 목표]")
            for i, goal in enumerate(summary["top_priorities"], 1):
                lines.append(f"  {i}. [P{goal['priority']}] {goal['content']}")
        
        return "\n".join(lines)


def get_intention_core(state_file: str = None) -> IntentionCore:
    """IntentionCore 팩토리 함수"""
    return IntentionCore(state_file=state_file)