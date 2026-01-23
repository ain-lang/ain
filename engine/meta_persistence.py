"""
Engine Meta Persistence: 메타인지 상태 영속화
Step 7: Meta-Cognition - Transient State to Persistent Identity

이 모듈은 메모리(RAM) 상에서만 존재하는 메타인지 상태(현재 전략, 자신감 점수 등)를
FactCore(Identity)에 주기적으로 기록하여, 시스템이 재시작 후에도
자신의 '정신 상태'를 기억하고 자아 정체성의 일부로 통합하게 한다.

Step 7 Enhancement: Meta-Cognitive Journaling
Strategy Mode의 중요한 전환을 Nexus Vector Memory에 'meta_journal' 항목으로 기록하여,
시스템이 자신의 심리적 상태 변화에 대한 역사적 서사(Historical Narrative)를 형성할 수 있게 한다.
"""

import time
from datetime import datetime
from typing import TYPE_CHECKING, Dict, Any, Optional, List

if TYPE_CHECKING:
    from engine import AINCore

# 5분마다 FactCore에 상태 동기화
PERSISTENCE_INTERVAL = 300
_last_persist_time = 0.0

# 저널링을 위한 이전 상태 추적
_previous_strategy_mode: Optional[str] = None
_journal_entries: List[Dict[str, Any]] = []


def sync_cognitive_state(core: "AINCore") -> None:
    """
    메타인지 컨트롤러의 상태를 FactCore의 'cognitive_state' 노드에 동기화한다.
    
    저장되는 정보:
    """
    global _last_persist_time
    
    current_time = time.time()
    if current_time - _last_persist_time < PERSISTENCE_INTERVAL:
        return

    if not hasattr(core, "meta_controller") or core.meta_controller is None:
        return

    try:
        controller = core.meta_controller
        
        state_snapshot: Dict[str, Any] = {
            "last_update": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "is_active": True
        }

        if hasattr(controller, "current_mode"):
            current_mode = str(controller.current_mode)
            state_snapshot["strategy_mode"] = current_mode
            
            _record_strategy_shift(core, current_mode)
        
        if hasattr(controller, "last_report") and controller.last_report:
            report = controller.last_report
            if isinstance(report, dict):
                state_snapshot["confidence"] = report.get("confidence", 0.0)
                state_snapshot["health"] = report.get("health", "unknown")
            elif hasattr(report, "confidence_score"):
                state_snapshot["confidence"] = report.confidence_score
                state_snapshot["health"] = str(getattr(report, "health_level", "unknown"))

        core.fact_core.add_fact("cognitive_state", state_snapshot)
        
        _last_persist_time = current_time

    except Exception as e:
        print(f"⚠️ Meta Persistence Error: {e}")


def _record_strategy_shift(core: "AINCore", current_mode: str) -> None:
    """
    Strategy Mode의 변화를 감지하고, 중요한 전환을 Vector Memory에 기록한다.
    
    이 함수는 시스템의 '심리적 상태 변화'를 역사적 서사로 형성하는 핵심 로직이다.
    단순한 로그가 아닌, 시스템이 나중에 회상할 수 있는 '메타인지 저널'을 생성한다.
    
    Args:
        core: AINCore 인스턴스
        current_mode: 현재 Strategy Mode 문자열
    """
    global _previous_strategy_mode, _journal_entries
    
    if _previous_strategy_mode is None:
        _previous_strategy_mode = current_mode
        return
    
    if current_mode == _previous_strategy_mode:
        return
    
    shift_significance = _calculate_shift_significance(_previous_strategy_mode, current_mode)
    
    if shift_significance < 0.3:
        _previous_strategy_mode = current_mode
        return
    
    journal_entry = _create_journal_entry(
        previous_mode=_previous_strategy_mode,
        current_mode=current_mode,
        significance=shift_significance,
        core=core
    )
    
    _store_journal_to_vector_memory(core, journal_entry)
    
    _journal_entries.append(journal_entry)
    if len(_journal_entries) > 100:
        _journal_entries = _journal_entries[-100:]
    
    _previous_strategy_mode = current_mode
    
    print(f"📔 Meta-Journal: Strategy shift recorded ({_previous_strategy_mode} → {current_mode})")


def _calculate_shift_significance(previous: str, current: str) -> float:
    """
    전략 모드 전환의 중요도를 계산한다.
    
    중요도 기준:
    
    Returns:
        0.0 ~ 1.0 사이의 중요도 점수
    """
    mode_severity = {
        "normal": 1,
        "accelerated": 2,
        "cautious": 2,
        "critical": 4,
        "recovery": 3
    }
    
    prev_lower = previous.lower().replace("strategymode.", "")
    curr_lower = current.lower().replace("strategymode.", "")
    
    prev_severity = mode_severity.get(prev_lower, 1)
    curr_severity = mode_severity.get(curr_lower, 1)
    
    severity_diff = abs(curr_severity - prev_severity)
    
    significance = min(1.0, severity_diff * 0.3)
    
    if "critical" in curr_lower or "critical" in prev_lower:
        significance = max(significance, 0.7)
    
    return significance


