"""
Goal Generator: 목표 생성 유틸리티
- Dreamer를 통한 목표 생성
- 프롬프트 구성 및 응답 파싱
"""

import json
from typing import List, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from . import AINCore


def build_goal_generation_prompt(current_focus: str) -> str:
    """목표 생성을 위한 프롬프트를 구성한다."""
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


def parse_goal_response(response: str) -> List[Dict[str, Any]]:
    """Dreamer 응답에서 목표 JSON을 파싱한다."""
    if not response:
        return []

    try:
        start_idx = response.find("[")
        end_idx = response.rfind("]")

        if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
            json_str = response[start_idx:end_idx + 1]
            goals = json.loads(json_str)

            if isinstance(goals, list):
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


def generate_default_goals(current_focus: str) -> List[Dict[str, Any]]:
    """Muse 응답 실패 시 기본 목표를 생성한다."""
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


async def dream_new_goals(core: "AINCore", current_focus: str) -> List[Dict[str, Any]]:
    """Muse(Dreamer)에게 새로운 목표 생성을 요청한다."""
    if not hasattr(core, "muse"):
        print("⚠️ Muse 인스턴스 없음. 기본 목표 생성.")
        return generate_default_goals(current_focus)

    prompt = build_goal_generation_prompt(current_focus)

    try:
        response = core.muse._ask_dreamer(prompt)

        if not response:
            return generate_default_goals(current_focus)

        goals = parse_goal_response(response)

        if goals:
            return goals
        else:
            return generate_default_goals(current_focus)

    except Exception as e:
        print(f"⚠️ 목표 생성 중 오류: {e}")
        return generate_default_goals(current_focus)
