import redis
import json
from api.keys import get_config

class RedisClient:
    """
    AIN State Manager (Redis):
    시스템의 휘발성 상태(Burst Mode, Interval 등)를 영구적으로 관리한다.
    서버 재시작(Rebuild) 상황에서도 상태를 유지하는 것이 목표.
    """
    def __init__(self):
        config = get_config()
        self.redis_url = config.get("redis_url")
        self.client = None
        
        if self.redis_url:
            try:
                # 외부 Redis 연결 안정성을 위해 retry 설정 추가
                self.client = redis.from_url(
                    self.redis_url, 
                    decode_responses=True,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                print("🔌 외부 Redis 연결 성공 (상태 관리용)")
            except Exception as e:
                print(f"⚠️ Redis 연결 실패: {e}")
        else:
            print("ℹ️ REDIS_URL이 설정되지 않았습니다. 파일 기반 상태 관리를 유지합니다.")

    def set_state(self, key: str, value: any):
        """상태 저장"""
        if not self.client: return False
        try:
            serialized = json.dumps(value)
            self.client.set(f"ain:state:{key}", serialized)
            return True
        except Exception as e:
            print(f"❌ Redis 저장 에러 ({key}): {e}")
            return False

    def get_state(self, key: str, default=None):
        """상태 인출"""
        if not self.client: return default
        try:
            data = self.client.get(f"ain:state:{key}")
            if data:
                return json.loads(data)
            return default
        except Exception as e:
            print(f"❌ Redis 인출 에러 ({key}): {e}")
            return default

    def set_burst_mode(self, end_time_iso: str, interval: int):
        """버스트 모드 전용 상태 저장"""
        state = {
            "burst_mode": True,
            "burst_end_time": end_time_iso,
            "current_interval": interval
        }
        self.set_state("system_state", state)

    def clear_burst_mode(self):
        """버스트 모드 종료 시 초기화"""
        state = {
            "burst_mode": False,
            "burst_end_time": None,
                        "current_interval": 3600 # Default 1h
        }
        self.set_state("system_state", state)
