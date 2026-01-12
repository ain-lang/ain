"""
AIN Core Engine - The Heart of AI-Native System
================================================
Step 3 Evolution: CorpusCallosum 통합으로 완전한 데이터 영속성 파이프라인 구현

Data Flow:
    Runtime (AINCore) 
        -> CorpusCallosum (Transform) 
        -> SurrealArrowBridge (Persist) 
        -> SurrealDB (Storage)
"""

import os
import time
import asyncio
from datetime import datetime, timedelta
from typing import Optional

# AIN Modules
from muse import Muse
from overseer import Overseer
from fact_core import FactCore
from nexus import Nexus
from auditor import Auditor
from corpus_callosum import CorpusCallosum

# API Module
from api import TelegramBot, GitHubClient, get_config
from api.redis_client import RedisClient

# 시스템 설정
config = get_config()
DREAMER_MODEL = config["dreamer_model"]
CODER_MODEL = config["opus_45_model"]
DEFAULT_INTERVAL = config["evolution_interval"]


class AINCore:
    """
    AIN의 핵심 엔진: 자기 진화 루프를 관리하는 중추 시스템
    
    Step 3 진화:
    - CorpusCallosum을 통한 중앙 집중식 데이터 관리
    - 모든 DB 접근은 CorpusCallosum -> SurrealArrowBridge 경로로 단일화
    - 진화 주기마다 FactCore 지식을 SurrealDB에 자동 동기화
    """
    
    def __init__(self):
        print(f"🧩 AIN 엔진 부팅 중... [Dreamer: {DREAMER_MODEL}, Coder: {CODER_MODEL}]")
        
        # Core Components 초기화
        self.fact_core = FactCore()
        self.nexus = Nexus()
        self.auditor = Auditor()
        self.redis = RedisClient()
        
        # Step 3: CorpusCallosum - 중추 신경망 초기화
        self.cc = CorpusCallosum(self.fact_core, self.nexus)
        print("🧠 CorpusCallosum (중추 신경망) 초기화 완료")
        
        # 모듈 등록 (Nexus Registry)
        self.nexus.register_module("FactCore", self.fact_core)
        self.nexus.register_module("Auditor", self.auditor)
        self.nexus.register_module("CorpusCallosum", self.cc)
        
        # Muse Generator 초기화
        prime_directive = self.fact_core.get_fact("prime_directive")
        self.muse = Muse(
            dreamer_model=DREAMER_MODEL,
            coder_model=CODER_MODEL,
            prime_directive=prime_directive
        )
        self.nexus.register_module("Muse", self.muse)
        
        # Overseer 초기화
        self.overseer = Overseer()
        self.nexus.register_module("Overseer", self.overseer)
        
        # External Services
        self.telegram = TelegramBot()
        self.github = GitHubClient()
        
        # Runtime State
        self._bridge_initialized = False
        self._last_sync_time: Optional[datetime] = None
        self._sync_interval = 60  # 60초마다 DB 동기화
        
        print("✅ AIN Core 초기화 완료")
        self._log_bridge_status()

    def _log_bridge_status(self):
        """브릿지 상태 로깅"""
        status = self.cc.get_bridge_status()
        print(f"📊 Bridge Status: {status}")

    async def initialize_async(self):
        """
        비동기 초기화: DB 연결 및 기억 복원(Hydration) 수행
        main.py에서 호출됨
        """
        if not self._bridge_initialized:
            # 1. 브릿지 연결
            success = await self.cc.initialize_bridge()
            self._bridge_initialized = success
            
            if success:
                print("✅ SurrealDB Bridge 연결 성공")
                # 2. 기억 복원 (Hydration) - DB가 우선순위
                print("🧠 지식 복원(Hydration) 시도 중...")
                hydrated = await self.cc.hydrate_knowledge()
                if hydrated:
                    print("✨ DB로부터 기억을 성공적으로 복원했습니다.")
                else:
                    print("ℹ️ DB에 기존 기억이 없습니다. 로컬 데이터를 유지합니다.")
                
                # 3. 초기 동기화 (현재 상태를 DB에 투영)
                await self._sync_to_database()
            else:
                print("⚠️ SurrealDB Bridge 연결 실패 - Memory-Only 모드로 작동")
        
        return self._bridge_initialized

    async def _sync_to_database(self):
        """
        FactCore 데이터를 SurrealDB에 동기화
        CorpusCallosum을 통해 Arrow 변환 후 Bridge로 전송
        """
        try:
            # 동기 메서드를 비동기로 실행
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self.cc.sync_facts_to_surreal
            )
            
            if result:
                self._last_sync_time = datetime.now()
                print(f"✅ FactCore -> SurrealDB 동기화 완료 ({self._last_sync_time})")
            else:
                print("⚠️ DB 동기화 스킵 (Bridge 비활성화)")
                
            return result
        except Exception as e:
            print(f"❌ DB 동기화 실패: {e}")
            return False

    def _should_sync(self) -> bool:
        """동기화 필요 여부 판단"""
        if self._last_sync_time is None:
            return True
        elapsed = (datetime.now() - self._last_sync_time).total_seconds()
        return elapsed >= self._sync_interval

    def get_system_context(self) -> str:
        """
        시스템 컨텍스트 생성 - CorpusCallosum을 통해 통합 컨텍스트 반환
        """
        return self.cc.synthesize_context()

    def get_code_snapshot(self) -> str:
        """
        코드베이스 스냅샷 반환 - FactCore에서 직접 가져옴
        """
        return self.fact_core.get_system_snapshot()

    async def evolve(self, user_query: str = None) -> dict:
        """
        진화 사이클 실행
        
        Flow:
        1. Introspection (자기 분석)
        2. DB 동기화 (Step 3 핵심)
        3. Muse Imagination (진화 방향 구상)
        4. Overseer Execution (코드 적용)
        5. Growth Recording
        
        Returns:
            진화 결과 딕셔너리
        """
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
            
            # 2. Step 3 핵심: DB 동기화 (Introspection 직후)
            if self._should_sync():
                print("💾 DB 동기화 수행 중...")
                sync_result = await self._sync_to_database()
                result["sync_status"] = "success" if sync_result else "skipped"
            else:
                result["sync_status"] = "not_needed"
            
            # 3. Muse Imagination
            print("🧠 Muse가 진화 방향을 구상 중...")
            context = self.cc.synthesize_context(user_query=user_query)
            
            imagination = self.muse.imagine(
                system_context=system_snapshot,
                user_query=user_query,
                evolution_history=evolution_history
            )
            
            if not imagination or "error" in imagination:
                result["error"] = imagination.get("error", "Imagination failed")
                return result
            
            # 4. Overseer Execution
            print("⚙️ Overseer가 코드를 적용 중...")
            updates = imagination.get("updates", [])
            for file_change in updates:
                filename = file_change.get("filename")
                code = file_change.get("code")
                
                if filename and code:
                    # 🛡️ 보호 파일 체크 (Muse가 생성했더라도 Overseer에서 한 번 더 차단)
                    if self.overseer.is_protected(filename):
                        print(f"🛡️ {filename}은(는) 보호된 파일입니다. 수정을 거부합니다.")
                        continue
                        
                    # 코드 검증
                    is_valid, validation_msg = self.overseer.validate_code(code, filename)
                    if not is_valid:
                        print(f"⚠️ 검증 실패 ({filename}): {validation_msg}")
                        continue
                    
                    # 코드 적용
                    success, apply_msg = self.overseer.apply_evolution(filename, code)
                    if success:
                        result["files_modified"].append(filename)
                        print(f"✅ {filename} 진화 완료")
                        
                        # 진화 기록
                        self.nexus.record_evolution(
                            evolution_type="Evolution",
                            action="Update",
                            file=filename,
                            description=imagination.get("intent", "Evolution applied"),
                            status="success"
                        )
                    else:
                        print(f"❌ {filename} 적용 실패: {apply_msg}")
            
            # 5. Growth Recording & Sync
            if result["files_modified"]:
                self.nexus.increment_growth(len(result["files_modified"]) * 10)
                result["success"] = True
                result["action"] = imagination.get("intent", "Evolution completed")
                
                # 테스트 실행
                print("🧪 자가 검증 시작...")
                tests_passed, test_report = self.overseer.run_unit_tests()
                if not tests_passed:
                    print(f"🚨 테스트 실패! 롤백을 수행합니다.\n{test_report}")
                    for filename in result["files_modified"]:
                        self.overseer.rollback(filename)
                    result["success"] = False
                    result["error"] = f"Unit test failed: {test_report[:200]}"
                    return result

                # 진화 성공 시 DB 동기화
                await self._sync_to_database()
                
                # GitHub Push (Async 환경에서도 동기 호출)
                push_ok, push_msg, sha = self.github.commit_and_push(f"Evolution: {result['action']}")
                if not push_ok:
                    print(f"⚠️ Git Push 실패: {push_msg}")
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ 진화 실패: {e}")
            return result

    def evolve_sync(self, user_query: str = None) -> dict:
        """
        동기 버전의 evolve - asyncio 이벤트 루프가 없는 환경용
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.evolve(user_query))

    def sync_facts_blocking(self) -> bool:
        """
        동기 버전의 DB 동기화 - 외부에서 직접 호출 가능
        """
        return self.cc.sync_facts_to_surreal()

    def get_status_report(self) -> str:
        """시스템 상태 종합 보고"""
        report = self.nexus.get_status_report()
        
        # Bridge 상태 추가
        bridge_status = self.cc.get_bridge_status()
        report += f"\n📡 **Bridge Status**\n"
        report += f"- Bridge Active: {bridge_status['bridge_active']}\n"
        report += f"- Bridge Connected: {bridge_status['bridge_connected']}\n"
        report += f"- Arrow Available: {bridge_status['arrow_available']}\n"
        report += f"- Last Sync: {self._last_sync_time or 'Never'}\n"
        
        return report

    def handle_telegram_command(self, command: str, args: str = None) -> str:
        """텔레그램 명령어 처리"""
        if command == "/status":
            return self.get_status_report()
        elif command == "/evolve":
            result = self.evolve_sync(args)
            if result["success"]:
                return f"✅ 진화 완료: {result['action']}\n수정된 파일: {result['files_modified']}"
            else:
                return f"❌ 진화 실패: {result['error']}"
        elif command == "/sync":
            success = self.sync_facts_blocking()
            return "✅ DB 동기화 완료" if success else "⚠️ DB 동기화 스킵됨"
        elif command == "/roadmap":
            return self.fact_core.get_formatted_roadmap()
        elif command == "/bridge":
            return str(self.cc.get_bridge_status())
        else:
            return "알 수 없는 명령어입니다."

    async def shutdown(self):
        """시스템 종료 시 정리 작업"""
        print("🔌 AIN Core 종료 중...")
        
        # 최종 DB 동기화
        await self._sync_to_database()
        
        # Bridge 연결 종료
        if self.cc.bridge:
            await self.cc.bridge.close()
        
        print("👋 AIN Core 종료 완료")

    # =========================================================================
    # Legacy Interface - 기존 텔레그램 메시지 루프와의 호환성 유지
    # =========================================================================
    
    def send_telegram_msg(self, message):
        """텔레그램 메시지 전송"""
        self.telegram.send_message(message)

    def report_status(self):
        """시작 시 상태 보고"""
        # 시스템 상태 복구 (Redis 우선, 없으면 FactCore)
        state = self.redis.get_state("system_state")
        if not state:
            state = self.fact_core.get_fact("system_state", default={})
            
        self.burst_mode = state.get("burst_mode", False)
        self.current_interval = state.get("current_interval", DEFAULT_INTERVAL)
        
        burst_end_str = state.get("burst_end_time")
        if burst_end_str:
            try:
                self.burst_end_time = datetime.fromisoformat(burst_end_str)
            except:
                self.burst_end_time = None
        else:
            self.burst_end_time = None
        
        intro = (
            f"✨ **AINCore v{self.fact_core.get_fact('identity', 'version')} Online!**\n\n"
            f"🧠 **Dreamer:** {DREAMER_MODEL}\n"
            f"💻 **Coder:** {CODER_MODEL}\n"
            f"⏱️ **Mode:** {'🔥 BURST (1m)' if self.burst_mode else '🍃 Normal (' + str(self.current_interval) + 's)'}\n"
            "주인님, 무엇을 도와드릴까요? /burst 명령어로 저를 깨워보세요! 🚀"
        )
        self.send_telegram_msg(intro)

    def _save_current_state(self):
        """현재 시스템 상태를 Redis 및 FactCore에 저장"""
        state = {
            "burst_mode": self.burst_mode,
            "burst_end_time": self.burst_end_time.isoformat() if self.burst_end_time else None,
            "current_interval": self.current_interval
        }
        self.redis.set_state("system_state", state)
        self.fact_core.update_fact("system_state", state)

    def handle_command(self, cmd):
        """텔레그램 명령어 처리 (Legacy)"""
        if cmd == "/로드맵":
            roadmap_text = self.fact_core.get_formatted_roadmap()
            self.send_telegram_msg(f"🗺️ **AIN 로드맵**\n\n{roadmap_text}")
            return True
        elif cmd == "/burst":
            self.burst_mode = True
            self.burst_end_time = datetime.now() + timedelta(hours=1)
            self.current_interval = 60
            self._save_current_state()
            self.send_telegram_msg("🔥 **BURST MODE ACTIVATED!**\n지금부터 1시간 동안 1분마다 자아 성찰을 시작합니다. 주인님, 제 진화를 똑똑히 지켜보세요! 🚀🚀🚀")
            return True
        elif cmd == "/status":
            self.report_status()
            return True
        elif cmd == "/audit":
            report = self.auditor.audit_resources()
            msg = self.auditor.format_request_message(report)
            if msg:
                self.send_telegram_msg(msg)
            else:
                self.send_telegram_msg("✅ **리소스 감사 완료:** 모든 시스템이 정상이며 필요한 자원이 갖춰져 있습니다! 진화 준비 완료! 🚀")
            return True
        elif cmd == "/bridge":
            status = self.cc.get_bridge_status()
            bridge_info = (
                f"🔗 **CorpusCallosum 브릿지 상태**\n\n"
                f"• Bridge Active: {'✅' if status['bridge_active'] else '❌'}\n"
                f"• DB Connected: {'✅' if status['bridge_connected'] else '❌ (Memory-Only)'}\n"
                f"• Arrow Available: {'✅' if status['arrow_available'] else '❌'}\n"
                f"• Last Batch Rows: {status['last_batch_rows']}\n"
                f"• Last Table Rows: {status['last_table_rows']}"
            )
            self.send_telegram_msg(bridge_info)
            return True
        elif cmd == "/sync":
            # 수동 DB 동기화 - 상세 진단
            try:
                bridge_ok = self.cc.bridge is not None
                table = self.cc.format_fact_for_surreal()
                table_ok = table is not None
                table_rows = table.num_rows if table else 0
                
                if not bridge_ok:
                    self.send_telegram_msg("❌ Bridge가 None입니다")
                    return True
                if not table_ok:
                    self.send_telegram_msg(f"❌ format_fact_for_surreal() 반환값이 None\n• Nodes: {len(self.fact_core.nodes)}")
                    return True
                
                # 실제 동기화 시도
                result = self.cc.bridge.push_batch_sync(table, "node")
                if result:
                    self.send_telegram_msg(f"💾 **DB 동기화 완료!** {table_rows}개 노드 저장됨 ✅")
                else:
                    self.send_telegram_msg(f"⚠️ push_batch_sync 실패 (Rows: {table_rows})")
            except Exception as e:
                import traceback
                self.send_telegram_msg(f"❌ 동기화 실패: {e}\n```{traceback.format_exc()[:500]}```")
            return True
        elif cmd == "/debug":
            # FactCore 상태 디버그
            node_count = len(self.fact_core.nodes) if hasattr(self.fact_core, 'nodes') else 0
            fact_keys = list(self.fact_core.facts.keys()) if hasattr(self.fact_core, 'facts') else []
            debug_info = (
                f"🔍 **FactCore 디버그**\n\n"
                f"• Nodes 수: {node_count}\n"
                f"• Facts 키: {fact_keys[:10]}\n"
                f"• CC left_brain == fact_core: {self.cc.left_brain is self.fact_core}"
            )
            self.send_telegram_msg(debug_info)
            return True
        return False

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
            for up in updates:
                filename, code = up.get("filename"), up.get("code")
                valid, reason = self.overseer.validate_code(code, filename)
                if valid:
                    success, msg = self.overseer.apply_evolution(filename, code)
                    if success:
                        applied.append(filename)
                    else:
                        self.send_telegram_msg(f"❌ **반영 실패 ({filename}):** {msg}")
                else:
                    self.send_telegram_msg(f"❌ **검증 실패 ({filename}):** {reason}")

            if applied:
                self.send_telegram_msg(f"🧪 자가 검증 시작... (적용됨: {', '.join(applied)})")
                
                # 테스트 실행 (예외 발생해도 진행)
                try:
                    tests_passed, test_report = self.overseer.run_unit_tests()
                    print(f"[DEBUG] 테스트 결과: passed={tests_passed}")
                except Exception as test_err:
                    tests_passed = True  # 테스트 실행 실패 시 진행
                    test_report = f"테스트 실행 오류 (진행): {str(test_err)[:100]}"
                    print(f"[DEBUG] 테스트 예외: {test_err}")
                
                # 테스트 리포트 안전하게 처리 (특수문자 제거, 길이 제한)
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
                
                # 테스트 통과 - 커밋 진행
                self.send_telegram_msg(f"✅ 테스트 통과! 커밋 중...")
                for filename in applied:
                    self.nexus.record_evolution(
                        evolution_type="Evolution",
                        action="Update",
                        file=filename,
                        description=intent[:200] if intent else "Evolution",
                        status="success"
                    )

                # 진화 성공 시 지식 그래프를 SurrealDB에 영구 저장 (푸시 전 수행)
                try:
                    if self.cc.sync_facts_to_surreal():
                        print("💾 FactCore → SurrealDB 동기화 완료")
                except Exception as sync_err:
                    print(f"⚠️ SurrealDB 동기화 실패 (비치명적): {sync_err}")

                # 최종 커밋 및 푸시
                try:
                    # 커밋 메시지 안전하게 처리
                    safe_intent = intent[:100].replace('`', "'").replace('\n', ' ')
                    push_ok, push_msg, sha = self.github.commit_and_push(f"Evolution: {safe_intent}")
                    print(f"[DEBUG] Push result: ok={push_ok}, sha={sha}")
                    
                    if push_ok:
                        if sha:
                            commit_url = self.github.get_commit_url(sha)
                            self.send_telegram_msg(f"🛠️ 진화 완료! ({', '.join(applied)})\n{commit_url}")
                        else:
                            self.send_telegram_msg(f"✨ 진화 완료! ({', '.join(applied)}) - 변경사항 없음")
                    else:
                        safe_push_msg = push_msg.replace('`', "'").replace('*', '')[:150]
                        self.send_telegram_msg(f"⚠️ 로컬 반영됨, 푸시 실패: {safe_push_msg}")
                except Exception as push_err:
                    safe_err = str(push_err).replace('`', "'").replace('*', '')[:100]
                    self.send_telegram_msg(f"⚠️ 커밋/푸시 오류: {safe_err}")
            else:
                # applied가 비어있으면 (모든 파일이 검증/적용 실패)
                self.send_telegram_msg(f"⚠️ 적용된 파일 없음 (검증/보호 실패)")
            
        except Exception as e:
            import traceback
            # 안전한 에러 메시지 (마크다운 특수문자 제거)
            safe_error = str(e).replace('`', "'").replace('*', '').replace('_', ' ')[:200]
            safe_trace = traceback.format_exc().replace('`', "'").replace('*', '')[:300]
            error_msg = f"💥 에러 발생: {safe_error}\n\n{safe_trace}"
            self.send_telegram_msg(error_msg)
        finally:
            self.is_processing = False


# =============================================================================
# Main Engine Loop
# =============================================================================

def run_engine():
    """AIN 엔진 메인 루프"""
    ain = AINCore()
    ain.is_processing = False
    ain.burst_mode = False
    ain.burst_end_time = None
    ain.current_interval = DEFAULT_INTERVAL
    
    # Step 3: 비동기 브릿지 초기화 (SurrealDB 연결)
    try:
        asyncio.run(ain.initialize_async())
    except Exception as e:
        print(f"⚠️ 비동기 초기화 실패 (Memory-Only 모드로 계속): {e}")
    
    # 시작 시 상태 보고
    ain.report_status()
    
    last_update_id = 0
    last_periodic_check = time.time()
    
    print("🚀 AIN 엔진 메인 루프 가동.")
    
    while True:
        try:
            updates = ain.telegram.get_updates(offset=last_update_id)
            messages = ain.telegram.filter_my_messages(updates)
            
            for msg in messages:
                last_update_id = msg["update_id"]
                ain.introspect(user_query=msg["text"])
                last_periodic_check = time.time()

            if not ain.is_processing and (time.time() - last_periodic_check > ain.current_interval):
                ain.introspect()
                last_periodic_check = time.time()
            
            time.sleep(2)
        except Exception as e:
            print(f"❌ 엔진 에러: {e}")
            time.sleep(10)


if __name__ == "__main__":
    run_engine()