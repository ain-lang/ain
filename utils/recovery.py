"""
AIN Recovery Module
====================
엔진 크래시 시 스마트 복구 로직을 제공한다.

복구 전략:
1. origin/main fetch 후 최신 코드 적용 (원격에 수정이 있을 경우)
2. HEAD~1 롤백 (직전 커밋으로 복구)
3. 마지막 성공 태그로 복구 (ain-stable 태그)
4. 백업 폴더 기반 복구 (최후의 수단)

Usage:
    from utils.recovery import smart_rollback

    success = smart_rollback()
"""

import os
import shutil
import subprocess
from typing import Optional, Tuple


STABLE_TAG = "ain-stable"


def _get_git_path() -> Optional[str]:
    """Git 실행 파일 경로를 찾는다."""
    return shutil.which("git")


def _run_git(args: list, timeout: int = 30) -> Tuple[bool, str]:
    """Git 명령을 실행하고 결과를 반환한다."""
    git_path = _get_git_path()
    if not git_path:
        return False, "Git not found"

    try:
        result = subprocess.run(
            [git_path] + args,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        output = result.stdout + result.stderr
        return result.returncode == 0, output.strip()
    except subprocess.TimeoutExpired:
        return False, "Git command timeout"
    except Exception as e:
        return False, str(e)


def _setup_safe_directory():
    """Docker/Railway 환경에서 safe.directory 설정."""
    current_dir = os.getcwd()
    _run_git(["config", "--global", "--add", "safe.directory", current_dir])


def fetch_and_reset_to_origin() -> Tuple[bool, str]:
    """
    원격 origin/main을 fetch하고 해당 상태로 리셋한다.
    원격에 수정사항이 푸시되었을 때 유용.
    """
    _setup_safe_directory()

    # 1. Fetch origin
    success, output = _run_git(["fetch", "--force", "origin", "main"])
    if not success:
        return False, f"Fetch 실패: {output}"

    # 2. Reset to origin/main
    success, output = _run_git(["reset", "--hard", "origin/main"])
    if not success:
        return False, f"Reset 실패: {output}"

    return True, "origin/main으로 복구 완료"


def rollback_to_previous_commit() -> Tuple[bool, str]:
    """직전 커밋(HEAD~1)으로 롤백한다."""
    _setup_safe_directory()

    success, output = _run_git(["reset", "--hard", "HEAD~1"])
    if not success:
        return False, f"HEAD~1 롤백 실패: {output}"

    return True, "HEAD~1로 롤백 완료"


def rollback_to_stable_tag() -> Tuple[bool, str]:
    """마지막 성공 태그(ain-stable)로 롤백한다."""
    _setup_safe_directory()

    # 태그 존재 확인
    success, output = _run_git(["tag", "-l", STABLE_TAG])
    if not success or STABLE_TAG not in output:
        return False, f"'{STABLE_TAG}' 태그가 존재하지 않음"

    success, output = _run_git(["reset", "--hard", STABLE_TAG])
    if not success:
        return False, f"태그 롤백 실패: {output}"

    return True, f"'{STABLE_TAG}' 태그로 롤백 완료"


def mark_as_stable() -> Tuple[bool, str]:
    """
    현재 커밋을 안정 버전으로 태그한다.
    엔진이 정상 부팅된 후 호출하면 좋음.
    """
    _setup_safe_directory()

    # 기존 태그 삭제 (있으면)
    _run_git(["tag", "-d", STABLE_TAG])

    # 새 태그 생성
    success, output = _run_git(["tag", STABLE_TAG])
    if not success:
        return False, f"태그 생성 실패: {output}"

    return True, f"'{STABLE_TAG}' 태그 생성 완료"


def rollback_via_backups() -> Tuple[bool, str]:
    """백업 폴더에서 최신 파일을 찾아 복구한다."""
    backup_dir = "backups"
    if not os.path.exists(backup_dir):
        return False, "백업 폴더 없음"

    import glob
    all_backups = glob.glob(os.path.join(backup_dir, "**/*.bak"), recursive=True)
    if not all_backups:
        return False, "백업 파일 없음"

    all_backups.sort(key=os.path.getmtime, reverse=True)
    restored = []

    for backup_path in all_backups[:5]:
        parts = os.path.basename(backup_path).split('.')
        if len(parts) < 3:
            continue

        original_filename = ".".join(parts[:-2])
        target_path = original_filename

        try:
            shutil.copy2(backup_path, target_path)
            restored.append(target_path)
        except Exception:
            continue

    if restored:
        return True, f"백업 복구 완료: {', '.join(restored)}"
    return False, "백업 복구 실패"


def smart_rollback() -> Tuple[bool, str]:
    """
    스마트 복구: 여러 전략을 순차적으로 시도한다.

    순서:
    1. origin/main fetch 후 리셋 (원격 수정 적용)
    2. 직전 커밋으로 롤백
    3. 안정 태그로 롤백
    4. 백업 폴더 복구

    Returns:
        (성공 여부, 메시지)
    """
    strategies = [
        ("origin/main fetch & reset", fetch_and_reset_to_origin),
        ("HEAD~1 롤백", rollback_to_previous_commit),
        ("안정 태그 롤백", rollback_to_stable_tag),
        ("백업 폴더 복구", rollback_via_backups),
    ]

    for name, strategy in strategies:
        print(f"🔄 복구 시도: {name}")
        success, message = strategy()
        if success:
            print(f"✅ {message}")
            return True, message
        else:
            print(f"⚠️ {name} 실패: {message}")

    return False, "모든 복구 전략 실패"


# main.py에서 직접 호출할 수 있는 함수
def recover() -> bool:
    """main.py 호환 인터페이스. 성공 시 True 반환."""
    success, message = smart_rollback()
    return success
