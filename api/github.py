"""
GitHub API Helper
"""

import subprocess
import os
from github import Github, Auth
from .keys import get_github_token, get_config

class GitHubClient:
    """GitHub 클라이언트"""
    
    def __init__(self):
        self.token = get_github_token()
        self.repo_name = get_config()["repo_name"]
        
        if self.token:
            auth = Auth.Token(self.token)
            self.github = Github(auth=auth)
            self.repo = self.github.get_repo(self.repo_name) if self.repo_name else None
        else:
            self.github = None
            self.repo = None
    
    def commit_and_push(self, message: str, branch: str = "main") -> tuple[bool, str, str | None]:
        """
        변경사항 커밋 및 푸시
        
        Returns:
            (success: bool, message: str, commit_sha: str | None)
        """
        import shutil
        git_path = shutil.which("git")
        if not git_path:
            return False, "❌ 서버 환경에 'git'이 설치되어 있지 않습니다. Railway 설정을 확인해주세요.", None

        try:
            # 1. 안전한 디렉토리 설정 (Docker/Railway 환경 대응 핵심!)
            current_dir = os.getcwd()
            subprocess.run([git_path, "config", "--global", "--add", "safe.directory", current_dir], check=True)
            
            # 2. Credential Helper 비활성화 (락 에러 방지)
            subprocess.run([git_path, "config", "--global", "--unset", "credential.helper"], check=False)
            subprocess.run([git_path, "config", "--global", "credential.helper", ""], check=True)
            
            # 3. .git 폴더가 없으면 init + remote 연결 (기존 파일 유지)
            remote_url = f"https://{self.token}@github.com/{self.repo_name}.git"
            if not os.path.exists(".git"):
                print("📂 .git 폴더가 없어 init + remote 연결을 진행합니다.")
                subprocess.run([git_path, "init"], check=True)
                subprocess.run([git_path, "remote", "add", "origin", remote_url], check=False)  # 이미 있으면 무시
                # 원격 히스토리 가져오기 (현재 파일은 유지)
                subprocess.run([git_path, "fetch", "origin", branch], check=False)
                # 원격 브랜치와 연결 (현재 변경사항 유지하면서)
                subprocess.run([git_path, "branch", "--set-upstream-to", f"origin/{branch}"], check=False)
            
            # 4. 유저 설정 (Global로 설정하여 안정성 확보)
            subprocess.run([git_path, "config", "--global", "user.email", "ain@evolution.ai"], check=True)
            subprocess.run([git_path, "config", "--global", "user.name", "AIN Core"], check=True)
            
            # 5. 최신 상태로 pull (conflict 발생 시 중단하고 현재 변경사항 우선)
            pull_result = subprocess.run(
                [git_path, "pull", remote_url, branch, "--no-rebase", "--strategy-option=theirs"],
                capture_output=True, text=True
            )
            # 충돌 발생 시 rebase 중단하고 현재 상태 유지
            if pull_result.returncode != 0:
                subprocess.run([git_path, "rebase", "--abort"], check=False)
                subprocess.run([git_path, "merge", "--abort"], check=False)
                print(f"⚠️ Pull 충돌 발생, 로컬 변경사항 우선 적용")
            
            subprocess.run([git_path, "add", "."], check=True)
            
            # 커밋 전 HEAD SHA 저장 (실패 시 빈 문자열)
            try:
                old_sha = subprocess.run(
                    [git_path, "rev-parse", "HEAD"],
                    capture_output=True, text=True, check=True
                ).stdout.strip()
            except:
                old_sha = ""
            
            result = subprocess.run(
                [git_path, "commit", "-m", f"🧬 {message}"],
                capture_output=True,
                text=True
            )
            
            if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                return True, "변경사항 없음 (이미 최신 상태입니다)", None
            
            # 커밋 후 HEAD SHA 확인 (실패 시 빈 문자열)
            try:
                new_sha = subprocess.run(
                    [git_path, "rev-parse", "HEAD"],
                    capture_output=True, text=True, check=True
                ).stdout.strip()
            except:
                new_sha = ""
            
            # 🚨 커밋이 실제로 생성되었는지 확인
            if old_sha and new_sha and old_sha == new_sha:
                print(f"⚠️ 커밋이 생성되지 않음 (SHA 변경 없음)")
                print(f"   stdout: {result.stdout[:200]}")
                print(f"   stderr: {result.stderr[:200]}")
                return True, "변경사항 없음 (커밋 생성 안됨)", None
            
            if new_sha:
                print(f"✅ 새 커밋 생성됨: {new_sha[:8]}")
            print(f"🚀 GitHub로 푸시 시도 중: {self.repo_name} (branch: {branch})")
            
            # 6. 일반 푸시 (--force 제거! 히스토리 보존)
            push_result = subprocess.run(
                [git_path, "push", remote_url, f"HEAD:{branch}"],
                capture_output=True,
                text=True
            )
            
            # 푸시 실패 시 pull 후 재시도 (한 번만)
            if push_result.returncode != 0:
                print("⚠️ 푸시 실패, pull 후 재시도...")
                subprocess.run([git_path, "pull", remote_url, branch, "--rebase"], check=False)
                push_result = subprocess.run(
                    [git_path, "push", remote_url, f"HEAD:{branch}"],
                    capture_output=True,
                    text=True
                )
            
            if push_result.returncode != 0:
                raise Exception(f"Push 실패: {push_result.stderr}")

            # 최종 SHA 확인 (이미 new_sha가 있으면 재사용)
            if not new_sha:
                try:
                    new_sha = subprocess.run(
                        [git_path, "rev-parse", "HEAD"],
                        capture_output=True, text=True, check=True
                    ).stdout.strip()
                except:
                    new_sha = None
            
            return True, "✅ 동기화 성공 (Push 완료)", new_sha
            
        except Exception as e:
            return False, f"❌ Git Push 실패: {str(e)}", None
    
    def get_commit_url(self, sha: str) -> str:
        """커밋 URL 생성"""
        return f"https://github.com/{self.repo_name}/commit/{sha}"
