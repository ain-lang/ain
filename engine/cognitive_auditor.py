"""
Engine Cognitive Auditor: 인지 감사 및 논리적 오류 탐지
Step 7: Meta-Cognition - Real-time Inference Path Auditing

이 모듈은 시스템의 최근 행동 패턴(History)을 분석하여
무한 루프, 논리적 정체, 로드맵 이탈 등의 '인지적 오류'를 감지한다.
Meta-Cognition의 'Self-Correction' 기능을 보조하는 핵심 컴포넌트이다.

Intention Goal: "실시간 추론 경로 감사 및 논리적 오류 자가 진단 메커니즘 구축"

Architecture:
    MetaCognitionMixin (engine/meta_cognition.py)
        ↓ 호출
    CognitiveAuditorMixin (이 모듈)
        ↓ 분석
    Loop Detection, Stagnation Detection, Roadmap Alignment 반환

Usage:
    from engine.cognitive_auditor import CognitiveAuditorMixin
    
    class AINCore(CognitiveAuditorMixin, ...):
        pass
    
    ain = AINCore()
    warning = ain.audit_reasoning_loop(history)
    alignment = ain.audit_roadmap_alignment(focus, actions)
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import Counter
from dataclasses import dataclass
from enum import Enum


class AuditSeverity(Enum):
    """감사 경고 심각도 열거형"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class AuditResult:
    """
    감사 결과 데이터 클래스
    
    Attributes:
        has_issue: 문제 감지 여부
        severity: 심각도 수준
        message: 경고 메시지
        recommendation: 권장 조치
        details: 상세 정보 딕셔너리
    """
    has_issue: bool
    severity: AuditSeverity
    message: str
    recommendation: str
    details: Dict[str, Any]


