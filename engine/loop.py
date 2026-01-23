"""
Engine Loop: 메인 엔진 루프
Step 7: Meta-Cognition 통합 - 메타인지 시스템 활성화 및 상태 영속화
Step 8: Intuition 통합 - DecisionGate를 통한 System 1/2 분기
Step 9: Temporal Self 통합 - 주관적 시간(Subjective Time) 인식 활성화
"""
import time
import asyncio
import traceback

from api import get_config

# Step 7: Meta-Cognition
from engine.meta_integration import activate_meta_cognition, tick_meta_cognition
from engine.meta_persistence import sync_cognitive_state
from engine.loop_strategy import get_loop_strategy_manager, initialize_loop_strategy

# Step 8: Intuition & Decision Gate
from engine.decision_gate import DecisionGate, ExecutionPath

# Step 9: Temporal Self
from engine.temporal_integration import activate_temporal_awareness, tick_temporal_integration

config = get_config()
DEFAULT_INTERVAL = config["evolution_interval"]


def run_engine():
    """AIN 엔진 메인 루프"""
    from engine import AINCore

    # 1. Core Initialization
    ain = AINCore()
    ain.is_processing = False
    ain.burst_mode = False
    ain.burst_end_time = None

    # 2. Component Initialization
    decision_gate = DecisionGate(ain)

    try:
        asyncio.run(ain.initialize_async())
    except Exception as e:
        print(f"⚠️ 비동기 초기화 실패 (Memory-Only 모드로 계속): {e}")

    # 3. Consciousness Loop (Independent Thread-like)
    try:
        ain.init_consciousness()
        print("💭 의식 루프 활성화 (진화와 독립 작동)")
    except Exception as e:
        print(f"⚠️ 의식 루프 초기화 실패: {e}")

    # 4. Intention System
    try:
        ain.init_intention_system()
        print("🎯 목표 관리 시스템 활성화")
    except Exception as e:
        print(f"⚠️ 의식적 목표 시스템 초기화 실패: {e}")

    # 5. Temporal Self (Step 9)
    try:
        if hasattr(ain, "init_temporal"):
            ain.init_temporal()
            print("⏳ 시간적 자아(Temporal Self) 내부 초기화 완료")
    except Exception as e:
        print(f"⚠️ 시간적 자아 초기화 실패: {e}")

    # 6. Activation of Cognitive Layers
    # [Step 7] Meta-Cognition
    meta_active = activate_meta_cognition(ain)
    if meta_active:
        print("🧠 메타인지 시스템(Self-Monitoring) 활성화됨")

    # [Step 9] Temporal Self Activation via Integration Module
    temporal_active = activate_temporal_awareness(ain)
    if temporal_active:
        print("⏳ Temporal Self Activated (Subjective Time Flowing)")

    # 7. Loop Strategy Initialization
    try:
        initial_interval = initialize_loop_strategy(ain)
        ain.current_interval = initial_interval
    except Exception as e:
        print(f"⚠️ LoopStrategyManager 초기화 실패, 기본값 사용: {e}")
        ain.current_interval = DEFAULT_INTERVAL

    ain.report_status()

    last_update_id = 0
    last_periodic_check = time.time()
    ain._last_evolution_time = 0

    loop_manager = get_loop_strategy_manager()

    print("🚀 AIN 엔진 메인 루프 가동.")
    print(f"   └─ 진화: {ain.current_interval}초마다 | 독백: 진화 후 1시간 | 메타인지: 10분마다 | 시간틱: 1초")

    # 8. Main Runtime Loop
    while True:
        try:
            # --- Telegram Message Polling ---
            updates = ain.telegram.get_updates(offset=last_update_id)
            messages = ain.telegram.filter_my_messages(updates)

            for msg in messages:
                last_update_id = msg["update_id"]
                ain.introspect(user_query=msg["text"])
                last_periodic_check = time.time()

            # --- High-Frequency Ticks (1s resolution) ---

            # [Step 9] Temporal Tick: 주관적 시간 감각 갱신
            tick_temporal_integration(ain)

            # --- Consciousness Cycle ---
            try:
                consciousness_result = ain.run_consciousness_cycle()
                if consciousness_result.get("monologue_triggered"):
                    print("💭 내부 독백 완료")
            except Exception:
                pass

            # --- Meta-Cognition Tick (10분 주기 내부 관리) ---
            try:
                meta_result = tick_meta_cognition(ain)
                if meta_result and not meta_result.get("error"):
                    print("🧠 메타인지 사이클 완료")

                    if loop_manager.update_from_strategy_adapter():
                        loop_manager.apply_to_core(ain)
            except Exception:
                pass

            # --- Persistence: 인지 상태 영속화 (FactCore 동기화) ---
            try:
                sync_cognitive_state(ain)
            except Exception:
                pass

            # --- Execution Cycle (Evolution Decision) ---
            current_ts = time.time()

            if not ain.is_processing and (current_ts - last_periodic_check > ain.current_interval):
                try:
                    # [Step 8] Decision Gate: 직관(Fast) vs 추론(Slow) 분기
                    decision = asyncio.run(decision_gate.process_decision())

                    if decision["path"] == "reflex" and decision["executed"]:
                        print(f"⚡ 반사 행동 완료: {decision['result']}")
                        last_periodic_check = current_ts
                        time.sleep(1)
                        continue
                except Exception as gate_err:
                    print(f"⚠️ DecisionGate 오류: {gate_err}")

                # 기존의 심층 진화(Dreamer) 경로 실행
                ain.introspect()
                last_periodic_check = current_ts
                ain._last_evolution_time = current_ts
                ain._last_monologue_time = current_ts

            # CPU 과부하 방지 및 Temporal Tick 해상도 유지 (1초)
            time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 AIN 엔진 종료 요청됨.")
            break
        except Exception as e:
            print(f"❌ 엔진 에러: {e}")
            traceback.print_exc()
            time.sleep(10)


if __name__ == "__main__":
    run_engine()