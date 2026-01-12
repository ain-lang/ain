"""
Engine Sync: DB 동기화 관련 기능
"""
import asyncio
from datetime import datetime


class SyncMixin:
    """DB 동기화 믹스인 - AINCore에서 사용"""
    
    async def initialize_async(self):
        """비동기 초기화: DB 연결 및 기억 복원(Hydration)"""
        if not self._bridge_initialized:
            success = await self.cc.initialize_bridge()
            self._bridge_initialized = success
            
            if success:
                print("✅ SurrealDB Bridge 연결 성공")
                print("🧠 지식 복원(Hydration) 시도 중...")
                hydrated = await self.cc.hydrate_knowledge()
                if hydrated:
                    print("✨ DB로부터 기억을 성공적으로 복원했습니다.")
                else:
                    print("ℹ️ DB에 기존 기억이 없습니다. 로컬 데이터를 유지합니다.")
                
                await self._sync_to_database()
            else:
                print("⚠️ SurrealDB Bridge 연결 실패 - Memory-Only 모드로 작동")
        
        return self._bridge_initialized

    async def _sync_to_database(self):
        """FactCore 데이터를 SurrealDB에 동기화"""
        try:
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

    def sync_facts_blocking(self) -> bool:
        """동기 버전의 DB 동기화"""
        return self.cc.sync_facts_to_surreal()

    async def shutdown(self):
        """시스템 종료 시 정리 작업"""
        print("🔌 AIN Core 종료 중...")
        await self._sync_to_database()
        
        if self.cc.bridge:
            await self.cc.bridge.close()
        
        print("👋 AIN Core 종료 완료")
