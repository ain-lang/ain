"""
Step 4: Vector Memory (LanceDB) 단위 테스트
===========================================
LanceBridge와 VectorMemory의 연결, 데이터 삽입, 검색 기능을 검증한다.

테스트 항목:
1. LanceBridge 싱글톤 초기화 및 연결 상태 확인
2. 메모리 추가 (add_memory) 기능 검증
3. 벡터 검색 (search_memory) 기능 검증
4. 벡터 차원 일관성 검증
5. VectorMemory 래퍼 클래스 동작 검증
"""

import unittest
import tempfile
import shutil
import os
import sys
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# LanceDB 및 관련 모듈 임포트 (가용성 체크)
try:
    from database.lance_bridge import LanceBridge, LANCE_AVAILABLE
except ImportError:
    LANCE_AVAILABLE = False
    LanceBridge = None

try:
    from nexus.memory import VectorMemory
except ImportError:
    VectorMemory = None


class TestLanceBridge(unittest.TestCase):
    """
    LanceBridge 단위 테스트
    
    LanceDB 연결, 테이블 생성, 데이터 삽입/검색을 검증한다.
    """

    def setUp(self):
        """테스트 전 설정: 임시 디렉토리 및 싱글톤 초기화"""
        if not LANCE_AVAILABLE:
            self.skipTest("LanceDB 또는 PyArrow가 설치되지 않아 테스트를 건너뜁니다.")
        
        # 테스트용 임시 디렉토리 생성
        self.test_dir = tempfile.mkdtemp()
        
        # 싱글톤 인스턴스 초기화 (테스트 격리)
        LanceBridge._instance = None
        
        # LanceBridge 초기화 (테스트용 경로 사용)
        self.bridge = LanceBridge(db_path=self.test_dir)

    def tearDown(self):
        """테스트 후 정리: 임시 디렉토리 삭제"""
        if hasattr(self, 'test_dir') and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        
        # 싱글톤 초기화
        if LanceBridge is not None:
            LanceBridge._instance = None

    def test_connection_status(self):
        """LanceBridge 연결 상태 확인"""
        self.assertTrue(
            self.bridge.is_connected,
            "LanceBridge가 연결되어 있어야 합니다."
        )

    def test_add_memory_success(self):
        """메모리 추가 기능 검증"""
        test_text = "AIN Step 4 테스트 기억입니다."
        test_vector = [0.1] * self.bridge.VECTOR_DIM
        
        result = self.bridge.add_memory(
            text=test_text,
            vector=test_vector,
            memory_type="test",
            source="unit_test"
        )
        
        self.assertTrue(result, "메모리 추가가 성공해야 합니다.")

    def test_vector_dimension_consistency(self):
        """벡터 차원 일관성 검증 - 짧은 벡터 패딩"""
        short_vector = [0.5] * 100  # 768보다 짧은 벡터
        
        result = self.bridge.add_memory(
            text="짧은 벡터 테스트",
            vector=short_vector,
            memory_type="test",
            source="unit_test"
        )
        
        self.assertTrue(result, "짧은 벡터도 패딩되어 저장되어야 합니다.")

    def test_vector_dimension_truncation(self):
        """벡터 차원 일관성 검증 - 긴 벡터 트렁케이션"""
        long_vector = [0.3] * 1000  # 768보다 긴 벡터
        
        result = self.bridge.add_memory(
            text="긴 벡터 테스트",
            vector=long_vector,
            memory_type="test",
            source="unit_test"
        )
        
        self.assertTrue(result, "긴 벡터도 트렁케이션되어 저장되어야 합니다.")

    def test_search_memory(self):
        """벡터 검색 기능 검증"""
        # 먼저 테스트 데이터 추가
        test_vector = [0.2] * self.bridge.VECTOR_DIM
        self.bridge.add_memory(
            text="검색 테스트용 기억",
            vector=test_vector,
            memory_type="semantic",
            source="unit_test"
        )
        
        # 유사 벡터로 검색
        query_vector = [0.2] * self.bridge.VECTOR_DIM
        results = self.bridge.search_memory(
            query_vector=query_vector,
            limit=5
        )
        
        self.assertIsInstance(results, list, "검색 결과는 리스트여야 합니다.")

    def test_get_recent_memories(self):
        """최근 기억 조회 기능 검증"""
        # 테스트 데이터 추가
        for i in range(3):
            self.bridge.add_memory(
                text=f"최근 기억 테스트 {i}",
                vector=[0.1 * i] * self.bridge.VECTOR_DIM,
                memory_type="episodic",
                source="unit_test"
            )
        
        recent = self.bridge.get_recent_memories(limit=5)
        
        self.assertIsInstance(recent, list, "최근 기억은 리스트여야 합니다.")
        self.assertGreaterEqual(len(recent), 1, "최소 1개 이상의 기억이 있어야 합니다.")

    def test_count_memories(self):
        """기억 개수 조회 기능 검증"""
        initial_count = self.bridge.count_memories()
        
        # 새 기억 추가
        self.bridge.add_memory(
            text="카운트 테스트",
            vector=[0.4] * self.bridge.VECTOR_DIM,
            memory_type="test",
            source="unit_test"
        )
        
        new_count = self.bridge.count_memories()
        
        self.assertEqual(
            new_count,
            initial_count + 1,
            "기억 추가 후 카운트가 1 증가해야 합니다."
        )


