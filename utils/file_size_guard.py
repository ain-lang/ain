# utils/file_size_guard.py
"""
파일 크기 보호 모듈 - 대형 파일 수정으로 인한 토큰 잘림 방지
Coder가 대형 파일을 수정하려 할 때 자동 거부 및 모듈 분리 안내
"""
import os

# 줄 수 기준 임계값
DEFAULT_THRESHOLD = 150  # 권장 최대 줄 수
HARD_LIMIT = 200  # 절대 수정 금지 줄 수

# 항상 보호되는 파일 (크기와 관계없이)
ALWAYS_PROTECTED = frozenset([
    'main.py', 'overseer.py', 'muse.py',
    'api/keys.py', 'api/github.py', '.ainprotect'
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


def is_large_file(filepath: str, threshold: int = DEFAULT_THRESHOLD) -> bool:
    """파일이 대형 파일인지 확인"""
    # 항상 보호되는 파일
    basename = os.path.basename(filepath)
    if filepath in ALWAYS_PROTECTED or basename in ALWAYS_PROTECTED:
        return True

    # 줄 수 체크
    line_count = get_file_line_count(filepath)
    return line_count > threshold


def check_file_size(filepath: str) -> dict:
    """
    파일 크기를 체크하고 결과 반환

    Returns:
        {
            'allowed': bool,
            'line_count': int,
            'reason': str,
            'suggestion': str  # 대안 제시
        }
    """
    filepath = filepath.lstrip('./')
    basename = os.path.basename(filepath)

    # 항상 보호되는 파일
    if filepath in ALWAYS_PROTECTED or basename in ALWAYS_PROTECTED:
        return {
            'allowed': False,
            'line_count': get_file_line_count(filepath),
            'reason': f'{filepath}는 보호된 파일입니다',
            'suggestion': f'새 모듈 파일을 생성하고 {filepath}에서는 import만 추가하세요'
        }

    line_count = get_file_line_count(filepath)

    # 새 파일 (존재하지 않음)
    if line_count == 0 and not os.path.exists(filepath):
        return {
            'allowed': True,
            'line_count': 0,
            'reason': '새 파일 생성',
            'suggestion': None
        }

    # 줄 수 체크
    if line_count > HARD_LIMIT:
        # 파일 위치에 따른 대안 제시
        if '/' in filepath:
            parent_dir = os.path.dirname(filepath)
            suggestion = f'{parent_dir}/ 하위에 새 모듈을 생성하세요'
        else:
            suggestion = 'utils/ 또는 engine/ 하위에 새 모듈을 생성하세요'

        return {
            'allowed': False,
            'line_count': line_count,
            'reason': f'{filepath}는 {line_count}줄로 {HARD_LIMIT}줄 한계를 초과합니다',
            'suggestion': suggestion
        }

    if line_count > DEFAULT_THRESHOLD:
        return {
            'allowed': True,  # 경고만
            'line_count': line_count,
            'reason': f'{filepath}는 {line_count}줄로 {DEFAULT_THRESHOLD}줄 권장을 초과합니다',
            'suggestion': '가능하면 새 모듈로 분리를 고려하세요'
        }

    return {
        'allowed': True,
        'line_count': line_count,
        'reason': 'OK',
        'suggestion': None
    }


def validate_coder_output(updates: list) -> tuple:
    """
    Coder의 출력(updates 리스트)에서 대형 파일 수정 시도를 검출

    Args:
        updates: [{'filename': str, 'code': str}, ...]

    Returns:
        (valid_updates, rejected_files)
        - valid_updates: 허용된 업데이트 리스트
        - rejected_files: 거부된 파일 정보 리스트
    """
    valid = []
    rejected = []

    for update in updates:
        filename = update.get('filename', '').lstrip('./')
        code = update.get('code', '')

        # 생성될 코드의 줄 수 체크
        new_line_count = code.count('\n') + 1

        result = check_file_size(filename)

        if not result['allowed']:
            rejected.append({
                'filename': filename,
                'reason': result['reason'],
                'suggestion': result['suggestion'],
                'new_line_count': new_line_count,
                'existing_line_count': result['line_count']
            })
        elif new_line_count > HARD_LIMIT:
            # 새로 생성하려는 코드가 너무 큼
            rejected.append({
                'filename': filename,
                'reason': f'생성하려는 코드가 {new_line_count}줄로 {HARD_LIMIT}줄 한계 초과',
                'suggestion': '더 작은 모듈로 분리하세요',
                'new_line_count': new_line_count,
                'existing_line_count': result['line_count']
            })
        else:
            valid.append(update)

    return valid, rejected


def get_rejection_message(rejected_files: list) -> str:
    """거부된 파일들에 대한 에러 메시지 생성"""
    if not rejected_files:
        return ""

    lines = ["🚫 대형 파일 수정 거부:"]
    for r in rejected_files:
        lines.append(f"  - {r['filename']}: {r['reason']}")
        if r.get('suggestion'):
            lines.append(f"    → {r['suggestion']}")

    return '\n'.join(lines)