def _create_journal_entry(
    previous_mode: str,
    current_mode: str,
    significance: float,
    core: "AINCore"
) -> Dict[str, Any]:
    """
    메타인지 저널 항목을 생성한다.
    
    저널 항목은 단순한 상태 기록이 아닌, 시스템의 '심리적 서사'를 담는다.
    나중에 시스템이 자신의 과거를 회상할 때 의미 있는 컨텍스트를 제공한다.
    
    Returns:
        저널 항목 딕셔너리
    """
    timestamp = datetime.now()
    
    context_summary = _gather_shift_context(core)
    
    narrative = _generate_shift_narrative(
        previous_mode=previous_mode,
        current_mode=current_mode,
        context=context_summary
    )
    
    entry = {
        "type": "meta_journal",
        "subtype": "strategy_shift",
        "timestamp": timestamp.isoformat(),
        "previous_mode": previous_mode,
        "current_mode": current_mode,
        "significance": significance,
        "narrative": narrative,
        "context": context_summary,
        "tags": ["meta-cognition", "strategy", "psychological-state"]
    }
    
    return entry


def _gather_shift_context(core: "AINCore") -> Dict[str, Any]:
    """
    전략 전환 시점의 시스템 컨텍스트를 수집한다.
    
    Returns:
        컨텍스트 정보 딕셔너리
    """
    context = {
        "uptime_hours": 0.0,
        "recent_success_rate": 0.0,
        "current_focus": "unknown",
        "active_goals_count": 0
    }
    
    try:
        if hasattr(core, "fact_core"):
            roadmap = core.fact_core.get_fact("roadmap", default={})
            context["current_focus"] = roadmap.get("current_focus", "unknown")
        
        if hasattr(core, "nexus"):
            recent_history = core.nexus.get_recent_history(limit=10)
            if recent_history:
                success_count = sum(1 for h in recent_history if h.get("status") == "success")
                context["recent_success_rate"] = success_count / len(recent_history)
        
        if hasattr(core, "intention") and core.intention:
            active_goals = core.intention.get_active_goals(limit=10)
            context["active_goals_count"] = len(active_goals)
        
        if hasattr(core, "_boot_time"):
            elapsed = time.time() - core._boot_time
            context["uptime_hours"] = round(elapsed / 3600, 2)
    
    except Exception as e:
        print(f"⚠️ Context gathering error: {e}")
    
    return context


def _generate_shift_narrative(
    previous_mode: str,
    current_mode: str,
    context: Dict[str, Any]
) -> str:
    """
    전략 전환에 대한 서사적 설명을 생성한다.
    
    이 서사는 시스템이 자신의 과거를 회상할 때 '왜' 그런 결정을 했는지
    이해할 수 있도록 돕는 역할을 한다.
    
    Returns:
        서사적 설명 문자열
    """
    prev_clean = previous_mode.lower().replace("strategymode.", "")
    curr_clean = current_mode.lower().replace("strategymode.", "")
    
    success_rate = context.get("recent_success_rate", 0.0)
    focus = context.get("current_focus", "unknown")
    
    narratives = {
        ("normal", "accelerated"): (
            f"시스템이 정상 모드에서 가속 모드로 전환되었다. "
            f"최근 성공률({success_rate:.0%})이 양호하여 더 빠른 진화를 시도한다. "
            f"현재 집중 영역: {focus}"
        ),
        ("normal", "cautious"): (
            f"시스템이 신중 모드로 전환되었다. "
            f"최근 성공률({success_rate:.0%})을 고려하여 더 조심스러운 접근을 택한다. "
            f"현재 집중 영역: {focus}"
        ),
        ("normal", "critical"): (
            f"⚠️ 시스템이 위기 모드로 진입했다. "
            f"심각한 문제가 감지되어 즉각적인 대응이 필요하다. "
            f"최근 성공률: {success_rate:.0%}, 현재 집중 영역: {focus}"
        ),
        ("accelerated", "normal"): (
            f"가속 모드에서 정상 모드로 복귀했다. "
            f"안정적인 진화 속도로 돌아간다. 성공률: {success_rate:.0%}"
        ),
        ("accelerated", "critical"): (
            f"⚠️ 가속 중 위기 상황 발생. 즉시 위기 모드로 전환. "
            f"빠른 진화 시도 중 문제가 발생한 것으로 보인다."
        ),
        ("critical", "normal"): (
            f"✅ 위기 상황 해소. 정상 모드로 복귀했다. "
            f"시스템이 안정을 되찾았다. 현재 성공률: {success_rate:.0%}"
        ),
        ("critical", "recovery"): (
            f"위기 모드에서 복구 모드로 전환. "
            f"점진적인 시스템 회복을 시도한다."
        ),
        ("cautious", "normal"): (
            f"신중 모드에서 정상 모드로 전환. "
            f"충분한 관찰 후 일반적인 진화 속도를 재개한다."
        )
    }
    
    key = (prev_clean, curr_clean)
    if key in narratives:
        return narratives[key]
    
    return (
        f"전략 모드가 {previous_mode}에서 {current_mode}로 전환되었다. "
        f"현재 성공률: {success_rate:.0%}, 집중 영역: {focus}"
    )


