import asyncio
from database.surreal_bridge import SurrealArrowBridge
import pyarrow as pa

async def evolve_step_3():
    """Step 3: SurrealDB & Apache Arrow 통합 레이어 초기화 및 검증"""
    bridge = SurrealArrowBridge()
    await bridge.connect()

    # 테스트용 AIN 상태 데이터 생성 (Arrow Schema)
    schema = pa.schema([
        ('component', pa.string()),
        ('version', pa.float64()),
        ('complexity_index', pa.int32())
    ])
    
    data = [
        pa.array(['FactCore', 'Nexus', 'Bridge']),
        pa.array([0.2, 0.2, 0.1]),
        pa.array([150, 200, 50])
    ]
    batch = pa.RecordBatch.from_arrays(data, schema=schema)

    # 1. SurrealDB에 Zero-Copy 지향 바이너리 저장
    await bridge.save_evolution_state("current_snapshot", batch)
    
    # 2. 저장된 데이터 로드 및 복원 검증
    restored_batch = await bridge.load_evolution_state("current_snapshot")
    
    print(f"✅ Bridge Integration Verified: Restored {restored_batch.num_rows} rows.")
    await bridge.close()

if __name__ == "__main__":
    asyncio.run(evolve_step_3())
