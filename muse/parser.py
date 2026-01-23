"""
Muse 파서
- Coder 출력에서 파일 섹션 파싱
- 보호된 파일 필터링
"""

import os
import re
from typing import List, Dict, Any, Optional

from utils.file_size_guard import validate_coder_output, get_rejection_message


# 최소 보호 파일 목록
PROTECTED_FILES = frozenset([
    "main.py", "api/keys.py", "api/github.py", ".ainprotect",
    "docs/hardware-catalog.md"
])


def parse_coder_output(
    code_output: str,
    intent: str
) -> Dict[str, Any]:
    """
    Coder 출력을 파싱하여 업데이트 목록 반환

    Returns:
        {
            "updates": List[Dict],
            "error": Optional[str],
            "no_evolution": bool
        }
    """
    # 무의미한 진화 시도 차단
    if "NO_EVOLUTION_NEEDED" in code_output:
        reason = code_output.split("NO_EVOLUTION_NEEDED:")[-1].strip()
        print(f"😴 [Muse] 진화 불필요 판단: {reason}")
        return {"updates": [], "no_evolution": True, "reason": reason}

    updates = []

    # FILE: 마커로 분할
    file_sections = re.split(r'(?i)(?:\n|^)[#\*\[ ]*FILE[ :\]]*\s*', code_output)
    if len(file_sections) > 1:
        file_sections = file_sections[1:]
    else:
        file_sections = []

    if not file_sections:
        # FILE: 마커가 없으면 대체 패턴 시도
        print("⚠️ [Muse] FILE: 마커 없음, 대체 패턴 시도...")
        updates = _try_alternative_patterns(code_output)

    for section in file_sections:
        parsed = _parse_file_section(section)
        if parsed:
            updates.append(parsed)

    if not updates:
        # 마지막 시도: 전체 응답에서 첫 번째 코드 블록 추출
        result = _try_last_resort_extraction(code_output, intent)
        if result.get("updates"):
            return result
        elif result.get("error"):
            return result

        sample = code_output[:500]
        return {
            "updates": [],
            "error": f"Coder가 규격에 맞는 코드를 생성하지 못했습니다.\n\n[응답 샘플 (처음 500자)]\n{sample}"
        }

    # 파일 보호 검증
    valid_updates, warnings, blocked = validate_coder_output(updates)

    if blocked:
        rejection_msg = get_rejection_message(blocked)
        print(f"🚫 [Muse] 절대 보호 파일 수정 차단:\n{rejection_msg}")
        if not valid_updates:
            return {
                "updates": [],
                "error": f"절대 보호 파일 수정 시도.\n{rejection_msg}"
            }

    if warnings:
        for w in warnings:
            print(f"⚠️ [Muse] 대형 파일 경고: {w['filename']} ({w['line_count']}줄 → {w['new_line_count']}줄)")

    return {"updates": valid_updates}


def _parse_file_section(section: str) -> Optional[Dict[str, str]]:
    """단일 파일 섹션 파싱"""
    lines = section.split('\n')
    if not lines:
        return None

    # 파일명 추출 및 정규화
    raw_filename = lines[0].strip()
    filename = raw_filename.replace('*', '').replace('`', '').replace('"', '').replace("'", '').strip()
    filename = filename.lstrip('./')

    if not filename or '.' not in filename:
        print(f"⚠️ [Muse] 유효하지 않은 파일명: '{raw_filename}'")
        return None

    # 보호된 파일 확인
    if filename in PROTECTED_FILES or os.path.basename(filename) in ["main.py", ".ainprotect"]:
        print(f"🛡️ [Muse] 보호된 파일 건너뜀: {filename}")
        return None

    # 마크다운 코드 블록 추출
    code_match = re.search(r'(?:```|\'\'\')(?:\w+)?\s*(.*?)\s*(?:```|\'\'\')', section, re.DOTALL)
    if code_match:
        code_content = code_match.group(1).strip()
        if filename and code_content and len(code_content) > 10:
            print(f"📦 [Muse] 파싱 성공: {filename} ({len(code_content)} bytes)")
            return {"filename": filename, "code": code_content}
        else:
            print(f"⚠️ [Muse] 코드가 너무 짧음: {filename} ({len(code_content) if code_content else 0} bytes)")
    else:
        print(f"⚠️ [Muse] 코드 블록 없음: {filename}")

    return None


def _try_alternative_patterns(code_output: str) -> List[Dict[str, str]]:
    """대체 패턴으로 파싱 시도"""
    updates = []

    # 패턴 1: ```python:filename.py 형식
    alt_pattern = re.findall(
        r'(?:```|\'\'\')(?:python|py)?:?\s*(\S+\.py)\s*\n(.*?)(?:```|\'\'\')',
        code_output, re.DOTALL
    )
    for filename, code in alt_pattern:
        filename = filename.strip().lstrip('./')
        if filename not in PROTECTED_FILES:
            updates.append({"filename": filename, "code": code.strip()})
            print(f"📦 [Muse] 대체 파싱 1 성공: {filename}")

    # 패턴 2: 파일명 + 코드블록
    if not updates:
        alt_pattern2 = re.findall(
            r'(?:\n|^)([a-zA-Z0-9_/]+\.py)\s*\n\s*(?:```|\'\'\')(?:python|py)?\n(.*?)(?:```|\'\'\')',
            code_output, re.DOTALL
        )
        for filename, code in alt_pattern2:
            filename = filename.strip().lstrip('./')
            if filename not in PROTECTED_FILES:
                updates.append({"filename": filename, "code": code.strip()})
                print(f"📦 [Muse] 대체 파싱 2 성공: {filename}")

    return updates


def _try_last_resort_extraction(code_output: str, intent: str) -> Dict[str, Any]:
    """마지막 시도: 코드 블록 + 의도에서 파일명 추론"""
    last_resort = re.search(r'```(?:python|py)?\s*(.*?)```', code_output, re.DOTALL)

    if last_resort:
        fallback_code = last_resort.group(1).strip()
        code_len = len(fallback_code)

        # 50자 이상이면 파일명 추론 시도 (기존 100자에서 완화)
        if code_len >= 50:
            file_hint = re.search(r'([\w/]+\.py)', intent)

            if file_hint:
                fallback_filename = file_hint.group(1)
                print(f"🔄 [Muse] 마지막 시도: {fallback_filename}로 코드 추출 ({code_len} bytes)")
                return {"updates": [{"filename": fallback_filename, "code": fallback_code}]}
            else:
                print("⚠️ [Muse] 파일명 추론 실패, 진화 스킵")
                return {"updates": [], "error": "파일명 추론 실패"}
        else:
            # 코드 블록은 있지만 너무 짧음
            print(f"⚠️ [Muse] 코드 블록이 너무 짧음 ({code_len}자 < 50자)")
            return {"updates": [], "error": f"코드 블록이 너무 짧음 ({code_len}자)"}

    # 코드 블록 자체가 없음 - 빈 dict 대신 에러 반환
    print("⚠️ [Muse] 코드 블록(```)을 찾을 수 없음")
    return {"updates": [], "error": "코드 블록(```)을 찾을 수 없음"}
