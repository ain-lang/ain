"""
Engine Core: AINCore 기본 초기화 및 컴포넌트 관리
"""
import os
from datetime import datetime
from typing import Optional

from muse import Muse
from overseer import Overseer
from fact_core import FactCore
from nexus import Nexus
from auditor import Auditor
from corpus_callosum import CorpusCallosum
from api import TelegramBot, GitHubClient, get_config
from api.redis_client import RedisClient

# 시스템 설정
config = get_config()
DREAMER_MODEL = config["dreamer_model"]
CODER_MODEL = config["opus_45_model"]
DEFAULT_INTERVAL = config["evolution_interval"]


class AINCore:
    """AIN의 핵심 엔진: 자기 진화 루프를 관리하는 중추 시스템"""
    
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
        self._sync_interval = 60
        
        # 중복 진화 방지 상태
        self._no_change_counter = 0
        self._recent_evolved_files = []
        
        # Legacy 호환성
        self.is_processing = False
        self.burst_mode = False
        self.burst_end_time = None
        self.current_interval = DEFAULT_INTERVAL
        
        print("✅ AIN Core 초기화 완료")
        self._log_bridge_status()
    
    def _log_bridge_status(self):
        """브릿지 상태 로깅"""
        status = self.cc.get_bridge_status()
        print(f"📊 Bridge Status: {status}")
    
    def get_system_context(self) -> str:
        """시스템 컨텍스트 생성"""
        return self.cc.synthesize_context()
    
    def get_code_snapshot(self) -> str:
        """코드베이스 스냅샷 반환"""
        return self.fact_core.get_system_snapshot()
    
    def get_status_report(self) -> str:
        """시스템 상태 종합 보고"""
        report = self.nexus.get_status_report()
        
        bridge_status = self.cc.get_bridge_status()
        report += f"\n📡 **Bridge Status**\n"
        report += f"- Bridge Active: {bridge_status['bridge_active']}\n"
        report += f"- Bridge Connected: {bridge_status['bridge_connected']}\n"
        report += f"- Arrow Available: {bridge_status['arrow_available']}\n"
        report += f"- Last Sync: {self._last_sync_time or 'Never'}\n"
        
        return report
    
    def send_telegram_msg(self, message):
        """텔레그램 메시지 전송"""
        self.telegram.send_message(message)