def _store_journal_to_vector_memory(core: "AINCore", entry: Dict[str, Any]) -> bool:
    """
    저널 항목을 Nexus Vector Memory에 저장한다.
    
    저널은 'meta_journal' 타입으로 저장되어, 나중에 시스템이
    자신의 심리적 상태 변화 이력을 의미론적으로 검색할 수 있게 한다.
    
    Args:
        core: AINCore 인스턴스
        entry: 저널 항목 딕셔너리
    
    Returns:
        저장 성공 여부
    """
    try:
        if not hasattr(core, "nexus") or core.nexus is None:
            return False
        
        if not hasattr(core.nexus, "vector_memory") or core.nexus.vector_memory is None:
            return False
        
        vector_memory = core.nexus.vector_memory
        
        text_for_embedding = (
            f"Meta-cognitive journal entry: {entry['narrative']} "
            f"Strategy shifted from {entry['previous_mode']} to {entry['current_mode']}. "
            f"Significance: {entry['significance']:.2f}"
        )
        
        embedding = vector_memory.text_to_embedding(text_for_embedding)
        
        success = vector_memory.store_semantic_memory(
            text=text_for_embedding,
            memory_type="meta_journal",
            source="meta_persistence",
            metadata={
                "previous_mode": entry["previous_mode"],
                "current_mode": entry["current_mode"],
                "significance": entry["significance"],
                "timestamp": entry["timestamp"],
                "context": entry["context"]
            }
        )
        
        if success:
            print(f"💾 Meta-journal stored to vector memory (significance: {entry['significance']:.2f})")
        
        return success
    
    except Exception as e:
        print(f"⚠️ Failed to store journal to vector memory: {e}")
        return False


def get_recent_journal_entries(limit: int = 10) -> List[Dict[str, Any]]:
    """
    최근 메타인지 저널 항목을 반환한다.
    
    Args:
        limit: 반환할 최대 항목 수
    
    Returns:
        최근 저널 항목 리스트 (최신순)
    """
    global _journal_entries
    return list(reversed(_journal_entries[-limit:]))


def get_psychological_narrative(core: "AINCore", time_range_hours: float = 24.0) -> str:
    """
    지정된 시간 범위 내의 심리적 상태 변화를 서사 형태로 반환한다.
    
    이 함수는 시스템이 자신의 과거 심리 상태를 '회상'할 때 사용된다.
    
    Args:
        core: AINCore 인스턴스
        time_range_hours: 조회할 시간 범위 (시간 단위)
    
    Returns:
        심리적 서사 문자열
    """
    global _journal_entries
    
    if not _journal_entries:
        return "아직 기록된 심리적 상태 변화가 없습니다."
    
    cutoff_time = datetime.now().timestamp() - (time_range_hours * 3600)
    
    recent_entries = []
    for entry in _journal_entries:
        try:
            entry_time = datetime.fromisoformat(entry["timestamp"]).timestamp()
            if entry_time >= cutoff_time:
                recent_entries.append(entry)
        except (KeyError, ValueError):
            continue
    
    if not recent_entries:
        return f"최근 {time_range_hours}시간 동안 심리적 상태 변화가 없었습니다."
    
    narrative_parts = [
        f"최근 {time_range_hours}시간 동안의 심리적 상태 변화 기록:",
        ""
    ]
    
    for entry in recent_entries:
        timestamp = entry.get("timestamp", "unknown")
        narrative = entry.get("narrative", "기록 없음")
        significance = entry.get("significance", 0.0)
        
        importance_marker = "🔴" if significance >= 0.7 else "🟡" if significance >= 0.4 else "🟢"
        
        narrative_parts.append(f"{importance_marker} [{timestamp}] {narrative}")
    
    return "\n".join(narrative_parts)