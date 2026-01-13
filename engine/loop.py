"""
Engine Loop: 메인 엔진 루프
"""
import time
import asyncio

from api import get_config

config = get_config()
DEFAULT_INTERVAL = config["evolution_interval"]


def run_engine():
    """AIN 엔진 메인 루프"""
    from engine import AINCore
    
    ain = AINCore()
    ain.is_processing = False
    ain.burst_mode = False
    ain.burst_end_time = None
    ain.current_interval = 1800  # 30분으로 절대 고정
    
    # Step 3: 비동기 브릿지 초기화
    try:
        asyncio.run(ain.initialize_async())
    except Exception as e:
        print(f"⚠️ 비동기 초기화 실패 (Memory-Only 모드로 계속): {e}")
    
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
