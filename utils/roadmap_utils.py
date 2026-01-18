"""
Roadmap 유틸리티 - 중첩 구조 탐색 (수정 금지)
==============================================
fact_core.json의 roadmap은 phase > step 중첩 구조.
이 모듈은 current_focus에서 step 정보를 올바르게 찾는다.

문제 배경:
- roadmap.get("step_7_meta_cognition") → {} (빈 딕셔너리)
- 실제 위치: roadmap["phase_3_awakening"]["step_7_meta_cognition"]
"""

from typing import Dict, Any, Optional


def find_step_info(roadmap: Dict[str, Any], step_key: str) -> Dict[str, Any]:
    """
    roadmap 중첩 구조에서 step 정보를 찾는다.

    Args:
        roadmap: fact_core.json의 roadmap 딕셔너리
        step_key: 찾을 step 키 (예: "step_7_meta_cognition")

    Returns:
        step 정보 딕셔너리. 못 찾으면 빈 딕셔너리.
    """
    if not roadmap or not step_key:
        return {}

    # 1. 직접 키로 존재하는지 확인
    if step_key in roadmap and isinstance(roadmap[step_key], dict):
        return roadmap[step_key]

    # 2. phase 안에서 찾기
    for phase_key, phase_data in roadmap.items():
        if not isinstance(phase_data, dict):
            continue
        if phase_key.startswith("phase_") and step_key in phase_data:
            return phase_data[step_key]

    return {}


def get_step_context(roadmap: Dict[str, Any], current_focus: str) -> Dict[str, Any]:
    """
    독백/진화에서 사용할 step 컨텍스트를 반환한다.

    Args:
        roadmap: fact_core.json의 roadmap 딕셔너리
        current_focus: 현재 focus step 키

    Returns:
        {
            "current_focus": str,
            "step_name": str,
            "step_desc": str,
            "status": str,
            "phase": str
        }
    """
    result = {
        "current_focus": current_focus or "unknown",
        "step_name": "Unknown",
        "step_desc": "",
        "status": "unknown",
        "phase": "unknown"
    }

    if not roadmap or not current_focus:
        return result

    # phase 이름 찾기 + step 정보 찾기
    for phase_key, phase_data in roadmap.items():
        if not isinstance(phase_data, dict):
            continue
        if phase_key.startswith("phase_") and current_focus in phase_data:
            step_info = phase_data[current_focus]
            result["phase"] = phase_key
            result["step_name"] = step_info.get("name", _format_step_name(current_focus))
            result["step_desc"] = step_info.get("desc", "")
            result["status"] = step_info.get("status", "unknown")
            break

    return result


def _format_step_name(step_key: str) -> str:
    """
    step 키에서 사람이 읽을 수 있는 이름 생성.
    예: "step_7_meta_cognition" → "Step 7: Meta Cognition"
    """
    if not step_key:
        return "Unknown"

    # step_7_meta_cognition → ["step", "7", "meta", "cognition"]
    parts = step_key.split("_")
    if len(parts) < 2:
        return step_key.replace("_", " ").title()

    # step 번호 추출
    step_num = parts[1] if parts[1].isdigit() else ""
    # 나머지 부분을 이름으로
    name_parts = parts[2:] if len(parts) > 2 else []
    name = " ".join(p.title() for p in name_parts)

    if step_num and name:
        return f"Step {step_num}: {name}"
    elif step_num:
        return f"Step {step_num}"
    else:
        return name or step_key