class CognitiveAuditorMixin:
    """
    인지 감사 믹스인
    
    AINCore에 상속되어(또는 MetaController에서 사용되어)
    시스템의 행동 로그를 기반으로 건전성(Sanity)을 감사한다.
    
    주요 기능:
    1. 순환 추론(Circular Reasoning) 감지 - 동일 파일 반복 수정
    2. 로드맵 정렬(Roadmap Alignment) 평가 - 현재 목표와 행동 일치도
    3. 정체(Stagnation) 감지 - 성장 지표의 변화 없음
    4. 에러 반복(Persistent Error) 감지 - 동일 에러 연속 발생
    """

    # 감사 임계값 설정
    LOOP_DETECTION_THRESHOLD = 3  # 동일 파일 수정 횟수 임계값
    LOOP_WINDOW_SIZE = 5  # 분석할 최근 기록 윈도우 크기
    ALIGNMENT_THRESHOLD = 0.4  # 로드맵 정렬 최소 임계값
    STAGNATION_WINDOW = 5  # 정체 감지 윈도우 크기

    def audit_reasoning_loop(
        self, 
        history: List[Dict[str, Any]], 
        window: int = None
    ) -> Optional[AuditResult]:
        """
        최근 행동에서 반복 루프(Circular Reasoning)를 감지한다.
        
        Args:
            history: 최근 진화 기록 리스트
            window: 분석할 최근 기록 윈도우 크기 (기본: LOOP_WINDOW_SIZE)
            
        Returns:
            AuditResult 객체 (문제 없으면 None)
        """
        if window is None:
            window = self.LOOP_WINDOW_SIZE
            
        if not history or len(history) < 2:
            return None

        recent = history[-window:]
        
        # 1. 파일 수정 반복 감지
        file_loop_result = self._detect_file_loop(recent, window)
        if file_loop_result is not None:
            return file_loop_result

        # 2. 에러 반복 감지
        error_loop_result = self._detect_error_loop(recent)
        if error_loop_result is not None:
            return error_loop_result

        # 3. 액션 패턴 반복 감지
        action_loop_result = self._detect_action_pattern_loop(recent)
        if action_loop_result is not None:
            return action_loop_result

        return None

    def _detect_file_loop(
        self, 
        recent: List[Dict[str, Any]], 
        window: int
    ) -> Optional[AuditResult]:
        """파일 수정 반복 패턴 감지"""
        files = [h.get("file") for h in recent if h.get("file")]
        if not files:
            return None
            
        file_counts = Counter(files)
        most_common_file, count = file_counts.most_common(1)[0]
        
        # 동일 파일이 윈도우 내 임계값 이상 수정되었고, 최근에도 수정되었다면
        if count >= self.LOOP_DETECTION_THRESHOLD and files[-1] == most_common_file:
            # 연속 수정인지 확인 (더 심각한 경우)
            consecutive_count = 0
            for f in reversed(files):
                if f == most_common_file:
                    consecutive_count += 1
                else:
                    break
            
            severity = AuditSeverity.CRITICAL if consecutive_count >= 3 else AuditSeverity.WARNING
            
            return AuditResult(
                has_issue=True,
                severity=severity,
                message=(
                    f"Loop Detected: '{most_common_file}' 파일이 "
                    f"최근 {window}회 중 {count}회 수정되었습니다."
                ),
                recommendation=(
                    "접근 방식을 변경하십시오. 다른 파일을 먼저 수정하거나, "
                    "문제의 근본 원인을 다시 분석하십시오."
                ),
                details={
                    "file": most_common_file,
                    "modification_count": count,
                    "consecutive_count": consecutive_count,
                    "window_size": window,
                    "all_files": files
                }
            )
        
        return None

    def _detect_error_loop(
        self, 
        recent: List[Dict[str, Any]]
    ) -> Optional[AuditResult]:
        """에러 반복 패턴 감지"""
        errors = [
            h.get("error") 
            for h in recent 
            if h.get("status") == "failed" and h.get("error")
        ]
        
        if len(errors) < 2:
            return None
            
        # 마지막 두 에러가 유사한지 확인
        if errors[-1] == errors[-2]:
            # 동일 에러가 3회 이상 연속인지 확인
            consecutive_error_count = 1
            last_error = errors[-1]
            for err in reversed(errors[:-1]):
                if err == last_error:
                    consecutive_error_count += 1
                else:
                    break
            
            severity = AuditSeverity.CRITICAL if consecutive_error_count >= 3 else AuditSeverity.WARNING
            
            error_preview = errors[-1][:80] if len(errors[-1]) > 80 else errors[-1]
            
            return AuditResult(
                has_issue=True,
                severity=severity,
                message=(
                    f"Persistent Error: 동일한 에러가 {consecutive_error_count}회 "
                    f"반복되고 있습니다. ('{error_preview}...')"
                ),
                recommendation=(
                    "동일한 접근법으로는 해결되지 않습니다. "
                    "에러의 근본 원인을 재분석하고, 다른 해결책을 시도하십시오."
                ),
                details={
                    "error_message": errors[-1],
                    "consecutive_count": consecutive_error_count,
                    "total_errors_in_window": len(errors)
                }
            )
        
        return None

    def _detect_action_pattern_loop(
        self, 
        recent: List[Dict[str, Any]]
    ) -> Optional[AuditResult]:
        """액션 패턴 반복 감지 (동일 action+file 조합)"""
        if len(recent) < 3:
            return None
            
        # (action, file) 튜플로 패턴 추출
        patterns = [
            (h.get("action", ""), h.get("file", "")) 
            for h in recent
        ]
        
        pattern_counts = Counter(patterns)
        most_common_pattern, count = pattern_counts.most_common(1)[0]
        
        if count >= 3 and patterns[-1] == most_common_pattern:
            action, file = most_common_pattern
            return AuditResult(
                has_issue=True,
                severity=AuditSeverity.WARNING,
                message=(
                    f"Action Pattern Loop: '{action}' on '{file}' 패턴이 "
                    f"{count}회 반복되고 있습니다."
                ),
                recommendation=(
                    "같은 액션을 반복하고 있습니다. "
                    "전략을 변경하거나 다른 목표로 전환을 고려하십시오."
                ),
                details={
                    "action": action,
                    "file": file,
                    "repeat_count": count
                }
            )
        
        return None

    def audit_roadmap_alignment(
        self, 
        current_focus: str, 
        recent_actions: List[Dict[str, Any]]
    ) -> Tuple[float, Optional[AuditResult]]:
        """
        최근 행동이 현재 로드맵 목표와 얼마나 일치하는지 평가한다.
        
        Args:
            current_focus: 현재 로드맵 단계 (예: "step_7_meta_cognition")
            recent_actions: 최근 행동 리스트
            
        Returns:
            (일치도 점수 0.0~1.0, AuditResult 또는 None)
        """
        if not current_focus or not recent_actions:
            return 0.5, None  # 정보 부족 시 중립
            
        # 로드맵 키워드 추출
        keywords = self._extract_roadmap_keywords(current_focus)
        
        if not keywords:
            return 1.0, None  # 특정 키워드 없으면 통과

        match_count = 0
        total_checked = 0
        matched_actions = []
        unmatched_actions = []
        
        for action in recent_actions[-self.LOOP_WINDOW_SIZE:]:
            desc = action.get("description", "").lower()
            file_path = action.get("file", "").lower()
            
            total_checked += 1
            
            matched = any(k in desc or k in file_path for k in keywords)
            if matched:
                match_count += 1
                matched_actions.append(action.get("file", "unknown"))
            else:
                unmatched_actions.append(action.get("file", "unknown"))
        
        if total_checked == 0:
            return 1.0, None
            
        alignment_score = match_count / total_checked
        
        # 정렬도가 낮으면 경고 생성
        if alignment_score < self.ALIGNMENT_THRESHOLD:
            return alignment_score, AuditResult(
                has_issue=True,
                severity=AuditSeverity.WARNING,
                message=(
                    f"Roadmap Misalignment: 최근 행동의 {alignment_score*100:.0f}%만이 "
                    f"현재 목표({current_focus})와 관련됩니다."
                ),
                recommendation=(
                    f"현재 로드맵 단계({current_focus})에 집중하십시오. "
                    f"관련 키워드: {', '.join(keywords[:5])}"
                ),
                details={
                    "alignment_score": alignment_score,
                    "current_focus": current_focus,
                    "keywords": keywords,
                    "matched_files": matched_actions,
                    "unmatched_files": unmatched_actions
                }
            )
        
        return alignment_score, None

    def _extract_roadmap_keywords(self, current_focus: str) -> List[str]:
        """로드맵 단계에서 관련 키워드를 추출"""
        focus_lower = current_focus.lower()
        
        keyword_map = {
            "vector": ["vector", "lance", "memory", "embedding", "semantic"],
            "meta": ["meta", "monitor", "evaluator", "strategy", "audit", "cognition"],
            "intuition": ["intuition", "pattern", "system 1", "fast", "recognition"],
            "consciousness": ["consciousness", "awareness", "stream", "monologue"],
            "intention": ["intention", "goal", "purpose", "objective"],
            "memory": ["memory", "consolidation", "hippocampus", "recall"],
            "temporal": ["temporal", "time", "continuity", "self"],
        }
        
        keywords = []
        for key, words in keyword_map.items():
            if key in focus_lower:
                keywords.extend(words)
        
        return keywords

    def detect_stagnation(
        self, 
        metrics_history: List[Dict[str, Any]]
    ) -> Optional[AuditResult]:
        """
        성장 지표(Growth Score)의 정체 여부를 감지한다.
        
        Args:
            metrics_history: 과거 메트릭스 기록 리스트
            
        Returns:
            AuditResult 객체 (정체 감지 시) 또는 None
        """
        if len(metrics_history) < self.STAGNATION_WINDOW:
            return None
            
        # 최근 N번의 기록 동안 점수 변화가 없는지 확인
        scores = [
            m.get("growth_score", 0) 
            for m in metrics_history[-self.STAGNATION_WINDOW:]
        ]
        
        if not scores:
            return None
            
        score_range = max(scores) - min(scores)
        
        if score_range == 0:
            return AuditResult(
                has_issue=True,
                severity=AuditSeverity.WARNING,
                message=(
                    f"Stagnation Detected: 최근 {self.STAGNATION_WINDOW}회 동안 "
                    f"성장 점수({scores[-1]})에 변화가 없습니다."
                ),
                recommendation=(
                    "성장이 정체되어 있습니다. 새로운 도전적인 목표를 설정하거나, "
                    "다른 영역으로 진화 방향을 전환해 보십시오."
                ),
                details={
                    "current_score": scores[-1],
                    "score_history": scores,
                    "window_size": self.STAGNATION_WINDOW
                }
            )
        
        return None

    def run_full_audit(
        self,
        history: List[Dict[str, Any]],
        metrics_history: List[Dict[str, Any]],
        current_focus: str
    ) -> Dict[str, Any]:
        """
        모든 감사를 실행하고 종합 리포트를 반환한다.
        
        Args:
            history: 진화 기록 리스트
            metrics_history: 메트릭스 기록 리스트
            current_focus: 현재 로드맵 단계
            
        Returns:
            종합 감사 리포트 딕셔너리
        """
        report = {
            "timestamp": None,
            "overall_health": "healthy",
            "issues": [],
            "warnings": [],
            "recommendations": [],
            "alignment_score": 1.0
        }
        
        from datetime import datetime
        report["timestamp"] = datetime.now().isoformat()
        
        # 1. 순환 추론 감사
        loop_result = self.audit_reasoning_loop(history)
        if loop_result is not None:
            if loop_result.severity == AuditSeverity.CRITICAL:
                report["issues"].append(loop_result.message)
                report["overall_health"] = "critical"
            else:
                report["warnings"].append(loop_result.message)
                if report["overall_health"] == "healthy":
                    report["overall_health"] = "degraded"
            report["recommendations"].append(loop_result.recommendation)
        
        # 2. 로드맵 정렬 감사
        alignment_score, alignment_result = self.audit_roadmap_alignment(
            current_focus, history
        )
        report["alignment_score"] = alignment_score
        if alignment_result is not None:
            report["warnings"].append(alignment_result.message)
            report["recommendations"].append(alignment_result.recommendation)
            if report["overall_health"] == "healthy":
                report["overall_health"] = "degraded"
        
        # 3. 정체 감사
        stagnation_result = self.detect_stagnation(metrics_history)
        if stagnation_result is not None:
            report["warnings"].append(stagnation_result.message)
            report["recommendations"].append(stagnation_result.recommendation)
            if report["overall_health"] == "healthy":
                report["overall_health"] = "degraded"
        
        return report