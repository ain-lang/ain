"""
Engine Introspect: 자기 성찰 및 진화 시도 (Legacy 메인 루프용)
"""
from datetime import datetime, timedelta

from api import get_config
from utils.error_memory import get_error_memory

config = get_config()
DEFAULT_INTERVAL = config["evolution_interval"]


class IntrospectMixin:
    """자기 성찰 믹스인 - AINCore에서 사용"""
    
    def introspect(self, user_query=None):
        """자기 성찰 및 진화 시도 (Legacy 메인 루프용)"""
        if hasattr(self, 'is_processing') and self.is_processing:
            return
        
        self.is_processing = True
        print(f"💡 AIN: 성찰 시작... (Query: {user_query})")
        
        try:
            # 버스트 모드 종료 체크
            if hasattr(self, 'burst_mode') and self.burst_mode and hasattr(self, 'burst_end_time') and self.burst_end_time:
                if datetime.now() > (self.burst_end_time + timedelta(seconds=10)):
                    self.burst_mode = False
                    self.current_interval = DEFAULT_INTERVAL
                    self._save_current_state()
                    self.send_telegram_msg("🍃 **Burst Mode Ended.**\n에너지를 다 썼어요... 이제 다시 평소 주기로 돌아가 조용히 공부할게요. 주인님 고생하셨어요! ✨")

            if user_query and self.handle_command(user_query):
                return

            context = self.fact_core.get_system_snapshot()
            history = self.nexus.get_evolution_summary()
            
            imagination = self.muse.imagine(context, user_query, history)
            
            if "error" in imagination:
                error_msg = imagination["error"]
                if "429" in error_msg:
                    self.send_telegram_msg("🚨 **API Rate Limit Detected!**\n잠시 휴식 모드로 전환합니다. 5분 후에 다시 시도할게요.")
                    self.current_interval = 300
                    self._save_current_state()
                else:
                    self.send_telegram_msg(f"⚠️ **에러:** {error_msg}")
                return

            intent, updates = imagination.get("intent", "성찰 중"), imagination.get("updates", [])

            if not updates:
                if hasattr(self, 'burst_mode') and self.burst_mode or user_query:
                    self.send_telegram_msg(f"💭 **생각:** {intent}")
                return

            self.send_telegram_msg(f"🧬 **진화 시도!**\n**의도:** {intent}")

            applied = []
            error_memory = get_error_memory()
            
            for up in updates:
                filename, code = up.get("filename"), up.get("code")
                valid, reason = self.overseer.validate_code(code, filename)
                if valid:
                    success, msg = self.overseer.apply_evolution(filename, code)
                    if success:
                        applied.append(filename)
                        # 🧠 성공 시 해당 파일의 오류 기록 삭제
                        error_memory.clear_file(filename)
                    else:
                        self.send_telegram_msg(f"❌ **반영 실패 ({filename}):** {msg}")
                        # 🧠 실패 기억에 기록
                        error_memory.record_error(filename, "apply_failed", msg[:100])
                else:
                    self.send_telegram_msg(f"❌ **검증 실패 ({filename}):** {reason}")
                    # 🧠 검증 실패 기억에 기록
                    error_type = "syntax_error" if "Syntax Error" in reason else "validation_failed"
                    error_memory.record_error(filename, error_type, reason[:100])

            if applied:
                self.send_telegram_msg(f"🧪 자가 검증 시작... (적용됨: {', '.join(applied)})")
                
                try:
                    tests_passed, test_report = self.overseer.run_unit_tests()
                    print(f"[DEBUG] 테스트 결과: passed={tests_passed}")
                except Exception as test_err:
                    tests_passed = True
                    test_report = f"테스트 실행 오류 (진행): {str(test_err)[:100]}"
                    print(f"[DEBUG] 테스트 예외: {test_err}")
                
                safe_report = test_report.replace('`', "'").replace('*', '').replace('_', ' ')
                if len(safe_report) > 1000:
                    safe_report = safe_report[:1000] + "\n... (중략)"

                if not tests_passed:
                    self.send_telegram_msg(f"🚨 테스트 실패! 롤백 수행\n{safe_report}")
                    for filename in applied:
                        self.overseer.rollback(filename)
                    self.nexus.record_evolution(
                        evolution_type="Rollback",
                        action="rollback",
                        file=", ".join(applied),
                        description="Test Failure",
                        status="failed"
                    )
                    return
                
                self.send_telegram_msg(f"✅ 테스트 통과! 커밋 중...")
                for filename in applied:
                    self.nexus.record_evolution(
                        evolution_type="Evolution",
                        action="Update",
                        file=filename,
                        description=intent[:200] if intent else "Evolution",
                        status="success"
                    )

                try:
                    if self.cc.sync_facts_to_surreal():
                        print("💾 FactCore → SurrealDB 동기화 완료")
                except Exception as sync_err:
                    print(f"⚠️ SurrealDB 동기화 실패 (비치명적): {sync_err}")

                try:
                    safe_intent = intent[:100].replace('`', "'").replace('\n', ' ')
                    push_ok, push_msg, sha, debug = self.github.commit_and_push(f"Evolution: {safe_intent}")
                    print(f"[DEBUG] Push result: ok={push_ok}, sha={sha}, debug={debug}")
                    
                    if push_ok:
                        if sha:
                            commit_url = self.github.get_commit_url(sha)
                            # 📊 디버그 정보 포함
                            debug_str = f"\n📊 {debug.get('changed_files', 0)} files | {' → '.join(debug.get('stages', []))}"
                            self.send_telegram_msg(f"🛠️ 진화 완료! ({', '.join(applied)}){debug_str}\n{commit_url}")
                        else:
                            # ⚠️ 변경사항 없음 - 원인 표시
                            debug_str = f"\n📊 diff: {debug.get('diff_stat', 'N/A')[:100]}"
                            stages = ' → '.join(debug.get('stages', []))
                            self.send_telegram_msg(f"✨ 진화 완료! ({', '.join(applied)}) - 변경사항 없음\n📊 {stages}{debug_str}")
                    else:
                        safe_push_msg = push_msg.replace('`', "'").replace('*', '')[:150]
                        stages = ' → '.join(debug.get('stages', []))
                        self.send_telegram_msg(f"⚠️ 로컬 반영됨, 푸시 실패: {safe_push_msg}\n📊 {stages}")
                except Exception as push_err:
                    safe_err = str(push_err).replace('`', "'").replace('*', '')[:100]
                    self.send_telegram_msg(f"⚠️ 커밋/푸시 오류: {safe_err}")
            else:
                self.send_telegram_msg(f"⚠️ 적용된 파일 없음 (검증/보호 실패)")
            
        except Exception as e:
            import traceback
            safe_error = str(e).replace('`', "'").replace('*', '').replace('_', ' ')[:200]
            safe_trace = traceback.format_exc().replace('`', "'").replace('*', '')[:300]
            error_msg = f"💥 에러 발생: {safe_error}\n\n{safe_trace}"
            self.send_telegram_msg(error_msg)
        finally:
            self.is_processing = False
