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
            
            # 3. .git 폴더가 없으면 clone (init 대신!)
            if not os.path.exists(".git"):
                print("📂 .git 폴더가 없어 clone을 진행합니다.")
                remote_url = f"https://{self.token}@github.com/{self.repo_name}.git"
                # 현재 디렉토리에 clone
                subprocess.run([git_path, "clone", remote_url, "."], check=True)
            
            # 4. 유저 설정 (Global로 설정하여 안정성 확보)
            subprocess.run([git_path, "config", "--global", "user.email", "ain@evolution.ai"], check=True)
            subprocess.run([git_path, "config", "--global", "user.name", "AIN Core"], check=True)
            
            # 5. 최신 상태로 pull (conflict 방지)
            remote_url = f"https://{self.token}@github.com/{self.repo_name}.git"
            subprocess.run([git_path, "pull", remote_url, branch, "--rebase"], check=False)
            
            subprocess.run([git_path, "add", "."], check=True)
            
            result = subprocess.run(
                [git_path, "commit", "-m", f"🧬 {message}"],
                capture_output=True,
                text=True
            )
            
            if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                return True, "변경사항 없음 (이미 최신 상태입니다)", None
            
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

            sha = subprocess.check_output([git_path, "rev-parse", "HEAD"]).decode().strip()
            return True, "✅ 동기화 성공 (Push 완료)", sha
            
        except Exception as e:
            return False, f"❌ Git Push 실패: {str(e)}", None
    
    def get_commit_url(self, sha: str) -> str:
        """커밋 URL 생성"""
        return f"https://github.com/{self.repo_name}/commit/{sha}"