class TestVectorMemory(unittest.TestCase):
    """
    VectorMemory 래퍼 클래스 단위 테스트
    
    Nexus에서 사용하는 VectorMemory 클래스의 동작을 검증한다.
    """

    def setUp(self):
        """테스트 전 설정"""
        if not LANCE_AVAILABLE or VectorMemory is None:
            self.skipTest("LanceDB 또는 VectorMemory가 사용 불가합니다.")
        
        # 테스트용 임시 디렉토리
        self.test_dir = tempfile.mkdtemp()
        
        # 싱글톤 초기화
        LanceBridge._instance = None
        
        # LanceBridge를 먼저 초기화 (VectorMemory가 내부적으로 사용)
        self.bridge = LanceBridge(db_path=self.test_dir)
        
        # VectorMemory 인스턴스 생성
        self.memory = VectorMemory()

    def tearDown(self):
        """테스트 후 정리"""
        if hasattr(self, 'test_dir') and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        
        if LanceBridge is not None:
            LanceBridge._instance = None

    def test_text_to_embedding(self):
        """텍스트 임베딩 변환 기능 검증"""
        text = "테스트 문장입니다."
        embedding = self.memory.text_to_embedding(text)
        
        self.assertIsInstance(embedding, list, "임베딩은 리스트여야 합니다.")
        self.assertEqual(
            len(embedding),
            self.memory.EMBEDDING_DIM,
            f"임베딩 차원은 {self.memory.EMBEDDING_DIM}이어야 합니다."
        )

    def test_store_semantic_memory(self):
        """의미론적 기억 저장 기능 검증"""
        result = self.memory.store_semantic_memory(
            text="VectorMemory 저장 테스트",
            memory_type="semantic",
            source="unit_test"
        )
        
        self.assertTrue(result, "의미론적 기억 저장이 성공해야 합니다.")

    def test_search_similar_memories(self):
        """유사 기억 검색 기능 검증"""
        # 테스트 데이터 저장
        self.memory.store_semantic_memory(
            text="Python 프로그래밍 학습",
            memory_type="semantic",
            source="unit_test"
        )
        
        # 유사 기억 검색
        results = self.memory.search_similar(
            query="프로그래밍 공부",
            limit=5
        )
        
        self.assertIsInstance(results, list, "검색 결과는 리스트여야 합니다.")


class TestLanceBridgeEdgeCases(unittest.TestCase):
    """
    LanceBridge 엣지 케이스 테스트
    
    비정상적인 입력이나 경계 조건에서의 동작을 검증한다.
    """

    def setUp(self):
        """테스트 전 설정"""
        if not LANCE_AVAILABLE:
            self.skipTest("LanceDB가 설치되지 않아 테스트를 건너뜁니다.")
        
        self.test_dir = tempfile.mkdtemp()
        LanceBridge._instance = None
        self.bridge = LanceBridge(db_path=self.test_dir)

    def tearDown(self):
        """테스트 후 정리"""
        if hasattr(self, 'test_dir') and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)
        
        if LanceBridge is not None:
            LanceBridge._instance = None

    def test_empty_text_memory(self):
        """빈 텍스트 저장 시도"""
        result = self.bridge.add_memory(
            text="",
            vector=[0.0] * self.bridge.VECTOR_DIM,
            memory_type="test",
            source="unit_test"
        )
        
        # 빈 텍스트도 저장은 가능해야 함 (시스템 안정성)
        self.assertTrue(result, "빈 텍스트도 저장 가능해야 합니다.")

    def test_special_characters_in_text(self):
        """특수 문자 포함 텍스트 저장"""
        special_text = "테스트 <script>alert('xss')</script> & \"quotes\" 'apostrophe'"
        
        result = self.bridge.add_memory(
            text=special_text,
            vector=[0.5] * self.bridge.VECTOR_DIM,
            memory_type="test",
            source="unit_test"
        )
        
        self.assertTrue(result, "특수 문자 포함 텍스트도 저장 가능해야 합니다.")

    def test_unicode_text(self):
        """유니코드 텍스트 저장"""
        unicode_text = "한글 테스트 🎉 日本語 中文 العربية"
        
        result = self.bridge.add_memory(
            text=unicode_text,
            vector=[0.6] * self.bridge.VECTOR_DIM,
            memory_type="test",
            source="unit_test"
        )
        
        self.assertTrue(result, "유니코드 텍스트도 저장 가능해야 합니다.")

    def test_metadata_json_serialization(self):
        """메타데이터 JSON 직렬화 검증"""
        metadata = {
            "key1": "value1",
            "nested": {"inner": "data"},
            "list": [1, 2, 3],
            "unicode": "한글"
        }
        
        result = self.bridge.add_memory(
            text="메타데이터 테스트",
            vector=[0.7] * self.bridge.VECTOR_DIM,
            memory_type="test",
            source="unit_test",
            metadata=metadata
        )
        
        self.assertTrue(result, "복잡한 메타데이터도 저장 가능해야 합니다.")


if __name__ == "__main__":
    unittest.main(verbosity=2)