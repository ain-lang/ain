"""
Nexus History: Evolution/Conversation 기록 관리
"""
from datetime import datetime
from typing import List, Dict, Any, Optional

from .storage import load_json, save_json
from .memory import VectorMemory


class HistoryManager:
    """진화 기록 및 대화 기록 관리"""
    
    def __init__(
        self, 
        memory_file: str = "evolution_history.json",
        dialogue_file: str = "dialogue_memory.json",
        vector_memory: Optional[VectorMemory] = None
    ):
        self.memory_file = memory_file
        self.dialogue_file = dialogue_file
        self.vector_memory = vector_memory
        
        self._evolution_cache: List[Dict[str, Any]] = []
        self._dialogue_cache: List[Dict[str, Any]] = []
        
        self._load_caches()
    
    def _load_caches(self):
        """캐시 로드"""
        data = load_json(self.memory_file)
        if data and isinstance(data, list):
            self._evolution_cache = data
        
        data = load_json(self.dialogue_file)
        if data and isinstance(data, list):
            self._dialogue_cache = data
    
    def record_evolution(
        self, 
        evolution_type: str, 
        action: str, 
        file: str, 
        description: str,
        status: str = "success", 
        error: str = None,
        emit_callback = None
    ) -> Dict[str, Any]:
        """진화 기록 저장 (Dual-Write: JSON + Vector DB)"""
        timestamp = datetime.now().isoformat()
        
        record = {
            "timestamp": timestamp,
            "type": evolution_type,
            "action": action,
            "file": file,
            "description": description,
            "status": status,
            "error": error
        }
        
        self._evolution_cache.append(record)
        
        # 최대 100개만 유지
        if len(self._evolution_cache) > 100:
            self._evolution_cache = self._evolution_cache[-100:]
        
        save_json(self.memory_file, self._evolution_cache)
        
        # Vector DB에도 저장 (Dual-Write)
        if self.vector_memory and self.vector_memory.is_connected:
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
            
            self.vector_memory.store(
                text=vector_text,
                memory_type="evolution",
                source="record_evolution",
                metadata=metadata
            )
        
        # 이벤트 발행
        if emit_callback:
            emit_callback("evolution", record)
        
        return record
    
    def record_conversation(
        self, 
        role: str, 
        content: str, 
        session_id: str = "default"
    ) -> Dict[str, Any]:
        """대화 기록 저장 (Dual-Write: JSON + Vector DB)"""
        timestamp = datetime.now().isoformat()
        
        record = {
            "timestamp": timestamp,
            "session_id": session_id,
            "role": role,
            "content": content
        }
        
        self._dialogue_cache.append(record)
        
        if len(self._dialogue_cache) > 50:
            self._dialogue_cache = self._dialogue_cache[-50:]
        
        save_json(self.dialogue_file, self._dialogue_cache)
        
        # Vector DB 저장
        if self.vector_memory and self.vector_memory.is_connected and len(content) > 10:
            vector_text = f"[{role}] {content}"
            metadata = {
                "timestamp": timestamp,
                "session_id": session_id,
                "role": role
            }
            
            self.vector_memory.store(
                text=vector_text,
                memory_type="conversation",
                source="record_conversation",
                metadata=metadata
            )
        
        return record
    
    def get_evolution_summary(self, limit: int = 5) -> str:
        """최근 진화 기록 요약"""
        history = self._evolution_cache[-limit:] if self._evolution_cache else []
        
        if not history:
            return "아직 진화 기록이 없습니다."
        
        summary = "### 📜 Recent Evolution History\n"
        for record in reversed(history):
            status_icon = "✅" if record.get("status") == "success" else "❌"
            summary += f"- {status_icon} [{record.get('type')}] {record.get('file')}: {record.get('description', '')[:50]}...\n"
        
        return summary
    
    def get_lessons_learned(self, limit: int = 10) -> str:
        """실패 사례에서 학습한 교훈"""
        failures = [
            r for r in self._evolution_cache 
            if r.get("status") == "failed" or r.get("error")
        ][-limit:]
        
        if not failures:
            return "아직 기록된 실패 사례가 없습니다."
        
        lessons = "### 📚 Lessons Learned (from failures)\n"
        for record in failures:
            lessons += f"- ❌ {record.get('file')}: {record.get('error', record.get('description', ''))[:100]}\n"
        
        return lessons
    
    def fallback_keyword_search(
        self, 
        query_text: str, 
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Vector DB 사용 불가 시 키워드 기반 검색"""
        results = []
        query_lower = query_text.lower()
        keywords = query_lower.split()
        
        if memory_type is None or memory_type == "evolution":
            for record in reversed(self._evolution_cache):
                desc = record.get("description", "").lower()
                file_name = record.get("file", "").lower()
                score = sum(1 for kw in keywords if kw in desc or kw in file_name)
                
                if score > 0:
                    results.append({
                        "text": f"[{record.get('type')}] {record.get('action')} on {record.get('file')}: {record.get('description')}",
                        "memory_type": "evolution",
                        "timestamp": record.get("timestamp"),
                        "metadata": record,
                        "distance": 1.0 / (score + 1),
                        "source": "fallback_search"
                    })
        
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
        
        results.sort(key=lambda x: x["distance"])
        return results[:limit]
    
    @property
    def evolution_cache(self) -> List[Dict[str, Any]]:
        return self._evolution_cache
    
    @evolution_cache.setter
    def evolution_cache(self, value: List[Dict[str, Any]]):
        self._evolution_cache = value
