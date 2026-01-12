import ctypes
import pyarrow as pa
import numpy as np

class ZeroCopyBufferExposer:
    """
    SurrealDB에서 추출된 원시 메모리 버퍼를 
    Arrow의 C Data Interface 구조체로 노출하여 복사를 0으로 유지함.
    """
    def __init__(self):
        # Arrow Schema/Array C 구조체 정의 (메모리 레이아웃 매핑)
        class ArrowArray(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_int64),
                ("null_count", ctypes.c_int64),
                ("offset", ctypes.c_int64),
                ("n_buffers", ctypes.c_int64),
                ("n_children", ctypes.c_int64),
                ("buffers", ctypes.POINTER(ctypes.c_void_p)),
                ("children", ctypes.c_void_p),
                ("dictionary", ctypes.c_void_p),
                ("release", ctypes.c_void_p),
                ("private_data", ctypes.c_void_p),
            ]
        self.ArrowArray = ArrowArray

    def expose_numpy_buffer(self, np_array):
        """
        Numpy 배열을 Arrow Buffer로 변환 (Zero-Copy)
        """
        return pa.py_buffer(np_array)

    def expose_raw_ptr_to_arrow(self, ptr, length, dtype):
        """
        물리 주소(ptr)를 받아 pyarrow.Array로 즉시 승격.
        이 과정에서 데이터의 물리적 복사는 발생하지 않음.
        """
        # 1. 포인터를 numpy buffer로 뷰 생성 (복사 없음)
        buffer_size = length * np.dtype(dtype).itemsize
        raw_array = np.frombuffer(
            (ctypes.c_char * buffer_size).from_address(ptr), 
            dtype=dtype
        )

        # 2. numpy array를 arrow buffer로 래핑
        arrow_buffer = pa.py_buffer(raw_array)
        
        # 3. 데이터 타입에 따른 Arrow Array 생성
        # null 비트맵은 존재하지 않는 것으로 간주 (null_count=0)
        return pa.Array.from_buffers(
            pa.from_numpy_dtype(np.dtype(dtype)),
            length,
            [None, arrow_buffer] # [null_bitmap, data_buffer]
        )

    def link_relation_stream(self, relation_data_ptr, count):
        """
        SurrealDB RELATION(Edge)의 ID 쌍을 Arrow Table로 고속 바인딩
        """
        # Edge 데이터는 보통 2개의 ID(int64_t x 2)로 구성된다고 가정
        # relation_data_ptr는 [in_id, out_id, in_id, out_id, ...] 형태의 연속 메모리
        
        in_ids = self.expose_raw_ptr_to_arrow(relation_data_ptr, count, np.int64)
        out_ids = self.expose_raw_ptr_to_arrow(
            relation_data_ptr + (count * 8), # offset by in_ids size
            count, 
            np.int64
        )
        
        return pa.Table.from_arrays([in_ids, out_ids], names=['in', 'out'])

# AIN 진화 로직: 
# 이제 SurrealDB의 Rust 엔진이 메모리에 직접 쓴 데이터를
# Python은 주소값만 전달받아 즉시 Arrow 연산(Vectorized Logic)에 투입 가능.