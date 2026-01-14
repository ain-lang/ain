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
    ain.current_interval = 3600  # 1시간으로 절대 고정 (진화 주기)

    # Step 3: 비동기 브릿지 초기화
    try:
        asyncio.run(ain.initialize_async())
    except Exception as e:
        print(f"⚠️ 비동기 초기화 실패 (Memory-Only 모드로 계속): {e}")

    # 의식 시스템 초기화
    try:
        ain.init_consciousness()
        print("💭 의식 루프 활성화 (진화와 독립 작동)")
    except Exception as e:
        print(f"⚠️ 의식 시스템 초기화 실패: {e}")

    ain.report_status()

    last_update_id = 0
    last_periodic_check = time.time()

    print("🚀 AIN 엔진 메인 루프 가동.")
    print("   └─ 진화: 1시간마다 | 의식 테스트: 계속 작동")

    while True:
        try:
            # 1. 텔레그램 메시지 처리
            updates = ain.telegram.get_updates(offset=last_update_id)
            messages = ain.telegram.filter_my_messages(updates)

            for msg in messages:
                last_update_id = msg["update_id"]
                ain.introspect(user_query=msg["text"])
                last_periodic_check = time.time()

            # 2. 의식 루프 (매 틱마다 - 토큰 안 쓰는 작업들)
            try:
                consciousness_result = ain.run_consciousness_cycle()
                # 중요한 이벤트만 로그
                if consciousness_result.get("monologue_triggered"):
                    print("💭 내부 독백 완료")
            except Exception as consciousness_err:
                pass  # 의식 오류는 조용히 무시 (진화에 영향 안 줌)

            # 3. 진화 주기 체크 (1시간마다)
            if not ain.is_processing and (time.time() - last_periodic_check > ain.current_interval):
                ain.introspect()
                last_periodic_check = time.time()

            time.sleep(2)
        except Exception as e:
            print(f"❌ 엔진 에러: {e}")
            time.sleep(10)
