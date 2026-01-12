"""
AIN Nexus Engine: 시스템의 기억(Evolution History)과 대화(Episodic Memory)를 관리한다.

Step 4 Evolution - Semantic Memory Expansion:
- LanceBridge 통합으로 벡터 기반 의미론적 기억 저장/검색
- Dual-Write 메커니즘: JSON + Vector DB 동시 저장
- recall_memories(): 의미 기반 문맥 검색 인터페이스
"""

import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

import pyarrow as pa
import pyarrow.compute as pc

# Arrow Schema 임포트 (SSOT)
try:
    from database.arrow_schema import get_history_schema, history_record_to_dict
    HAS_SCHEMA = True
except ImportError:
    HAS_SCHEMA = False
    print("⚠️ Arrow Schema 임포트 실패. 기본 스키마 사용.")

# LanceBridge 임포트 (Step 4: Vector Memory)
try:
    from database.lance_bridge import get_lance_bridge, LanceBridge, LANCE_AVAILABLE
    HAS_LANCE = LANCE_AVAILABLE
except ImportError:
    HAS_LANCE = False
    print("⚠️ LanceBridge 임포트 실패. Vector Memory 비활성화.")


class Nexus:
    """
    AIN의 Nexus Engine: 시스템의 기억(Evolution History)과 대화(Episodic Memory)를 관리한다.
    
    Step 3 Evolution - Full-Cycle Persistence:
    - export_history_as_arrow(): 내부 기록을 Arrow Table로 직렬화
    - load_history_from_arrow(): Arrow Table에서 내부 메모리로 복원
    - JSON과 Arrow 양방향 호환성 보장
    
    Step 4 Evolution - Semantic Memory Expansion:
    - LanceBridge 통합: 진화 기록을 벡터화하여 저장
    - Dual-Write: JSON 저장과 동시에 Vector DB에도 저장
    - recall_memories(): 의미 기반 유사 기억 검색
    """
    
    # 간단한 텍스트 임베딩을 위한 기본 차원
    EMBEDDING_DIM = 384
    
    def __init__(self, memory_file="evolution_history.json", dialogue_file="dialogue_memory.json"):
        self.memory_file = memory_file
        self.dialogue_file = dialogue_file
        self.modules = {}  # Module Registry
        self.metrics = {
            "growth_score": 0,
            "level": 1,
            "total_evolutions": 0
        }
        self.callbacks = {}  # Event Callbacks (Pub/Sub)
        
        # Step 3: 내부 메모리 캐시 (Arrow 호환)
        self._evolution_history_cache: List[Dict[str, Any]] = []
        self._dialogue_cache: List[Dict[str, Any]] = []
        
        # Step 4: LanceBridge 초기화 (Graceful Degradation)
        self._lance_bridge: Optional[LanceBridge] = None
        self._lance_connected: bool = False
        self._init_lance_bridge()
        
        self._load_metrics()
        self._load_history_cache()

    def _init_lance_bridge(self):
        """LanceBridge 싱글톤 초기화 (실패 시 Graceful Degradation)"""
        if not HAS_LANCE:
            print("ℹ️ Nexus: LanceBridge 미사용 (라이브러리 미설치)")
            return
        
        try:
            self._lance_bridge = get_lance_bridge()
            self._lance_connected = self._lance_bridge.is_connected
            
            if self._lance_connected:
                print(f"✅ Nexus: LanceBridge 연결 성공 (기억 수: {self._lance_bridge.count_memories()})")
            else:
                print("⚠️ Nexus: LanceBridge 연결 실패. JSON-Only 모드로 작동.")
        except Exception as e:
            print(f"❌ Nexus: LanceBridge 초기화 오류 - {e}")
            self._lance_bridge = None
            self._lance_connected = False

    def _load_metrics(self):
        """성장 지표 로드"""
        data = self.load_data("nexus_metrics.json")
        if data:
            self.metrics.update(data)

    def _save_metrics(self):
        """성장 지표 저장"""
        self.save_data("nexus_metrics.json", self.metrics)

    def _load_history_cache(self):
        """진화 기록을 내부 캐시로 로드"""
        data = self.load_data(self.memory_file)
        if data and isinstance(data, list):
            self._evolution_history_cache = data
        else:
            self._evolution_history_cache = []

    def register_module(self, name, instance):
        """시스템 모듈 등록"""
        self.modules[name] = instance
        print(f"🔗 Nexus: 모듈 '{name}' 등록됨.")

    def get_status_report(self):
        """시스템 상태 종합 보고"""
        report = f"📊 **AIN Status Report**\n"
        report += f"- Level: {self.metrics['level']} (Score: {self.metrics['growth_score']})\n"
        report += f"- Active Modules: {', '.join(self.modules.keys())}\n"
        report += f"- Total Evolutions: {self.metrics['total_evolutions']}\n"
        report += f"- Cached History Records: {len(self._evolution_history_cache)}\n"
        
        # Step 4: Vector Memory 상태 추가
        if self._lance_connected and self._lance_bridge:
            report += f"- Vector Memories: {self._lance_bridge.count_memories()}\n"
            report += f"- Semantic Search: ✅ Enabled\n"
        else:
            report += f"- Vector Memories: N/A (Disabled)\n"
            report += f"- Semantic Search: ❌ Disabled\n"
        
        return report

    def subscribe(self, event_type, callback):
        """특정 이벤트에 대한 콜백 등록"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)

    def emit(self, event_type, data):
        """이벤트 발생 및 콜백 실행"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"⚠️ Nexus Callback Error: {e}")

    # =========================================================================
    # JSON File Operations (Legacy Support)
    # =========================================================================

    def load_data(self, filename):
        """범용 JSON 로드"""
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Nexus load_data error ({filename}): {e}")
        return None

    def save_data(self, filename, data):
        """범용 JSON 저장"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"⚠️ Nexus save_data error ({filename}): {e}")
            return False

    # =========================================================================
    # Step 4: Semantic Memory Operations (Dual-Write)
    # =========================================================================

    def _text_to_simple_embedding(self, text: str) -> List[float]:
        """
        간단한 텍스트 → 벡터 변환 (임베딩 모델 없이)
        
        실제 프로덕션에서는 sentence-transformers 등의 모델을 사용해야 하지만,
        현재는 텍스트의 특성을 기반으로 한 간단한 해시 기반 벡터를 생성한다.
        
        향후 진화 방향: 
        - OpenAI/Cohere Embedding API 연동
        - 로컬 sentence-transformers 모델 로딩
        """
        import hashlib
        
        # 텍스트를 정규화
        normalized = text.lower().strip()
        
        # 단어 기반 특성 추출
        words = normalized.split()
        word_count = len(words)
        char_count = len(normalized)
        
        # 해시 기반 벡터 생성
        vector = []
        
        # 텍스트 전체 해시를 기반으로 초기 벡터 생성
        full_hash = hashlib.sha256(normalized.encode()).hexdigest()
        for i in range(0, min(len(full_hash), self.EMBEDDING_DIM * 2), 2):
            # 16진수 2자리를 0-1 범위의 float로 변환
            val = int(full_hash[i:i+2], 16) / 255.0
            vector.append(val)
        
        # 단어별 해시 추가 (의미적 다양성 확보)
        for word in words[:50]:  # 최대 50단어
            word_hash = hashlib.md5(word.encode()).hexdigest()[:8]
            for i in range(0, 8, 2):
                if len(vector) >= self.EMBEDDING_DIM:
                    break
                val = int(word_hash[i:i+2], 16) / 255.0
                vector.append(val)
        
        # 차원 맞추기 (패딩 또는 트렁케이션)
        if len(vector) < self.EMBEDDING_DIM:
            # 패딩: 텍스트 길이 기반 값으로 채움
            padding_val = (word_count % 100) / 100.0
            vector.extend([padding_val] * (self.EMBEDDING_DIM - len(vector)))
        else:
            vector = vector[:self.EMBEDDING_DIM]
        
        return vector

    def _store_to_vector_db(
        self, 
        text: str, 
        memory_type: str = "evolution",
        source: str = "nexus",
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        텍스트를 벡터화하여 LanceDB에 저장 (Dual-Write의 Vector 부분)
        
        Args:
            text: 저장할 텍스트
            memory_type: 기억 유형 (evolution, conversation, error 등)
            source: 기억의 출처
            metadata: 추가 메타데이터
        
        Returns:
            성공 여부
        """
        if not self._lance_connected or not self._lance_bridge:
            return False
        
        try:
            # 텍스트를 벡터로 변환
            vector = self._text_to_simple_embedding(text)
            
            # LanceBridge를 통해 저장
            success = self._lance_bridge.add_memory(
                text=text,
                vector=vector,
                memory_type=memory_type,
                source=source,
                metadata=metadata
            )
            
            return success
            
        except Exception as e:
            print(f"⚠️ Vector DB 저장 실패: {e}")
            return False

    def record_evolution(self, evolution_type, action, file, description, 
                        status="success", error=None):
        """
        진화 기록 저장 (Dual-Write: JSON + Vector DB)
        
        Step 4 Enhancement:
        - 기존 JSON 저장 유지 (하위 호환성)
        - LanceBridge를 통한 벡터 저장 추가 (의미 검색 지원)
        """
        timestamp = datetime.now().isoformat()
        
        # 1. 기존 로직: JSON 리스트에 추가
        record = {
            "timestamp": timestamp,
            "type": evolution_type,
            "action": action,
            "file": file,
            "description": description,
            "status": status,
            "error": error
        }
        
        self._evolution_history_cache.append(record)
        
        # 최대 100개만 유지 (메모리 관리)
        if len(self._evolution_history_cache) > 100:
            self._evolution_history_cache = self._evolution_history_cache[-100:]
        
        # JSON 파일 저장
        self.save_data(self.memory_file, self._evolution_history_cache)
        
        # 2. Step 4: Vector DB에도 저장 (Dual-Write)
        if self._lance_connected:
            # 벡터 검색에 적합한 텍스트 구성
            vector_text = f"[{evolution_type}] {action} on {file}: {description}"
            if error:
                vector_text += f" (Error: {error})"
            
            metadata = {
                "timestamp": timestamp,
                "file": file,
                "action": action,
                "status": status,
                "evolution_type": evolution_type
            }
            
            self._store_to_vector_db(
                text=vector_text,
                memory_type="evolution",
                source="record_evolution",
                metadata=metadata
            )
        
        # 3. 성장 지표 업데이트
        if status == "success":
            self.metrics["growth_score"] += 10
            self.metrics["total_evolutions"] += 1
            
            # 레벨업 체크
            new_level = (self.metrics["growth_score"] // 100) + 1
            if new_level > self.metrics["level"]:
                self.metrics["level"] = new_level
                self.emit("level_up", {"new_level": new_level})
        
        self._save_metrics()
        
        # 4. 이벤트 발행
        self.emit("evolution", record)
        
        return record

    def record_conversation(self, role: str, content: str, session_id: str = "default"):
        """
        대화 기록 저장 (Dual-Write: JSON + Vector DB)
        
        Args:
            role: 발화자 (user, assistant, system)
            content: 대화 내용
            session_id: 세션 ID
        """
        timestamp = datetime.now().isoformat()
        
        # 1. JSON 저장
        record = {
            "timestamp": timestamp,
            "session_id": session_id,
            "role": role,
            "content": content
        }
        
        self._dialogue_cache.append(record)
        
        # 최대 50개 유지
        if len(self._dialogue_cache) > 50:
            self._dialogue_cache = self._dialogue_cache[-50:]
        
        self.save_data(self.dialogue_file, self._dialogue_cache)
        
        # 2. Vector DB 저장 (대화도 의미 검색 가능하게)
        if self._lance_connected and len(content) > 10:  # 너무 짧은 내용 제외
            vector_text = f"[{role}] {content}"
            metadata = {
                "timestamp": timestamp,
                "session_id": session_id,
                "role": role
            }
            
            self._store_to_vector_db(
                text=vector_text,
                memory_type="conversation",
                source="record_conversation",
                metadata=metadata
            )
        
        return record

    # =========================================================================
    # Step 4: Semantic Memory Retrieval (의미 기반 기억 회상)
    # =========================================================================

    def recall_memories(
        self, 
        query_text: str, 
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        의미 기반 기억 회상 (Semantic Retrieval)
        
        입력된 텍스트(현재 상황, 에러 메시지 등)와 의미적으로 가장 가까운
        과거의 기억(코드 수정 내역, 성공/실패 사례 등)을 반환한다.
        
        Args:
            query_text: 검색 쿼리 텍스트
            limit: 반환할 최대 결과 수
            memory_type: 특정 기억 유형으로 필터링 (evolution, conversation 등)
        
        Returns:
            유사한 기억 목록 (유사도 순 정렬)
        
        Example:
            >>> nexus.recall_memories("SurrealDB 연결 에러")
            [
                {"text": "[ERROR] DB connection failed...", "distance": 0.12, ...},
                {"text": "[EVOLUTION] Fixed DB timeout...", "distance": 0.23, ...}
            ]
        """
        if not self._lance_connected or not self._lance_bridge:
            print("ℹ️ Vector Memory 비활성화. JSON 기반 검색으로 대체.")
            return self._fallback_keyword_search(query_text, limit, memory_type)
        
        try:
            # 쿼리 텍스트를 벡터로 변환
            query_vector = self._text_to_simple_embedding(query_text)
            
            # LanceBridge를 통한 ANN 검색
            results = self._lance_bridge.search_memory(
                query_vector=query_vector,
                limit=limit,
                memory_type=memory_type
            )
            
            if results:
                print(f"🔍 의미 검색 완료: {len(results)}개 기억 발견")
            
            return results
            
        except Exception as e:
            print(f"⚠️ 의미 검색 실패: {e}")
            return self._fallback_keyword_search(query_text, limit, memory_type)

    def _fallback_keyword_search(
        self, 
        query_text: str, 
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Vector DB 사용 불가 시 키워드 기반 검색 (Fallback)
        """
        results = []
        query_lower = query_text.lower()
        keywords = query_lower.split()
        
        # 진화 기록에서 검색
        if memory_type is None or memory_type == "evolution":
            for record in reversed(self._evolution_history_cache):
                desc = record.get("description", "").lower()
                file_name = record.get("file", "").lower()
                
                # 키워드 매칭 점수 계산
                score = sum(1 for kw in keywords if kw in desc or kw in file_name)
                
                if score > 0:
                    results.append({
                        "text": f"[{record.get('type')}] {record.get('action')} on {record.get('file')}: {record.get('description')}",
                        "memory_type": "evolution",
                        "timestamp": record.get("timestamp"),
                        "metadata": record,
                        "distance": 1.0 / (score + 1),  # 점수가 높을수록 거리가 작음
                        "source": "fallback_search"
                    })
        
        # 대화 기록에서 검색
        if memory_type is None or memory_type == "conversation":
            for record in reversed(self._dialogue_cache):
                content = record.get("content", "").lower()
                
                score = sum(1 for kw in keywords if kw in content)
                
                if score > 0:
                    results.append({
                        "text": f"[{record.get('role')}] {record.get('content')}",
                        "memory_type": "conversation",
                        "timestamp": record.get("timestamp"),
                        "metadata": record,
                        "distance": 1.0 / (score + 1),
                        "source": "fallback_search"
                    })
        
        # 거리순 정렬 후 상위 N개 반환
        results.sort(key=lambda x: x["distance"])
        return results[:limit]

    def recall_similar_evolutions(self, current_error: str, limit: int = 3) -> List[Dict[str, Any]]:
        """
        현재 에러와 유사한 과거 진화 사례 검색 (Muse 연상 지원용)
        
        Args:
            current_error: 현재 발생한 에러 메시지
            limit: 반환할 최대 결과 수
        
        Returns:
            유사한 진화 사례 목록
        """
        return self.recall_memories(
            query_text=current_error,
            limit=limit,
            memory_type="evolution"
        )

    def get_recent_vector_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """최근 저장된 벡터 기억 조회"""
        if not self._lance_connected or not self._lance_bridge:
            return []
        
        return self._lance_bridge.get_recent_memories(limit=limit)

    # =========================================================================
    # Arrow Table Operations (Step 3 호환)
    # =========================================================================

    def export_history_as_arrow(self) -> Optional[pa.Table]:
        """
        진화 기록을 Arrow Table로 직렬화하여 반환.
        SurrealDB 저장 또는 외부 시스템 연동에 사용.
        """
        if not self._evolution_history_cache:
            return None
        
        try:
            # 스키마 정의
            if HAS_SCHEMA:
                schema = get_history_schema()
            else:
                schema = pa.schema([
                    ("timestamp", pa.string()),
                    ("type", pa.string()),
                    ("action", pa.string()),
                    ("file", pa.string()),
                    ("description", pa.string()),
                    ("status", pa.string()),
                    ("error", pa.string()),
                ])
            
            # 데이터 정규화
            if HAS_SCHEMA:
                records = [history_record_to_dict(r) for r in self._evolution_history_cache]
            else:
                records = self._evolution_history_cache
            
            # Arrow Table 생성
            table = pa.Table.from_pylist(records, schema=schema)
            self._last_arrow_table = table
            
            return table
            
        except Exception as e:
            print(f"❌ Arrow 직렬화 실패: {e}")
            return None

    def load_history_from_arrow(self, table: pa.Table) -> bool:
        """
        Arrow Table에서 진화 기록을 복원하여 내부 캐시에 로드.
        SurrealDB에서 복원 시 사용.
        """
        if table is None or table.num_rows == 0:
            return False
        
        try:
            # Arrow Table → Python List[Dict]
            records = table.to_pylist()
            
            # 내부 캐시 갱신
            self._evolution_history_cache = records
            
            # JSON 파일에도 동기화
            self.save_data(self.memory_file, records)
            
            print(f"✅ Nexus: {len(records)}개 진화 기록 복원됨")
            return True
            
        except Exception as e:
            print(f"❌ Arrow 역직렬화 실패: {e}")
            return False

    # =========================================================================
    # Legacy Methods (하위 호환성)
    # =========================================================================

    def get_evolution_summary(self, limit=5):
        """최근 진화 기록 요약 반환"""
        history = self._evolution_history_cache[-limit:] if self._evolution_history_cache else []
        
        if not history:
            return "아직 진화 기록이 없습니다."
        
        summary = "### 📜 Recent Evolution History\n"
        for record in reversed(history):
            status_icon = "✅" if record.get("status") == "success" else "❌"
            summary += f"- {status_icon} [{record.get('type')}] {record.get('file')}: {record.get('description', '')[:50]}...\n"
        
        return summary

    def get_lessons_learned(self, limit=10):
        """실패 사례에서 학습한 교훈 반환"""
        failures = [
            r for r in self._evolution_history_cache 
            if r.get("status") == "failed" or r.get("error")
        ][-limit:]
        
        if not failures:
            return "아직 기록된 실패 사례가 없습니다."
        
        lessons = "### 📚 Lessons Learned (from failures)\n"
        for record in failures:
            lessons += f"- ❌ {record.get('file')}: {record.get('error', record.get('description', ''))[:100]}\n"
        
        return lessons