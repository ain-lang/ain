"""
AIN Database Layer Package
==========================
고속 데이터 파이프라인을 위한 통합 데이터베이스 레이어

주요 컴포넌트:
- SurrealArrowBridge: SurrealDB ↔ Arrow 양방향 브릿지 (SSOT)
- ArrowBufferManager: 메모리 효율적 버퍼 관리
- ZeroCopyBufferExposer: C Data Interface 기반 Zero-Copy
- ArrowDiskSpiller: 대용량 데이터 디스크 스필링

Usage:
    from database import SurrealArrowBridge, get_bridge
    
    # 방법 1: 직접 인스턴스 생성
    bridge = SurrealArrowBridge()
    await bridge.connect()
    
    # 방법 2: 싱글톤 사용
    bridge = get_bridge()
    
    # 방법 3: 컨텍스트 매니저
    async with SurrealArrowBridge() as bridge:
        await bridge.push_batch("table_name", data)

DEPRECATED (이 패키지로 대체됨):
- bridge.py (루트)
- bridge_core.py (루트)
- nexus_bridge.py (루트)
"""

# Core Bridge (SSOT) - 항상 사용 가능
from .surreal_bridge import (
    SurrealArrowBridge,
    ArrowBufferManager,
    get_bridge,
    get_connected_bridge,
    quick_push,
    quick_pull
)

# Zero-Copy Utilities - 선택적 임포트
try:
    from .zero_copy import ZeroCopyBufferExposer
    HAS_ZERO_COPY = True
except ImportError:
    HAS_ZERO_COPY = False

# Disk Spiller - 선택적 임포트
try:
    from .arrow_spiller import ArrowDiskSpiller
    HAS_SPILLER = True
except ImportError:
    HAS_SPILLER = False

# C Data Interface - 선택적 임포트
try:
    from .c_data_interface import CDataBridge
    HAS_C_DATA = True
except ImportError:
    HAS_C_DATA = False

# LanceDB Vector Bridge (Step 4) - 선택적 임포트
try:
    from .lance_bridge import LanceBridge, get_lance_bridge
    HAS_LANCE = True
except ImportError:
    HAS_LANCE = False

__all__ = [
    # Core (필수)
    "SurrealArrowBridge",
    "ArrowBufferManager",
    "get_bridge",
    "get_connected_bridge",
    "quick_push",
    "quick_pull",
    # Step 4: Vector Memory
    "LanceBridge",
    "get_lance_bridge",
    # Optional
    "ZeroCopyBufferExposer",
    "ArrowDiskSpiller",
    "CDataBridge",
    # Flags
    "HAS_ZERO_COPY",
    "HAS_SPILLER",
    "HAS_C_DATA",
    "HAS_LANCE",
]

__version__ = "0.4.0"  # Step 4 진입