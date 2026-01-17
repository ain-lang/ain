"""
Roadmap Git 영속성: Step 완료 시 Git 커밋/푸시
"""

import subprocess
from typing import Tuple


def commit_and_push_roadmap(
    base_path: str,
    fact_core_path: str,
    completed_step: str,
    next_step: str
) -> Tuple[bool, str]:
    """
    fact_core.json 변경사항을 Git에 커밋하고 푸시
    Step 완료 시 영속성을 보장하기 위함

    Returns:
        (성공 여부, 메시지)
    """
    try:
        commit_msg = f"roadmap: {completed_step} 완료 → {next_step} 시작"

        # Git add
        subprocess.run(
            ["git", "add", fact_core_path],
            cwd=base_path,
            capture_output=True,
            timeout=30
        )

        # Git commit
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=base_path,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            if "nothing to commit" in result.stdout.lower():
                return True, "ℹ️ 로드맵: 커밋할 변경사항 없음"
            return False, f"⚠️ 로드맵 커밋 실패: {result.stderr}"

        # Git push
        push_result = subprocess.run(
            ["git", "push"],
            cwd=base_path,
            capture_output=True,
            text=True,
            timeout=60
        )

        if push_result.returncode == 0:
            return True, f"✅ 로드맵 업데이트 푸시 완료: {commit_msg}"
        else:
            return False, f"⚠️ 로드맵 푸시 실패: {push_result.stderr}"

    except subprocess.TimeoutExpired:
        return False, "⚠️ 로드맵 Git 작업 타임아웃"
    except Exception as e:
        return False, f"⚠️ 로드맵 Git 작업 오류: {e}"
