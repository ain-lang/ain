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

# Git 충돌 마커 (모든 마커 포함)
CONFLICT_MARKERS = ['<<<<<<<', '=======', '>>>>>>>']

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
    # Step 2: Git 충돌 마커 자동 제거 (더 포괄적인 검사)
    # ─────────────────────────────────────────────────────────────────────────
    lines = code_output.split('\n')
    cleaned_lines = []
    
    for line in lines:
        stripped = line.strip()
        should_remove = False
        
        # 충돌 시작/끝 마커 건너뛰기 (줄 어디에 있든)
        if '<<<<<<<' in line or '>>>>>>>' in line:
            if verbose:
                print(f"🔧 [Sanitizer] 충돌 마커 제거: {stripped[:40]}...")
            result["removed_lines"] += 1
            should_remove = True
        
        # ======= 구분선 건너뛰기 (정확히 7개의 = 또는 그 이상)
        elif '=======' in stripped and stripped.replace('=', '').strip() == '':
            if verbose:
                print("🔧 [Sanitizer] 충돌 구분선 제거")
            result["removed_lines"] += 1
            should_remove = True
        
        # 줄 전체가 충돌 마커인 경우
        elif stripped in ['<<<<<<<', '=======', '>>>>>>>']:
            if verbose:
                print(f"🔧 [Sanitizer] 순수 충돌 마커 제거: {stripped}")
            result["removed_lines"] += 1
            should_remove = True
        
        if not should_remove:
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
    # Step 4: Diff 형식 감지 및 자동 변환
    # ─────────────────────────────────────────────────────────────────────────
    current_lines = code_output.split('\n')
    diff_indicators = [
        l for l in current_lines 
        if l.strip().startswith('+ ') or l.strip().startswith('- ')
    ]
    result["diff_count"] = len(diff_indicators)
    has_diff_format = len(diff_indicators) >= 1 or '@@ ' in code_output
    
    # 🔧 Diff 형식 자동 변환 (코드 블록 내부에서만)
    if has_diff_format:
        converted_lines = []
        in_code_block = False
        diff_converted = 0
        diff_removed = 0
        
        for line in current_lines:
            # 코드 블록 시작/끝 감지
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                converted_lines.append(line)
                continue
            
            # 코드 블록 내부에서만 diff 변환
            if in_code_block:
                # @@ 마커 제거
                if line.strip().startswith('@@') and '@@' in line[2:]:
                    diff_removed += 1
                    continue
                
                # + 로 시작하는 줄: prefix 제거하고 추가
                if line.startswith('+ ') or line.startswith('+\t'):
                    converted_lines.append(line[1:])  # '+' 제거, 공백/탭 유지
                    diff_converted += 1
                    continue
                elif line == '+':  # 빈 줄 추가
                    converted_lines.append('')
                    diff_converted += 1
                    continue
                
                # - 로 시작하는 줄: 삭제된 줄이므로 제거
                if line.startswith('- ') or line.startswith('-\t') or line == '-':
                    diff_removed += 1
                    continue
                
                # 일반 줄 (컨텍스트)
                converted_lines.append(line)
            else:
                converted_lines.append(line)
        
        if diff_converted > 0 or diff_removed > 0:
            code_output = '\n'.join(converted_lines)
            result["cleaned"] = True
            result["diff_converted"] = diff_converted
            result["diff_removed"] = diff_removed
            if verbose:
                print(f"🔧 [Sanitizer] Diff 형식 자동 변환: +{diff_converted}줄 변환, -{diff_removed}줄 제거")
    
    # 변환 후 다시 감지
    final_lines = code_output.split('\n')
    remaining_diff = [
        l for l in final_lines 
        if l.strip().startswith('+ ') or l.strip().startswith('- ')
    ]
    result["has_diff"] = len(remaining_diff) >= 1 or '@@ ' in code_output
    
    # ─────────────────────────────────────────────────────────────────────────
    # Step 6: 구문 오류 자가 치유 (Unterminated String Literal 등)
    # ─────────────────────────────────────────────────────────────────────────
    # 따옴표 개수가 홀수면 닫아줌 (주로 docstring에서 발생)
    for quote_type in ['"""', "'''"]:
        count = code_output.count(quote_type)
        if count % 2 != 0:
            if verbose:
                print(f"🔧 [Sanitizer] 미종결 따옴표({quote_type}) 감지. 강제 종결 시도.")
            # 코드 마지막에 따옴표 추가
            if not code_output.endswith('\n'):
                code_output += '\n'
            code_output += quote_type
            result["cleaned"] = True

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
