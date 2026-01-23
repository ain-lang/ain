import subprocess
import time
import sys
import os
import shutil
from datetime import datetime

# AIN Supervisor (The Heart)
# 이 파일은 시스템의 핵심 감시 장치로, AI가 직접 수정할 수 없는 보호 구역입니다.
# 신체(ain_engine.py)가 망가지면 Git을 통해 스스로를 치유하고 부활시킵니다.

ENGINE_SCRIPT = "ain_engine.py"

def report_to_telegram(message):
    """긴급 상황 발생 시 텔레그램으로 보고 (엔진 없이 직접 수행)"""
    try:
        from api.keys import get_telegram_config
        import requests
        
        config = get_telegram_config()
        token = config["token"]
        chat_id = config["chat_id"]
        
        if token and chat_id:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": f"❤️ **AIN 심장(Supervisor) 알림**:\n{message}",
                "parse_mode": "Markdown"
            }
            requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"⚠️ 텔레그램 보고 실패: {e}")

def rollback_via_backups():
    """Git이 없을 경우 backups 폴더에서 가장 최신 파일을 찾아 복구"""
    print("🚑 백업 폴더 기반 복구 시도...")
    try:
        backup_dir = "backups"
        if not os.path.exists(backup_dir):
            return False
            
        # 모든 백업 파일 탐색 (.bak로 끝나는 파일)
        import glob
        all_backups = glob.glob(os.path.join(backup_dir, "**/*.bak"), recursive=True)
        if not all_backups:
            return False
            
        # 가장 최근에 생성된 백업 파일 순으로 정렬
        all_backups.sort(key=os.path.getmtime, reverse=True)
        
        # 최근 5개의 백업에 대해 복구 시도
        for backup_path in all_backups[:5]:
            # 백업 파일명 형식: filename.timestamp.bak
            parts = os.path.basename(backup_path).split('.')
            if len(parts) < 3: continue
            
            original_filename = ".".join(parts[:-2])
            # 서브디렉토리 구조 복원 필요
            # TODO: backups/ 내부의 실제 상대 경로를 추출하는 로직 보강
            # 일단은 루트 디렉토리 파일 위주로 간단히 복구
            target_path = original_filename
            
            print(f"♻️ '{backup_path}' -> '{target_path}' 복구 시도...")
            shutil.copy2(backup_path, target_path)
            
        report_to_telegram("🛠️ Git을 찾을 수 없어 로컬 백업 파일을 통해 긴급 복구를 완료했습니다.")
        return True
    except Exception as e:
        print(f"❌ 백업 복구 실패: {e}")
        return False

def rollback_via_git():
    """에러 발생 시 가장 최근의 성공적인 커밋으로 롤백"""
    print("🚑 시스템 자가 치유 시작 (Git Rollback)...")
    try:
        # git_path 탐색
        git_path = shutil.which("git")
        if not git_path:
            return rollback_via_backups()
            
        # 1. 안전한 디렉토리 설정 (Docker/Railway 대응)
        current_dir = os.getcwd()
        subprocess.run([git_path, "config", "--global", "--add", "safe.directory", current_dir], check=True)

        # 2. .git 폴더 확인
        if not os.path.exists(".git"):
            print("📂 .git 폴더가 없어 백업 복구로 전환합니다.")
            return rollback_via_backups()

        # 3. 최신 수정사항 폐기 및 이전 커밋으로 복구
        subprocess.run([git_path, "reset", "--hard", "HEAD"], check=True)
        
        report_to_telegram("🛠️ 신체가 손상되어 Git을 통해 자가 치유를 완료했습니다. 다시 부팅합니다.")
        return True
    except Exception as e:
        print(f"❌ 롤백 실패: {e}")
        # Git 실패 시 백업 폴더 시도
        return rollback_via_backups()

def start_engine():
    """AIN 엔진(신체) 실행 및 감시"""
    while True:
        print(f"💓 AIN 심장: 엔진({ENGINE_SCRIPT}) 가동...")
        
        # 엔진을 별도 프로세스로 실행 (표준 에러 캡처)
        process = subprocess.Popen(
            [sys.executable, ENGINE_SCRIPT],
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 에러 로그 캡처용
        _, stderr = process.communicate()
        exit_code = process.returncode
        
        if exit_code == 0:
            print("👋 엔진이 정상적으로 종료되었습니다.")
            break
        else:
            print(f"🚨 엔진 충돌 감지! (Exit Code: {exit_code})")
            error_preview = stderr[-500:] if stderr else "No error log captured."
            
            # 에러 내용을 AIN이 학습할 수 있도록 파일로 기록
            with open("last_crash.log", "w", encoding="utf-8") as f:
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Exit Code: {exit_code}\n")
                f.write(f"Error:\n{stderr}")

            report_to_telegram(f"🚨 엔진이 멈췄습니다 (코드: {exit_code}).\n\n**에러 요약:**\n`{error_preview}`\n\n30초 후 복구 모드를 가동합니다.")
            time.sleep(30)
            
            # 자가 치유 로직 가동 (스마트 복구 모듈 우선 사용)
            try:
                from utils.recovery import recover
                recovered = recover()
            except ImportError:
                recovered = rollback_via_git()

            if recovered:
                print("♻️ 엔진 재시작 준비 완료.")
            else:
                print("⚠️ 치유 실패. 1분 후 강제 재시도...")
                time.sleep(60)

if __name__ == "__main__":
    print("❤️ AIN 불멸의 심장(Supervisor) 활성화.")
    start_engine()
