"""
Git 동기화 유틸리티 (수정 금지)
================================
진화 커밋/푸시 전후 동기화 상태를 검증한다.

문제 배경:
- 커밋 후 푸시 시 mismatch 발생
- force-push가 효과 없는 경우
- 로컬과 원격 분기로 인한 진화 손실
"""

import subprocess
from typing import Dict, Any, Optional, Tuple


def get_git_status() -> Dict[str, Any]:
    """
    현재 Git 상태를 반환한다.

    Returns:
        {
            "local_head": str,      # 로컬 HEAD 커밋 해시
            "remote_head": str,     # origin/main HEAD 커밋 해시
            "is_synced": bool,      # 동기화 여부
            "ahead": int,           # 로컬이 앞선 커밋 수
            "behind": int,          # 로컬이 뒤처진 커밋 수
            "has_uncommitted": bool # 커밋 안 된 변경 있는지
        }
    """
    result = {
        "local_head": "",
        "remote_head": "",
        "is_synced": False,
        "ahead": 0,
        "behind": 0,
        "has_uncommitted": False,
        "error": None
    }

    try:
        # 로컬 HEAD
        local = _run_git("rev-parse", "HEAD")
        result["local_head"] = local[:7] if local else ""

        # fetch 후 원격 HEAD
        _run_git("fetch", "origin", "main", "--quiet")
        remote = _run_git("rev-parse", "origin/main")
        result["remote_head"] = remote[:7] if remote else ""

        # ahead/behind 계산
        ahead_behind = _run_git("rev-list", "--left-right", "--count", "HEAD...origin/main")
        if ahead_behind:
            parts = ahead_behind.split()
            if len(parts) == 2:
                result["ahead"] = int(parts[0])
                result["behind"] = int(parts[1])

        # 동기화 여부
        result["is_synced"] = (result["ahead"] == 0 and result["behind"] == 0)

        # 커밋 안 된 변경
        status = _run_git("status", "--porcelain")
        result["has_uncommitted"] = bool(status and status.strip())

    except Exception as e:
        result["error"] = str(e)

    return result


def verify_push(expected_hash: str) -> Tuple[bool, str]:
    """
    푸시 후 원격에 해당 커밋이 있는지 검증한다.

    Args:
        expected_hash: 푸시한 커밋 해시 (7자 이상)

    Returns:
        (성공 여부, 메시지)
    """
    try:
        _run_git("fetch", "origin", "main", "--quiet")
        remote_head = _run_git("rev-parse", "origin/main")

        if not remote_head:
            return False, "원격 HEAD를 가져올 수 없음"

        expected_short = expected_hash[:7]
        remote_short = remote_head[:7]

        if remote_short == expected_short:
            return True, f"push: verified ({remote_short})"
        else:
            return False, f"mismatch: {remote_short} != {expected_short}"

    except Exception as e:
        return False, f"verify error: {e}"


def safe_push(max_retries: int = 3) -> Tuple[bool, str]:
    """
    안전한 푸시 - 실패 시 pull-rebase 후 재시도.

    Args:
        max_retries: 최대 재시도 횟수

    Returns:
        (성공 여부, 메시지)
    """
    for attempt in range(max_retries):
        # 1. 일반 푸시 시도
        push_result = _run_git("push", "origin", "main")
        if "rejected" not in (push_result or "").lower():
            # 검증
            local_head = _run_git("rev-parse", "HEAD")
            success, msg = verify_push(local_head)
            if success:
                return True, msg

        # 2. pull --rebase 후 재시도
        _run_git("pull", "--rebase", "origin", "main")

    return False, f"push failed after {max_retries} retries"


def sync_before_commit() -> Tuple[bool, str]:
    """
    커밋 전 동기화 - 원격이 앞서 있으면 pull.

    Returns:
        (동기화 필요 여부, 메시지)
    """
    status = get_git_status()

    if status.get("error"):
        return False, f"git error: {status['error']}"

    if status["behind"] > 0:
        # 원격이 앞서 있음 - pull 필요
        _run_git("pull", "--rebase", "origin", "main")
        return True, f"pulled {status['behind']} commits from origin"

    return False, "already synced"


def _run_git(*args) -> Optional[str]:
    """Git 명령 실행 헬퍼."""
    try:
        result = subprocess.run(
            ["git"] + list(args),
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None
