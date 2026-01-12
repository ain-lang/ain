"""
🛡️ AIN Code Sanitizer - Coder 출력 후처리 모듈

이 파일은 .ainprotect에 등록되어 AIN이 수정할 수 없습니다.
Coder(LLM)가 생성한 코드에서 오류 패턴을 감지하고 정리합니다.

주요 기능:
1. Git 충돌 마커 자동 제거 (<<<<<<<, =======, >>>>>>>)
2. Diff 형식 감지 (+ / - 로 시작하는 줄)
3. 코드 생략 패턴 감지 (# ... existing 등)
4. 코드 블록 포맷 정규화 (''' → ```)
"""

import re
from typing import Tuple, List


# ═══════════════════════════════════════════════════════════════════════════
# 📌 상수 정의 - 감지 패턴
# ═══════════════════════════════════════════════════════════════════════════

# Git 충돌 마커
CONFLICT_MARKERS = ['<<<<<<<', '>>>>>>>']

# 코드 생략 패턴 (정교하게 설계 - 일반 주석과 구분)
OMISSION_PATTERNS = [
    r'#\s*\.\.\.\s*existing',      # # ... existing
    r'#\s*\.\.\.\s*rest',          # # ... rest of
    r'#\s*\.\.\.\s*same',          # # ... same as
    r'#\s*\.\.\.\s*unchanged',     # # ... unchanged
    r'#\s*keep\s+existing',        # # keep existing
    r'#\s*unchanged\s+from',       # # unchanged from
    r'#\s*omitted',                # # omitted
    r'#\s*truncated',              # # truncated
]


# ═══════════════════════════════════════════════════════════════════════════
# 🔧 메인 함수 - 코드 정리
# ═══════════════════════════════════════════════════════════════════════════

def sanitize_code_output(code_output: str, verbose: bool = True) -> Tuple[str, dict]:
    """
    Coder 출력물을 정리하고 문제점을 감지합니다.
    
    Args:
        code_output: Coder(LLM)가 생성한 원본 코드 문자열
        verbose: True면 콘솔에 로그 출력
    
    Returns:
        Tuple[str, dict]: (정리된 코드, 감지 결과)
        감지 결과 예시: {
            "cleaned": True,  # 정리가 수행되었는지
            "has_conflict": False,  # 충돌 마커 남아있는지
            "has_diff": False,  # diff 형식인지
            "has_omission": False,  # 생략 패턴 있는지
            "diff_count": 0,  # diff 줄 수
            "removed_lines": 5,  # 제거된 줄 수
        }
    """
    result = {
        "cleaned": False,
        "has_conflict": False,
        "has_diff": False,
        "has_omission": False,
        "diff_count": 0,
        "removed_lines": 0,
    }
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step 1: 코드 블록 마커 정규화 (''' → ```)
    # ─────────────────────────────────────────────────────────────────────────
    if "'''" in code_output:
        code_output = code_output.replace("'''", "```")
        result["cleaned"] = True
        if verbose:
            print("🔧 [Sanitizer] '''를 ```로 자동 치환함")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step 2: Git 충돌 마커 자동 제거
    # ─────────────────────────────────────────────────────────────────────────
    lines = code_output.split('\n')
    cleaned_lines = []
    
    for line in lines:
        stripped = line.strip()
        
        # 충돌 시작/끝 마커 건너뛰기
        if stripped.startswith('<<<<<<<') or stripped.startswith('>>>>>>>'):
            if verbose:
                print(f"🔧 [Sanitizer] 충돌 마커 제거: {stripped[:40]}...")
            result["removed_lines"] += 1
            continue
        
        # ======= 구분선 건너뛰기
        if stripped == '=======' or stripped.startswith('======='):
            if verbose:
                print("🔧 [Sanitizer] 충돌 구분선 제거")
            result["removed_lines"] += 1
            continue
        
        cleaned_lines.append(line)
    
    if result["removed_lines"] > 0:
        code_output = '\n'.join(cleaned_lines)
        result["cleaned"] = True
        if verbose:
            print(f"🔧 [Sanitizer] 충돌 마커 제거 완료: {len(lines)} -> {len(cleaned_lines)} 줄")
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step 3: 잔여 충돌 마커 감지
    # ─────────────────────────────────────────────────────────────────────────
    result["has_conflict"] = any(marker in code_output for marker in CONFLICT_MARKERS)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step 4: Diff 형식 감지
    # ─────────────────────────────────────────────────────────────────────────
    current_lines = code_output.split('\n')
    diff_indicators = [
        l for l in current_lines 
        if l.strip().startswith('+ ') or l.strip().startswith('- ')
    ]
    result["diff_count"] = len(diff_indicators)
    result["has_diff"] = len(diff_indicators) > 3 or '@@ ' in code_output
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step 5: 생략 패턴 감지
    # ─────────────────────────────────────────────────────────────────────────
    result["has_omission"] = any(
        re.search(p, code_output, re.IGNORECASE) 
        for p in OMISSION_PATTERNS
    )
    
    return code_output, result


def get_error_message(result: dict) -> str:
    """
    감지 결과를 기반으로 에러 메시지를 생성합니다.
    
    Args:
        result: sanitize_code_output의 반환값 중 감지 결과 dict
    
    Returns:
        str: 에러 메시지 (문제 없으면 빈 문자열)
    """
    if result["has_conflict"] or result["has_diff"]:
        return (
            f"Git 충돌 마커 또는 diff 형식(+/-)이 감지됨. "
            f"diff: {result['diff_count']}줄, conflict: {result['has_conflict']}. "
            "절대 diff 형식을 사용하지 말고 전체 파일을 새로 작성하라."
        )
    
    if result["has_omission"]:
        return (
            "코드 생략 패턴(# ... existing 등)이 감지됨. "
            "생략하지 말고 전체 코드를 작성하라."
        )
    
    return ""  # 문제 없음


def is_valid_output(result: dict) -> bool:
    """
    감지 결과가 유효한지 확인합니다.
    
    Args:
        result: sanitize_code_output의 반환값 중 감지 결과 dict
    
    Returns:
        bool: 유효하면 True, 문제 있으면 False
    """
    return not (result["has_conflict"] or result["has_diff"] or result["has_omission"])
