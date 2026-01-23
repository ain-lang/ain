"""
Nexus Core: 기본 클래스 - 모듈 등록, 이벤트 시스템, 메트릭스
"""
from typing import Dict, Any, Callable, List

from .storage import load_json, save_json


class NexusCore:
    """Nexus 기본 기능: 모듈 등록, 이벤트, 메트릭스"""
    
    def __init__(self):
        self.modules: Dict[str, Any] = {}
        self.metrics = {
            "growth_score": 0,
            "level": 1,
            "total_evolutions": 0
        }
        self.callbacks: Dict[str, List[Callable]] = {}
        
        self._load_metrics()
    
    def _load_metrics(self):
        """성장 지표 로드"""
        data = load_json("nexus_metrics.json")
        if data:
            self.metrics.update(data)
    
    def _save_metrics(self):
        """성장 지표 저장"""
        save_json("nexus_metrics.json", self.metrics)
    
    def register_module(self, name: str, instance: Any):
        """시스템 모듈 등록"""
        self.modules[name] = instance
        print(f"🔗 Nexus: 모듈 '{name}' 등록됨.")
    
    def subscribe(self, event_type: str, callback: Callable):
        """특정 이벤트에 대한 콜백 등록"""
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        self.callbacks[event_type].append(callback)
    
    def emit(self, event_type: str, data: Any):
        """이벤트 발생 및 콜백 실행"""
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    print(f"⚠️ Nexus Callback Error: {e}")
    
    def increment_growth(self, points: int = 10):
        """성장 점수 증가"""
        self.metrics["growth_score"] += points
        self.metrics["total_evolutions"] += 1
        
        new_level = (self.metrics["growth_score"] // 100) + 1
        if new_level > self.metrics["level"]:
            self.metrics["level"] = new_level
            self.emit("level_up", {"new_level": new_level})
        
        self._save_metrics()
    
    def get_status_report(self) -> str:
        """시스템 상태 종합 보고 (기본)"""
        report = f"📊 **AIN Status Report**\n"
        report += f"- Level: {self.metrics['level']} (Score: {self.metrics['growth_score']})\n"
        report += f"- Active Modules: {', '.join(self.modules.keys())}\n"
        report += f"- Total Evolutions: {self.metrics['total_evolutions']}\n"
        return report
