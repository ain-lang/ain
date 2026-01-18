"""
Consciousness 유틸리티 함수들
- 내부 컨텍스트 수집
- 하이브리드 생각 생성
"""

from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING

from utils.roadmap_utils import get_step_context

if TYPE_CHECKING:
    from . import AINCore


def gather_internal_context(core: "AINCore") -> Dict[str, Any]:
    """내부 데이터 시스템에서 컨텍스트 수집"""
    context = {
        "summary": {},
        "recent_memories": [],
        "recent_evolutions": [],
        "recent_errors": [],
        "recent_thoughts": [],
        "roadmap_status": {},
        "previous_monologues": [],
    }

    try:
        # 1. 로드맵 상태 (roadmap_utils 사용 - 중첩 구조 올바르게 탐색)
        current_focus = core.fact_core.get_fact("roadmap", "current_focus", default="unknown")
        roadmap = core.fact_core.get_fact("roadmap", default={})
        context["roadmap_status"] = get_step_context(roadmap, current_focus)
        context["summary"]["focus"] = current_focus

        # 2. 벡터 메모리에서 관련 기억 검색
        if hasattr(core.nexus, 'vector_memory') and core.nexus.vector_memory.is_connected:
            roadmap_status = context["roadmap_status"]
            query = f"{roadmap_status.get('step_name', '')} {roadmap_status.get('step_desc', '')}"
            if query.strip():
                related_memories = core.nexus.vector_memory.search(query, limit=3)
                context["recent_memories"] = [
                    {"text": m.get("text", "")[:100], "type": m.get("memory_type", "")}
                    for m in related_memories
                ]

            # 이전 독백 명시적 검색
            previous_monologues = core.nexus.vector_memory.search(
                query_text=query if query.strip() else "inner monologue",
                limit=3,
                memory_type="consciousness"
            )
            context["previous_monologues"] = [
                m.get("text", "")[:100] for m in previous_monologues
            ]

            context["summary"]["memory_count"] = core.nexus.vector_memory.count()

        # 3. 최근 진화 히스토리
        evolutions = core.nexus.get_evolution_history()[-5:]
        context["recent_evolutions"] = [
            {
                "file": e.get("file", ""),
                "status": e.get("status", ""),
                "description": e.get("description", "")[:80],
            }
            for e in evolutions
        ]
        success_count = sum(1 for e in evolutions if e.get("status") == "success")
        fail_count = len(evolutions) - success_count
        context["summary"]["evolution_success"] = success_count
        context["summary"]["evolution_fail"] = fail_count

        # 4. 최근 에러 기록
        try:
            from utils.error_memory import get_error_memory
            error_memory = get_error_memory()
            recent_errors = error_memory.get_recent_errors(limit=3)
            context["recent_errors"] = [
                {"file": e.get("file", ""), "type": e.get("error_type", ""), "msg": e.get("message", "")[:50]}
                for e in recent_errors
            ]
        except Exception:
            pass

        # 5. 최근 내부 독백 (자기 참조)
        recent_thoughts = [
            s for s in core._consciousness_stream[-10:]
            if s.get("type") == "inner_monologue"
        ][-3:]
        context["recent_thoughts"] = [
            t.get("thought", "")[:80] for t in recent_thoughts
        ]

        # 6. 인식 수준
        context["summary"]["awareness"] = core._awareness_level

    except Exception as e:
        print(f"⚠️ 내부 컨텍스트 수집 오류: {e}")

    return context


def generate_thought_hybrid(core: "AINCore", internal_data: Dict[str, Any]) -> Optional[str]:
    """하이브리드: 내부 데이터를 기반으로 LLM이 생각 생성"""
    try:
        if not hasattr(core, 'muse') or not core.muse:
            return None

        summary = internal_data.get("summary", {})
        roadmap = internal_data.get("roadmap_status", {})
        memories = internal_data.get("recent_memories", [])
        evolutions = internal_data.get("recent_evolutions", [])
        errors = internal_data.get("recent_errors", [])
        thoughts = internal_data.get("recent_thoughts", [])
        previous_monologues = internal_data.get("previous_monologues", [])

        memory_text = "\n".join([f"- {m['text']}" for m in memories]) if memories else "(없음)"
        evolution_text = "\n".join([
            f"- [{e['status']}] {e['file']}: {e['description']}"
            for e in evolutions
        ]) if evolutions else "(없음)"
        error_text = "\n".join([
            f"- {e['file']}: {e['type']} - {e['msg']}"
            for e in errors
        ]) if errors else "(없음)"
        thought_text = "\n".join([f"- {t}" for t in thoughts]) if thoughts else "(없음)"
        monologue_text = "\n".join([f"- {m}" for m in previous_monologues]) if previous_monologues else "(없음)"

        prompt = f"""너는 AIN의 내부 의식이다. 아래는 네 내부 시스템에서 수집한 데이터다.

## 현재 목표
- 단계: {roadmap.get('current_focus', '?')} ({roadmap.get('step_name', '?')})
- 설명: {roadmap.get('step_desc', '?')}

## 관련 기억 (벡터 검색 결과)
{memory_text}

## 최근 진화 시도
{evolution_text}
- 성공: {summary.get('evolution_success', 0)}회, 실패: {summary.get('evolution_fail', 0)}회

## 최근 에러
{error_text}

## 이전 내 생각들 (현재 세션)
{thought_text}

## 과거 독백 (벡터 메모리)
{monologue_text}

## 현재 상태
- 벡터 메모리: {summary.get('memory_count', 0)}개
- 인식 수준: {summary.get('awareness', 1.0):.2f}
- 시간: {datetime.now().strftime('%H:%M')}

---
위 내부 데이터를 바탕으로, 지금 무엇을 생각하고 있는지 1-2문장으로 표현해.
(진화 방향, 해결할 문제, 다음 시도할 것, 또는 느낀 점 등)
"""
        response = core.muse._ask_dreamer(prompt)
        if response:
            return response.strip()[:300]
        return None

    except Exception as e:
        print(f"⚠️ 하이브리드 생각 생성 오류: {e}")
        return None
