"""
Engine Evolution: 진화 사이클 로직
"""
import os
import asyncio


class EvolutionMixin:
    """진화 로직 믹스인 - AINCore에서 사용"""
    
    async def evolve(self, user_query: str = None) -> dict:
        """진화 사이클 실행"""
        result = {
            "success": False,
            "action": None,
            "files_modified": [],
            "error": None,
            "sync_status": None
        }
        
        try:
            # 1. Introspection
            print("🔍 Introspection 단계...")
            system_snapshot = self.get_code_snapshot()
            evolution_history = self.nexus.get_evolution_summary()
            
            # 2. DB 동기화
            if self._should_sync():
                print("💾 DB 동기화 수행 중...")
                sync_result = await self._sync_to_database()
                result["sync_status"] = "success" if sync_result else "skipped"
            else:
                result["sync_status"] = "not_needed"
            
            # 3. Muse Imagination
            print("🧠 Muse가 진화 방향을 구상 중...")
            
            # 중복 방지: 최근 진화 파일 목록 전달
            avoid_files_hint = ""
            if self._recent_evolved_files:
                avoid_files_hint = f"\n\n[🚨 최근 진화된 파일 - 다른 파일로 진화하라]\n{', '.join(self._recent_evolved_files[-5:])}"
            
            if self._no_change_counter >= 2:
                avoid_files_hint += f"\n\n[⚠️ 연속 {self._no_change_counter}회 변경 없음! 반드시 다른 파일을 수정하라]"
            
            imagination = self.muse.imagine(
                system_context=system_snapshot,
                user_query=(user_query or "") + avoid_files_hint,
                evolution_history=evolution_history
            )
            
            if not imagination or "error" in imagination:
                result["error"] = imagination.get("error", "Imagination failed")
                return result
            
            # 4. Overseer Execution
            print("⚙️ Overseer가 코드를 적용 중...")
            updates = imagination.get("updates", [])
            actually_changed = []
            
            for file_change in updates:
                filename = file_change.get("filename")
                code = file_change.get("code")
                
                if filename and code:
                    if self.overseer.is_protected(filename):
                        print(f"🛡️ {filename}은(는) 보호된 파일입니다. 수정을 거부합니다.")
                        continue
                    
                    # 기존 코드와 비교
                    existing_code = ""
                    target_path = os.path.join(self.overseer.base_path, filename)
                    if os.path.exists(target_path):
                        try:
                            with open(target_path, "r", encoding="utf-8") as f:
                                existing_code = f.read()
                        except:
                            pass
                    
                    new_normalized = code.strip().replace('\r\n', '\n')
                    old_normalized = existing_code.strip().replace('\r\n', '\n')
                    
                    if new_normalized == old_normalized:
                        print(f"⏭️ {filename}: 변경 없음, 스킵")
                        continue
                    
                    is_valid, validation_msg = self.overseer.validate_code(code, filename)
                    if not is_valid:
                        print(f"⚠️ 검증 실패 ({filename}): {validation_msg}")
                        continue
                    
                    success, apply_msg = self.overseer.apply_evolution(filename, code)
                    if success:
                        result["files_modified"].append(filename)
                        actually_changed.append(filename)
                        print(f"✅ {filename} 진화 완료")
                        
                        self.nexus.record_evolution(
                            evolution_type="Evolution",
                            action="Update",
                            file=filename,
                            description=imagination.get("intent", "Evolution applied"),
                            status="success"
                        )
                        
                        if filename not in self._recent_evolved_files:
                            self._recent_evolved_files.append(filename)
                        if len(self._recent_evolved_files) > 10:
                            self._recent_evolved_files.pop(0)
                    else:
                        print(f"❌ {filename} 적용 실패: {apply_msg}")
            
            # 연속 무변경 카운터 업데이트
            if not actually_changed:
                self._no_change_counter += 1
                print(f"⚠️ 실제 변경된 파일 없음 (연속 {self._no_change_counter}회)")
            else:
                self._no_change_counter = 0
            
            # 5. Growth Recording & Sync
            if actually_changed:
                self.nexus.increment_growth(len(actually_changed) * 10)
                result["success"] = True
                result["action"] = imagination.get("intent", "Evolution completed")
                
                print(f"🧪 자가 검증 시작... (적용됨: {', '.join(actually_changed)})")
                tests_passed, test_report = self.overseer.run_unit_tests()
                if not tests_passed:
                    print(f"🚨 테스트 실패! 롤백을 수행합니다.\n{test_report}")
                    for filename in actually_changed:
                        self.overseer.rollback(filename)
                    result["success"] = False
                    result["error"] = f"Unit test failed: {test_report[:200]}"
                    return result

                await self._sync_to_database()
                
                push_ok, push_msg, sha = self.github.commit_and_push(f"🧬 Evolution: {result['action'][:80]}")
                if push_ok:
                    result["commit_sha"] = sha
                    print(f"✅ Git Push 성공: {sha}")
                else:
                    print(f"⚠️ Git Push 실패: {push_msg}")
            else:
                result["success"] = False
                result["error"] = "No actual changes (code identical to existing)"
                result["action"] = "skipped_no_change"
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ 진화 실패: {e}")
            return result

    def evolve_sync(self, user_query: str = None) -> dict:
        """동기 버전의 evolve"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.evolve(user_query))
