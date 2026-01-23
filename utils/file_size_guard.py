# utils/file_size_guard.py
"""
파일 크기 보호 모듈 - 대형 파일 수정 시 컨텍스트 문제 방지

정책:
- 절대 보호: main.py, api/keys.py (수정 불가)
- 대형 파일: 경고 + 작은 변경만 허용 (컨텍스트 힌트 전달)
"""
import os

# 줄 수 기준 임계값
DEFAULT_THRESHOLD = 150  # 권장 최대 줄 수
HARD_LIMIT = 200  # 경고 발생 줄 수 (차단 아님)

# 절대 수정 금지 파일 (진화로도 수정 불가)
ABSOLUTELY_PROTECTED = frozenset([
    'main.py', 'api/keys.py', '.ainprotect'
])

# 대형 파일 (수정 가능하지만 경고 + 컨텍스트 힌트 필요)
LARGE_FILE_WARNING = frozenset([
    'overseer.py', 'muse.py'
])


def get_file_line_count(filepath: str) -> int:
    """파일의 줄 수를 반환. 파일이 없으면 0 반환."""
    if not os.path.exists(filepath):
        return 0
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except:
        return 0


def is_absolutely_protected(filepath: str) -> bool:
    """절대 수정 금지 파일인지 확인"""
    basename = os.path.basename(filepath.lstrip('./'))
    return filepath.lstrip('./') in ABSOLUTELY_PROTECTED or basename in ABSOLUTELY_PROTECTED


def is_large_file(filepath: str, threshold: int = DEFAULT_THRESHOLD) -> bool:
    """파일이 대형 파일인지 확인 (경고 대상)"""
    filepath = filepath.lstrip('./')
    basename = os.path.basename(filepath)

    # 알려진 대형 파일
    if basename in LARGE_FILE_WARNING:
        return True

    # 줄 수 체크
    line_count = get_file_line_count(filepath)
    return line_count > threshold


def check_file_size(filepath: str) -> dict:
    """
    파일 크기를 체크하고 결과 반환

    Returns:
        {
            'allowed': bool,          # 수정 허용 여부
            'warning': bool,          # 경고 필요 여부
            'line_count': int,
            'reason': str,
            'context_hint': str       # Coder에게 전달할 컨텍스트 힌트
        }
    """
    filepath = filepath.lstrip('./')
    basename = os.path.basename(filepath)
    line_count = get_file_line_count(filepath)

    # 절대 보호 파일
    if is_absolutely_protected(filepath):
        return {
            'allowed': False,
            'warning': False,
            'line_count': line_count,
            'reason': f'{filepath}는 절대 수정 금지 파일입니다',
            'context_hint': None
        }

    # 새 파일 (존재하지 않음)
    if line_count == 0 and not os.path.exists(filepath):
        return {
            'allowed': True,
            'warning': False,
            'line_count': 0,
            'reason': '새 파일 생성',
            'context_hint': None
        }

    # 대형 파일 (수정 허용하되 경고)
    if line_count > HARD_LIMIT or basename in LARGE_FILE_WARNING:
        context_hint = f"""
⚠️ 대형 파일 수정 주의 ({filepath}: {line_count}줄)
- 토큰 한계로 인해 전체 파일을 출력하면 코드가 잘릴 수 있음
- 반드시 **최소한의 변경만** 수행하라
- 가능하면 새 모듈 파일을 생성하고 import만 추가하라
- 불가피하게 수정해야 한다면:
  1. 변경할 부분만 명확히 지정
  2. 기존 코드 구조 유지
  3. 새 함수/클래스 추가는 별도 파일 권장
"""
        return {
            'allowed': True,
            'warning': True,
            'line_count': line_count,
            'reason': f'{filepath}는 {line_count}줄 대형 파일입니다 (주의 필요)',
            'context_hint': context_hint
        }

    # 권장 초과 (경고만)
    if line_count > DEFAULT_THRESHOLD:
        return {
            'allowed': True,
            'warning': True,
            'line_count': line_count,
            'reason': f'{filepath}는 {line_count}줄로 {DEFAULT_THRESHOLD}줄 권장 초과',
            'context_hint': f'⚠️ {filepath}는 {line_count}줄입니다. 가능하면 새 모듈로 분리를 고려하세요.'
        }

    return {
        'allowed': True,
        'warning': False,
        'line_count': line_count,
        'reason': 'OK',
        'context_hint': None
    }


def validate_coder_output(updates: list) -> tuple:
    """
    Coder의 출력(updates 리스트)을 검증

    Args:
        updates: [{'filename': str, 'code': str}, ...]

    Returns:
        (valid_updates, warnings, blocked_files)
        - valid_updates: 허용된 업데이트 (경고 포함)
        - warnings: 경고 메시지 리스트 (Coder에게 전달용)
        - blocked_files: 차단된 파일 정보 리스트
    """
    valid = []
    warnings = []
    blocked = []

    for update in updates:
        filename = update.get('filename', '').lstrip('./')
        code = update.get('code', '')
        new_line_count = code.count('\n') + 1

        result = check_file_size(filename)

        if not result['allowed']:
            # 절대 보호 파일 - 차단
            blocked.append({
                'filename': filename,
                'reason': result['reason']
            })
        else:
            # 허용 (경고 있을 수 있음)
            valid.append(update)

            if result['warning'] and result['context_hint']:
                warnings.append({
                    'filename': filename,
                    'hint': result['context_hint'],
                    'line_count': result['line_count'],
                    'new_line_count': new_line_count
                })

    return valid, warnings, blocked


def get_context_hints_for_coder(target_files: list) -> str:
    """
    Coder 프롬프트에 추가할 컨텍스트 힌트 생성

    Args:
        target_files: 수정 대상 파일 경로 리스트

    Returns:
        Coder에게 전달할 컨텍스트 힌트 문자열
    """
    hints = []
    for filepath in target_files:
        result = check_file_size(filepath)
        if result['warning'] and result['context_hint']:
            hints.append(result['context_hint'])

    if not hints:
        return ""

    return "\n[🚨 대형 파일 주의사항]\n" + "\n".join(hints)


def get_rejection_message(blocked_files: list) -> str:
    """차단된 파일들에 대한 에러 메시지 생성"""
    if not blocked_files:
        return ""

    lines = ["🚫 절대 보호 파일 수정 차단:"]
    for b in blocked_files:
        lines.append(f"  - {b['filename']}: {b['reason']}")

    return '\n'.join(lines)
