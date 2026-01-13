"""
Engine Handlers: 텔레그램 명령어 처리
"""
from datetime import datetime, timedelta

from api import get_config

config = get_config()
DEFAULT_INTERVAL = config["evolution_interval"]


class HandlersMixin:
    """명령어 처리 믹스인 - AINCore에서 사용"""
    
    def handle_telegram_command(self, command: str, args: str = None) -> str:
        """텔레그램 명령어 처리 (API용)"""
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

    def report_status(self):
        """시작 시 상태 보고"""
        state = self.redis.get_state("system_state")
        if not state:
            state = self.fact_core.get_fact("system_state", default={})
            
        self.burst_mode = state.get("burst_mode", False)
        
        # 🍃 Normal 모드일 때는 항상 api/keys.py의 설정을 우선 (SSOT)
        # 🚨 중요: 여기서 DEFAULT_INTERVAL(1800)이 강제 적용되어야 함
        if not self.burst_mode:
            self.current_interval = DEFAULT_INTERVAL
            print(f"📡 [Status] Normal Mode: interval set to {self.current_interval} (from DEFAULT)")
        else:
            self.current_interval = state.get("current_interval", 600)
            print(f"📡 [Status] Burst Mode: interval set to {self.current_interval}")
        
        burst_end_str = state.get("burst_end_time")
        if burst_end_str:
            try:
                self.burst_end_time = datetime.fromisoformat(burst_end_str)
            except:
                self.burst_end_time = None
        else:
            self.burst_end_time = None
        
        from engine.core import DREAMER_MODEL, CODER_MODEL
        intro = (
            f"✨ **AINCore v{self.fact_core.get_fact('identity', 'version')} Online!**\n\n"
            f"🧠 **Dreamer:** {DREAMER_MODEL}\n"
            f"💻 **Coder:** {CODER_MODEL}\n"
            f"⏱️ **Mode:** {'🔥 BURST (10m)' if self.burst_mode else '🍃 Normal (' + str(self.current_interval // 60) + 'm)'}\n"
            "주인님, 무엇을 도와드릴까요? /burst 명령어로 저를 깨워보세요! 🚀"
        )
        self.send_telegram_msg(intro)

    def _save_current_state(self):
        """현재 시스템 상태 저장"""
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
            self.current_interval = 600  # 10분
            self._save_current_state()
            self.send_telegram_msg("🔥 **BURST MODE ACTIVATED!**\n지금부터 1시간 동안 10분마다 자아 성찰을 시작합니다. 주인님, 제 진화를 똑똑히 지켜보세요! 🚀🚀🚀")
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
