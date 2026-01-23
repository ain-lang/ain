"""
Engine Resource Monitor: 시스템 자원(토큰/비용) 추적 및 인식
Step 11: Limitation Awareness (Support for Step 8: Intuition)

이 모듈은 시스템의 '대사량(Metabolism)'을 추적한다.
LLM 사용량(Token)과 예상 비용(Cost)을 누적 집계하고,
현재 자원 상태(ResourceStatus)를 판단하여 DecisionGate에 신호를 제공한다.

Architecture:
    Muse/EvolutionMixin (LLM 호출)
        ↓ Usage Stats
    ResourceMonitor (이 모듈)
        ↓ ResourceStatus (ABUNDANT, SCARCE, etc.)
    DecisionGate (경로 선택)

Usage:
    from engine.resource_monitor import ResourceAwarenessMixin, ResourceStatus
    
    # Mixin in AINCore
    self.resource_monitor.track_usage(model="gpt-4", input_tokens=100, output_tokens=50)
    status = self.resource_monitor.get_resource_status()
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import json
import os


# 비용 상한선 (Safety Guard) - $5.00 per day
DAILY_BUDGET_LIMIT = 5.00

# 예산 비율 임계값
BUDGET_THRESHOLDS = {
    "abundant": 0.25,    # 25% 미만 사용 → 풍족
    "sufficient": 0.50,  # 50% 미만 사용 → 적절
    "scarce": 0.75,      # 75% 미만 사용 → 부족
    "critical": 1.00,    # 75% 이상 사용 → 위험
}


class ResourceStatus(Enum):
    """자원 상태 등급"""
    ABUNDANT = "abundant"      # 풍족 (System 2 적극 사용)
    SUFFICIENT = "sufficient"  # 적절 (기본 정책)
    SCARCE = "scarce"          # 부족 (System 1 권장, 압축 사용)
    CRITICAL = "critical"      # 위험 (System 1 강제, 생존 모드)


@dataclass
class UsageRecord:
    """단일 사용 기록"""
    timestamp: datetime
    model: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float


@dataclass
class UsageStats:
    """사용량 통계 데이터"""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    estimated_cost: float = 0.0
    call_count: int = 0
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "estimated_cost": round(self.estimated_cost, 6),
            "call_count": self.call_count,
            "last_updated": self.last_updated.isoformat(),
        }


class ResourceMonitor:
    """
    자원 모니터링 클래스
    
    시스템의 토큰 사용량과 예상 비용을 추적하고,
    현재 자원 상태를 판단하여 DecisionGate에 신호를 제공한다.
    """
    
    # 모델별 비용 테이블 (입력/출력 1M 토큰당 $)
    # 참고용 근사치 - 실제 가격은 변동될 수 있음
    COST_TABLE: Dict[str, Tuple[float, float]] = {
        # (input_cost_per_1m, output_cost_per_1m)
        "claude-3-opus": (15.0, 75.0),
        "claude-3-5-sonnet": (3.0, 15.0),
        "claude-3-sonnet": (3.0, 15.0),
        "claude-3-haiku": (0.25, 1.25),
        "gpt-4o": (5.0, 15.0),
        "gpt-4-turbo": (10.0, 30.0),
        "gpt-3.5-turbo": (0.5, 1.5),
        "gemini-1.5-pro": (3.5, 10.5),
        "gemini-1.5-flash": (0.075, 0.3),
        "gemini-2.0-flash": (0.1, 0.4),
        "gemini-3.0-flash": (0.1, 0.4),
        # OpenRouter 모델명 매핑
        "google/gemini-3.0-flash": (0.1, 0.4),
        "google/gemini-2.0-flash-001": (0.1, 0.4),
        "anthropic/claude-3.5-sonnet": (3.0, 15.0),
        "anthropic/claude-3-opus": (15.0, 75.0),
    }
    
    # 기본 비용 (알 수 없는 모델용)
    DEFAULT_COST = (1.0, 3.0)
    
    def __init__(self, daily_budget: float = DAILY_BUDGET_LIMIT):
        """
        ResourceMonitor 초기화
        
        Args:
            daily_budget: 일일 예산 한도 (USD)
        """
        self._daily_budget = daily_budget
        self._daily_stats = UsageStats()
        self._session_stats = UsageStats()
        self._usage_history: List[UsageRecord] = []
        self._day_start = self._get_day_start()
        self._initialized = True
        
        # 이전 세션 데이터 로드 시도
        self._load_persisted_stats()
    
    def _get_day_start(self) -> datetime:
        """오늘 시작 시각 반환 (UTC 기준 00:00)"""
        now = datetime.now()
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    def _check_day_rollover(self) -> None:
        """날짜가 바뀌었으면 일일 통계 초기화"""
        current_day_start = self._get_day_start()
        if current_day_start > self._day_start:
            print(f"📅 새로운 날 시작: 일일 자원 통계 초기화")
            self._persist_daily_stats()  # 이전 날 데이터 저장
            self._daily_stats = UsageStats()
            self._day_start = current_day_start
    
    def _get_model_cost(self, model: str) -> Tuple[float, float]:
        """
        모델의 토큰당 비용 조회
        
        Args:
            model: 모델명
            
        Returns:
            (input_cost_per_1m, output_cost_per_1m) 튜플
        """
        # 정확한 매칭 시도
        if model in self.COST_TABLE:
            return self.COST_TABLE[model]
        
        # 부분 매칭 시도 (모델명에 키워드 포함 여부)
        model_lower = model.lower()
        for key, cost in self.COST_TABLE.items():
            if key.lower() in model_lower or model_lower in key.lower():
                return cost
        
        # 기본값 반환
        return self.DEFAULT_COST
    
    def _calculate_cost(
        self, 
        model: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> float:
        """
        예상 비용 계산
        
        Args:
            model: 사용된 모델명
            input_tokens: 입력 토큰 수
            output_tokens: 출력 토큰 수
            
        Returns:
            예상 비용 (USD)
        """
        input_cost_per_1m, output_cost_per_1m = self._get_model_cost(model)
        
        input_cost = (input_tokens / 1_000_000) * input_cost_per_1m
        output_cost = (output_tokens / 1_000_000) * output_cost_per_1m
        
        return input_cost + output_cost
    
    def track_usage(
        self, 
        model: str, 
        input_tokens: int, 
        output_tokens: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        LLM 사용량 기록
        
        Args:
            model: 사용된 모델명
            input_tokens: 입력 토큰 수
            output_tokens: 출력 토큰 수
            metadata: 추가 메타데이터 (선택)
            
        Returns:
            기록 결과 및 현재 상태
        """
        self._check_day_rollover()
        
        # 비용 계산
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        
        # 기록 생성
        record = UsageRecord(
            timestamp=datetime.now(),
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost=cost,
        )
        
        # 통계 업데이트
        self._update_stats(self._daily_stats, record)
        self._update_stats(self._session_stats, record)
        
        # 히스토리 추가 (최근 100개만 유지)
        self._usage_history.append(record)
        if len(self._usage_history) > 100:
            self._usage_history = self._usage_history[-100:]
        
        # 현재 상태 반환
        status = self.get_resource_status()
        
        return {
            "recorded": True,
            "cost": round(cost, 6),
            "daily_total": round(self._daily_stats.estimated_cost, 4),
            "budget_used_pct": round(self.get_budget_usage_percentage(), 1),
            "status": status.value,
        }
    
    def _update_stats(self, stats: UsageStats, record: UsageRecord) -> None:
        """통계 객체 업데이트"""
        stats.total_input_tokens += record.input_tokens
        stats.total_output_tokens += record.output_tokens
        stats.estimated_cost += record.estimated_cost
        stats.call_count += 1
        stats.last_updated = record.timestamp
    
    def get_resource_status(self) -> ResourceStatus:
        """
        현재 자원 상태 판단
        
        Returns:
            ResourceStatus 열거형 값
        """
        usage_ratio = self.get_budget_usage_percentage() / 100.0
        
        if usage_ratio < BUDGET_THRESHOLDS["abundant"]:
            return ResourceStatus.ABUNDANT
        elif usage_ratio < BUDGET_THRESHOLDS["sufficient"]:
            return ResourceStatus.SUFFICIENT
        elif usage_ratio < BUDGET_THRESHOLDS["scarce"]:
            return ResourceStatus.SCARCE
        else:
            return ResourceStatus.CRITICAL
    
    def get_budget_usage_percentage(self) -> float:
        """
        일일 예산 사용률 반환 (%)
        
        Returns:
            0.0 ~ 100.0+ 범위의 백분율
        """
        if self._daily_budget <= 0:
            return 100.0
        return (self._daily_stats.estimated_cost / self._daily_budget) * 100.0
    
    def get_remaining_budget(self) -> float:
        """
        남은 일일 예산 반환 (USD)
        
        Returns:
            남은 예산 (음수일 수 있음)
        """
        return self._daily_budget - self._daily_stats.estimated_cost
    
    def get_daily_stats(self) -> Dict[str, Any]:
        """일일 통계 반환"""
        self._check_day_rollover()
        return {
            **self._daily_stats.to_dict(),
            "budget_limit": self._daily_budget,
            "budget_remaining": round(self.get_remaining_budget(), 4),
            "budget_used_pct": round(self.get_budget_usage_percentage(), 2),
            "status": self.get_resource_status().value,
        }
    
    def get_session_stats(self) -> Dict[str, Any]:
        """세션 통계 반환"""
        return self._session_stats.to_dict()
    
    def should_use_system_1(self) -> bool:
        """
        System 1 (직관/반사) 사용을 권장하는지 판단
        
        자원이 부족하거나 위험 상태일 때 True 반환
        
        Returns:
            System 1 권장 여부
        """
        status = self.get_resource_status()
        return status in (ResourceStatus.SCARCE, ResourceStatus.CRITICAL)
    
    def get_model_recommendation(self) -> str:
        """
        현재 자원 상태에 따른 모델 추천
        
        Returns:
            추천 모델 티어 문자열
        """
        status = self.get_resource_status()
        
        recommendations = {
            ResourceStatus.ABUNDANT: "premium",    # Claude Opus, GPT-4
            ResourceStatus.SUFFICIENT: "standard", # Claude Sonnet, GPT-4o
            ResourceStatus.SCARCE: "economy",      # Gemini Flash, GPT-3.5
            ResourceStatus.CRITICAL: "minimal",    # Gemini Flash only
        }
        
        return recommendations.get(status, "standard")
    
    def _persist_daily_stats(self) -> None:
        """일일 통계를 파일에 저장 (영속화)"""
        try:
            stats_file = "resource_stats.json"
            data = {
                "date": self._day_start.isoformat(),
                "daily_stats": self._daily_stats.to_dict(),
            }
            
            # 기존 히스토리 로드
            history = []
            if os.path.exists(stats_file):
                with open(stats_file, "r", encoding="utf-8") as f:
                    existing = json.load(f)
                    history = existing.get("history", [])
            
            # 새 데이터 추가 (최근 30일만 유지)
            history.append(data)
            history = history[-30:]
            
            with open(stats_file, "w", encoding="utf-8") as f:
                json.dump({"history": history}, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ 자원 통계 저장 실패: {e}")
    
    def _load_persisted_stats(self) -> None:
        """저장된 통계 로드 (오늘 데이터가 있으면 복원)"""
        try:
            stats_file = "resource_stats.json"
            if not os.path.exists(stats_file):
                return
            
            with open(stats_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            history = data.get("history", [])
            if not history:
                return
            
            # 오늘 데이터 찾기
            today_str = self._day_start.isoformat()
            for entry in reversed(history):
                if entry.get("date") == today_str:
                    stats = entry.get("daily_stats", {})
                    self._daily_stats.total_input_tokens = stats.get("total_input_tokens", 0)
                    self._daily_stats.total_output_tokens = stats.get("total_output_tokens", 0)
                    self._daily_stats.estimated_cost = stats.get("estimated_cost", 0.0)
                    self._daily_stats.call_count = stats.get("call_count", 0)
                    print(f"📊 이전 자원 통계 복원: ${self._daily_stats.estimated_cost:.4f} 사용됨")
                    break
                    
        except Exception as e:
            print(f"⚠️ 자원 통계 로드 실패: {e}")


class ResourceAwarenessMixin:
    """
    자원 인식 믹스인
    
    AINCore에 포함되어 시스템의 자원 소비를 추적하고 관리한다.
    """
    
    _resource_monitor: Optional[ResourceMonitor] = None
    
    def init_resource_monitor(self, daily_budget: float = DAILY_BUDGET_LIMIT) -> None:
        """
        리소스 모니터 초기화
        
        Args:
            daily_budget: 일일 예산 한도 (USD)
        """
        self._resource_monitor = ResourceMonitor(daily_budget=daily_budget)
        print(f"💰 Resource Monitor(대사량 추적) 활성화 - 일일 예산: ${daily_budget:.2f}")
    
    @property
    def resource_monitor(self) -> ResourceMonitor:
        """ResourceMonitor 인스턴스 반환 (Lazy 초기화)"""
        if self._resource_monitor is None:
            self.init_resource_monitor()
        return self._resource_monitor
    
    def track_llm_usage(
        self, 
        model: str, 
        input_tokens: int, 
        output_tokens: int
    ) -> Dict[str, Any]:
        """
        LLM 사용량 추적 (편의 메서드)
        
        Args:
            model: 사용된 모델명
            input_tokens: 입력 토큰 수
            output_tokens: 출력 토큰 수
            
        Returns:
            추적 결과
        """
        return self.resource_monitor.track_usage(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )
    
    def get_resource_status(self) -> ResourceStatus:
        """현재 자원 상태 반환"""
        return self.resource_monitor.get_resource_status()
    
    def get_resource_report(self) -> str:
        """
        자원 상태 리포트 생성
        
        Returns:
            사람이 읽기 쉬운 형식의 리포트 문자열
        """
        daily = self.resource_monitor.get_daily_stats()
        status = self.resource_monitor.get_resource_status()
        
        status_emoji = {
            ResourceStatus.ABUNDANT: "🟢",
            ResourceStatus.SUFFICIENT: "🟡",
            ResourceStatus.SCARCE: "🟠",
            ResourceStatus.CRITICAL: "🔴",
        }
        
        report_lines = [
            "💰 **Resource Status Report**",
            f"- Status: {status_emoji.get(status, '⚪')} {status.value.upper()}",
            f"- Daily Cost: ${daily['estimated_cost']:.4f} / ${daily['budget_limit']:.2f}",
            f"- Budget Used: {daily['budget_used_pct']:.1f}%",
            f"- API Calls: {daily['call_count']}",
            f"- Tokens: {daily['total_input_tokens']:,} in / {daily['total_output_tokens']:,} out",
            f"- Recommendation: {self.resource_monitor.get_model_recommendation()}",
        ]
        
        return "\n".join(report_lines)


# 싱글톤 인스턴스 (전역 접근용)
_global_monitor: Optional[ResourceMonitor] = None


def get_resource_monitor() -> ResourceMonitor:
    """전역 ResourceMonitor 인스턴스 반환"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = ResourceMonitor()
    return _global_monitor