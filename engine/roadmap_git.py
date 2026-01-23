"""
Roadmap Git 영속성: Step 완료 시 Git 커밋/푸시
토큰 기반 push로 Railway 환경에서도 작동
"""

import os
import subprocess
import shutil
from typing import Tuple


def _get_remote_url() -> str:
    """토큰 기반 원격 URL 생성"""
    token = os.getenv("GITHUB_TOKEN", "")
    repo = os.getenv("REPO_NAME", "ain-lang/ain")
    if token:
        return f"https://{token}@github.com/{repo}.git"
    return ""


def commit_and_push_roadmap(
    base_path: str,
    fact_core_path: str,
    completed_step: str,
    next_step: str
) -> Tuple[bool, str]:
    """
    fact_core.json 변경사항을 Git에 커밋하고 푸시
    Step 완료 시 영속성을 보장하기 위함 (토큰 기반)

    Returns:
        (성공 여부, 메시지)
    """
    try:
        git_path = shutil.which("git") or "git"
        commit_msg = f"roadmap: {completed_step} 완료 → {next_step} 시작"

        # Git add
        subprocess.run(
            [git_path, "add", fact_core_path],
            cwd=base_path,
            capture_output=True,
            timeout=30
        )

        # Git commit
        result = subprocess.run(
            [git_path, "commit", "-m", commit_msg],
            cwd=base_path,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            if "nothing to commit" in result.stdout.lower():
                return True, "ℹ️ 로드맵: 커밋할 변경사항 없음"
            return False, f"⚠️ 로드맵 커밋 실패: {result.stderr}"

        # 토큰 기반 원격 URL로 push
        remote_url = _get_remote_url()
        if not remote_url:
            return False, "⚠️ 로드맵 푸시 실패: GITHUB_TOKEN 없음"

        push_result = subprocess.run(
            [git_path, "push", remote_url, "HEAD:main"],
            cwd=base_path,
            capture_output=True,
            text=True,
            timeout=60
        )

        if push_result.returncode == 0:
            return True, f"✅ 로드맵 업데이트 푸시 완료: {commit_msg}"
        else:
            # push 실패 시 force push 시도
            force_result = subprocess.run(
                [git_path, "push", "--force", remote_url, "HEAD:main"],
                cwd=base_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            if force_result.returncode == 0:
                return True, f"✅ 로드맵 force push 완료: {commit_msg}"
            return False, f"⚠️ 로드맵 푸시 실패: {push_result.stderr}"

    except subprocess.TimeoutExpired:
        return False, "⚠️ 로드맵 Git 작업 타임아웃"
    except Exception as e:
        return False, f"⚠️ 로드맵 Git 작업 오류: {e}"
