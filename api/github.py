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
    
    def commit_and_push(self, message: str, branch: str = "main") -> tuple[bool, str, str | None, dict]:
        """
        변경사항 커밋 및 푸시
        
        Returns:
            (success: bool, message: str, commit_sha: str | None, debug_info: dict)
        """
        import shutil
        git_path = shutil.which("git")
        if not git_path:
            return False, "❌ git 미설치", None, {}
        
        debug = {"stages": [], "diff_stat": "", "changed_files": 0}
        
        # 🔍 토큰 검증
        token_info = f"len={len(self.token) if self.token else 0}, prefix={self.token[:4] if self.token and len(self.token) > 4 else 'N/A'}"
        print(f"🔑 Token info: {token_info}")
        debug["token_info"] = token_info
        
        if not self.token or len(self.token) < 10:
            return False, f"❌ GitHub 토큰 없음 또는 너무 짧음 ({token_info})", None, debug
        
        # 🔐 GitHub API로 토큰 권한 확인
        try:
            if self.github:
                user = self.github.get_user()
                scopes = self.github.oauth_scopes or []
                debug["github_user"] = user.login
                debug["github_scopes"] = scopes
                print(f"✅ GitHub API 인증 성공: {user.login}, scopes={scopes}")
                
                # repo 스코프 확인
                if 'repo' not in scopes and 'public_repo' not in scopes:
                    debug["push_issue"] = f"토큰에 repo 스코프 없음: {scopes}"
                    return False, f"❌ 토큰에 push 권한(repo 스코프) 없음: {scopes}", None, debug
        except Exception as api_err:
            debug["github_api_error"] = str(api_err)[:100]
            print(f"⚠️ GitHub API 인증 실패: {api_err}")

        try:
            # 1. 안전한 디렉토리 설정 (Docker/Railway 환경 대응 핵심!)
            current_dir = os.getcwd()
            subprocess.run([git_path, "config", "--global", "--add", "safe.directory", current_dir], check=True)
            
            # 2. Credential Helper 비활성화 (락 에러 방지)
            subprocess.run([git_path, "config", "--global", "--unset", "credential.helper"], check=False)
            subprocess.run([git_path, "config", "--global", "credential.helper", ""], check=True)
            
            # 3. .git 폴더가 없으면 init + remote 연결 (기존 파일 유지)
            remote_url = f"https://{self.token}@github.com/{self.repo_name}.git"
            debug["repo"] = self.repo_name
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
            
            # 5. 최신 상태로 pull (충돌 시 로컬 변경사항 우선 - ours 전략)
            pull_result = subprocess.run(
                [git_path, "pull", remote_url, branch, "--no-rebase", "--strategy-option=ours"],
                capture_output=True, text=True
            )
            # 충돌 발생 시 강제 복구 (현재 로컬 상태 유지)
            if pull_result.returncode != 0:
                print(f"⚠️ Pull 충돌 발생, 로컬 상태 강제 복구 (ours 전략)")
                subprocess.run([git_path, "merge", "--abort"], check=False)
                subprocess.run([git_path, "rebase", "--abort"], check=False)
                # 충돌 마커가 생기는 것을 방지하기 위해 로컬 파일을 강제 유지
                subprocess.run([git_path, "checkout", "--ours", "."], check=False)
                subprocess.run([git_path, "add", "."], check=False)
            
            subprocess.run([git_path, "add", "."], check=True)
            
            # 📊 변경사항 확인 (디버그용)
            diff_result = subprocess.run(
                [git_path, "diff", "--cached", "--stat"],
                capture_output=True, text=True
            )
            debug["diff_stat"] = diff_result.stdout.strip()[:500] if diff_result.stdout else "(no changes)"
            debug["changed_files"] = diff_result.stdout.count('\n') if diff_result.stdout else 0
            debug["stages"].append(f"diff: {debug['changed_files']} files")
            
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
                debug["stages"].append("nothing to commit")
                return True, "변경사항 없음 (이미 최신 상태입니다)", None, debug
            
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
                debug["stages"].append("commit: SHA unchanged")
                debug["commit_stdout"] = result.stdout[:200]
                debug["commit_stderr"] = result.stderr[:200]
                return True, "변경사항 없음 (커밋 생성 안됨)", None, debug
            
            if new_sha:
                print(f"✅ 새 커밋 생성됨: {new_sha[:8]}")
                debug["stages"].append(f"commit: {new_sha[:8]}")
            print(f"🚀 GitHub로 푸시 시도 중: {self.repo_name} (branch: {branch})")
            
            # 6. 일반 푸시 (--force 제거! 히스토리 보존)
            push_result = subprocess.run(
                [git_path, "push", remote_url, f"HEAD:{branch}"],
                capture_output=True,
                text=True
            )
            
            print(f"📤 푸시 결과: code={push_result.returncode}")
            print(f"   stdout: {push_result.stdout[:300] if push_result.stdout else '(empty)'}")
            print(f"   stderr: {push_result.stderr[:300] if push_result.stderr else '(empty)'}")
            debug["push_stdout"] = push_result.stdout[:300] if push_result.stdout else ""
            debug["push_stderr"] = push_result.stderr[:300] if push_result.stderr else ""
            
            # 푸시 실패 시 pull 후 재시도 (한 번만)
            if push_result.returncode != 0:
                print("⚠️ 푸시 실패, pull 후 재시도...")
                subprocess.run([git_path, "pull", remote_url, branch, "--rebase"], check=False)
                push_result = subprocess.run(
                    [git_path, "push", remote_url, f"HEAD:{branch}"],
                    capture_output=True,
                    text=True
                )
                print(f"📤 재시도 결과: code={push_result.returncode}")
            
            if push_result.returncode != 0:
                raise Exception(f"Push 실패: {push_result.stderr}")
            
            # 🔍 원격 HEAD 확인 (실제로 푸시되었는지 검증)
            try:
                ls_result = subprocess.run(
                    [git_path, "ls-remote", remote_url, f"refs/heads/{branch}"],
                    capture_output=True, text=True, timeout=10
                )
                remote_head = ls_result.stdout.strip().split()[0] if ls_result.stdout.strip() else ""
                
                if remote_head and new_sha and remote_head != new_sha:
                    print(f"⚠️ 원격 HEAD({remote_head[:8]})와 로컬({new_sha[:8]})이 다름! Force Push 시도...")
                    debug["stages"].append(f"mismatch: {remote_head[:8]} != {new_sha[:8]}")

                    # 🔄 Force Push 전 remote URL 재설정 (토큰 갱신)
                    subprocess.run([git_path, "remote", "set-url", "origin", remote_url], check=False)

                    # 🔄 로컬 ref 강제 동기화 (핵심! ref가 오래되면 force push가 "up-to-date" 반환)
                    subprocess.run([git_path, "fetch", "--force", remote_url, f"{branch}:refs/remotes/origin/{branch}"],
                                   capture_output=True, timeout=30)
                    # ref 정리 (삭제된 원격 브랜치 정리)
                    subprocess.run([git_path, "remote", "prune", "origin"], capture_output=True, timeout=10)

                    # 🚀 Force Push 재시도 (최대 3회)
                    force_success = False
                    for attempt in range(1, 4):
                        print(f"📤 Force Push 시도 {attempt}/3...")
                        # --force-with-lease 대신 명시적 ref 지정
                        force_result = subprocess.run(
                            [git_path, "push", "--force", remote_url, f"{new_sha}:{branch}"],
                            capture_output=True, text=True
                        )

                        # 실패 시 다른 방식으로 재시도
                        if force_result.returncode != 0 and attempt < 3:
                            # HEAD 대신 명시적 SHA 사용
                            force_result = subprocess.run(
                                [git_path, "push", "--force", "--no-thin", remote_url, f"{new_sha}:refs/heads/{branch}"],
                                capture_output=True, text=True
                            )

                        print(f"   결과: code={force_result.returncode}")
                        if force_result.stderr:
                            print(f"   stderr: {force_result.stderr[:200]}")

                        if force_result.returncode == 0:
                            force_success = True
                            break

                        # 재시도 전 잠시 대기
                        import time
                        time.sleep(1)

                    # Force push stdout/stderr 기록
                    debug["force_stdout"] = force_result.stdout[:300] if force_result.stdout else ""
                    debug["force_stderr"] = force_result.stderr[:300] if force_result.stderr else ""
                    debug["force_attempts"] = attempt

                    if force_success:
                        # 재확인
                        verify = subprocess.run(
                            [git_path, "ls-remote", remote_url, f"refs/heads/{branch}"],
                            capture_output=True, text=True, timeout=10
                        )
                        verify_head = verify.stdout.strip().split()[0] if verify.stdout.strip() else ""
                        if verify_head == new_sha:
                            print(f"✅ Force Push 성공! 원격 HEAD: {verify_head[:8]}")
                            debug["stages"].append(f"force-push: success ({new_sha[:8]})")
                        else:
                            # 🚨 returncode=0인데 원격이 안 바뀜 = 토큰 권한 문제
                            debug["stages"].append(f"force-push: NO EFFECT (still {verify_head[:8]})")
                            debug["push_issue"] = "토큰 권한 확인 필요 (push 성공했으나 원격 미반영)"
                            debug["remote_head"] = verify_head
                            debug["local_head"] = new_sha
                            
                            # 🔄 GitHub API로 대안 시도
                            print("🔄 Force push 무효, GitHub API로 대안 시도...")
                            api_result = self._push_via_api(git_path, message, branch)
                            if api_result:
                                debug["stages"].append("api-push: success")
                                return True, "✅ GitHub API로 동기화 성공", api_result, debug
                            
                            return False, f"푸시 실패: 토큰 권한 확인 필요", None, debug
                    else:
                        debug["stages"].append(f"force-push: error ({force_result.returncode})")
                        debug["push_issue"] = force_result.stderr[:200] if force_result.stderr else "unknown"
                        debug["remote_head"] = remote_head
                        debug["local_head"] = new_sha
                        
                        # 🚨 Git push 완전 실패 - GitHub API로 대안 시도
                        print("🔄 Git push 실패, GitHub API로 대안 시도...")
                        api_result = self._push_via_api(git_path, message, branch)
                        if api_result:
                            debug["stages"].append("api-push: success")
                            return True, "✅ GitHub API로 동기화 성공", api_result, debug
                        
                        return False, f"푸시 실패: {force_result.stderr[:100]}", None, debug
                else:
                    print(f"✅ 원격 HEAD 확인: {remote_head[:8] if remote_head else 'N/A'}")
                    debug["stages"].append(f"push: verified ({remote_head[:8] if remote_head else 'N/A'})")
            except Exception as verify_err:
                print(f"⚠️ 원격 확인 실패: {verify_err}")

            # 최종 SHA 확인 (이미 new_sha가 있으면 재사용)
            if not new_sha:
                try:
                    new_sha = subprocess.run(
                        [git_path, "rev-parse", "HEAD"],
                        capture_output=True, text=True, check=True
                    ).stdout.strip()
                except:
                    new_sha = None
            
            debug["stages"].append("success")
            return True, "✅ 동기화 성공 (Push 완료)", new_sha, debug
            
        except Exception as e:
            debug["stages"].append(f"error: {str(e)[:50]}")
            return False, f"❌ Git Push 실패: {str(e)}", None, debug
    
    def _push_via_api(self, git_path: str, message: str, branch: str) -> str | None:
        """
        Git push 실패 시 GitHub Git Data API로 실제 커밋 생성

        기존 방식(update_file)은 파일별 개별 커밋 → 로컬 히스토리와 불일치
        개선 방식: Tree → Commit → Ref 업데이트로 단일 커밋 생성
        """
        try:
            if not self.repo:
                print("❌ GitHub API repo 객체 없음")
                return None

            import subprocess
            import base64
            import os

            # 제외할 파일 패턴 (캐시, 설정, 바이너리)
            EXCLUDE_PATTERNS = [
                '.ain_cache/', '.claude/settings.local', '/data/', 'lancedb/',
                '.arrow', '.pyc', '__pycache__', '.env', '.venv'
            ]

            # 1. 원격 HEAD SHA 먼저 가져오기 (API 사용 - 로컬 ref 무시)
            ref = self.repo.get_git_ref(f"heads/{branch}")
            current_head_sha = ref.object.sha
            print(f"  📍 원격 HEAD (API): {current_head_sha[:8]}")

            # 2. 원격 HEAD 기준으로 변경된 파일 목록 가져오기
            diff_result = subprocess.run(
                [git_path, "diff", "--name-only", current_head_sha],
                capture_output=True, text=True
            )
            all_changed = [f.strip() for f in diff_result.stdout.strip().split('\n') if f.strip()]
            print(f"  📊 변경 파일: {len(all_changed)}개 (vs {current_head_sha[:8]})")

            # 제외 패턴 필터링
            changed_files = [
                f for f in all_changed
                if not any(pat in f for pat in EXCLUDE_PATTERNS)
            ]

            if not changed_files:
                print(f"⚠️ API push: 유효한 파일 없음 (전체 {len(all_changed)}개 중 모두 제외됨)")
                return None

            print(f"📤 API push (Git Data API): {len(changed_files)} files (제외: {len(all_changed) - len(changed_files)})")

            # 3. 현재 HEAD의 tree 가져오기
            head_commit = self.repo.get_git_commit(current_head_sha)
            base_tree_sha = head_commit.tree.sha

            # 4. 변경된 파일들의 blob 생성 및 tree element 준비
            tree_elements = []
            skipped_reasons = {"not_found": 0, "conflict": 0, "binary": 0, "error": 0}

            for filepath in changed_files:
                try:
                    # 파일 존재 확인
                    if not os.path.exists(filepath):
                        print(f"  ⚠️ {filepath}: 파일 없음 (삭제됨?)")
                        skipped_reasons["not_found"] += 1
                        continue

                    # 바이너리 파일 체크
                    try:
                        with open(filepath, 'rb') as f:
                            chunk = f.read(8192)
                            if b'\x00' in chunk:
                                print(f"  ⚠️ {filepath}: 바이너리 파일, 스킵")
                                skipped_reasons["binary"] += 1
                                continue
                    except:
                        pass

                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # 충돌 마커 안전 검사
                    if any(m in content for m in ['<<<<<<<', '=======', '>>>>>>>']):
                        print(f"  🚫 {filepath}: 충돌 마커 감지됨, 스킵")
                        skipped_reasons["conflict"] += 1
                        continue

                    # Blob 생성 (UTF-8 base64 인코딩)
                    blob = self.repo.create_git_blob(content, "utf-8")

                    tree_elements.append({
                        "path": filepath,
                        "mode": "100644",  # regular file
                        "type": "blob",
                        "sha": blob.sha
                    })
                    print(f"  📄 {filepath} → blob {blob.sha[:8]}")

                except Exception as file_err:
                    print(f"  ❌ {filepath}: {type(file_err).__name__}: {file_err}")
                    skipped_reasons["error"] += 1

            print(f"  📊 스킵 요약: {skipped_reasons}")

            if not tree_elements:
                print("⚠️ API push: 유효한 파일 없음")
                return None

            # 5. 새 Tree 생성 (base_tree 위에 변경사항 적용)
            from github import InputGitTreeElement
            git_tree_elements = [
                InputGitTreeElement(
                    path=elem["path"],
                    mode=elem["mode"],
                    type=elem["type"],
                    sha=elem["sha"]
                )
                for elem in tree_elements
            ]
            new_tree = self.repo.create_git_tree(git_tree_elements, base_tree=self.repo.get_git_tree(base_tree_sha))
            print(f"  🌳 새 Tree: {new_tree.sha[:8]}")

            # 6. 새 Commit 생성 (parent = 현재 원격 HEAD)
            new_commit = self.repo.create_git_commit(
                message=f"🧬 {message}",
                tree=new_tree,
                parents=[head_commit]
            )
            print(f"  ✨ 새 Commit: {new_commit.sha[:8]}")

            # 7. Ref 업데이트 (원격 HEAD를 새 커밋으로)
            ref.edit(sha=new_commit.sha, force=True)
            print(f"  🔗 Ref 업데이트: {branch} → {new_commit.sha[:8]}")

            # 8. 검증
            updated_ref = self.repo.get_git_ref(f"heads/{branch}")
            if updated_ref.object.sha == new_commit.sha:
                print(f"✅ API push 성공! 원격 HEAD: {new_commit.sha[:8]}")
                return new_commit.sha
            else:
                print(f"⚠️ Ref 업데이트 실패: {updated_ref.object.sha[:8]} != {new_commit.sha[:8]}")
                return None

        except Exception as e:
            print(f"❌ API push 실패: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_commit_url(self, sha: str) -> str:
        """커밋 URL 생성"""
        if not sha:
            return f"https://github.com/{self.repo_name}"  # SHA 없으면 레포 URL
        return f"https://github.com/{self.repo_name}/commit/{sha}"
