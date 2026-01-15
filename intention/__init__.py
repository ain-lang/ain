"""
AIN Intention Package
Step 6: Intentionality - 자율적 목표 설정 및 관리 시스템

이 패키지는 AIN이 스스로 목표를 생성하고, 우선순위를 결정하며,
달성 여부를 추적할 수 있는 '전두엽(Frontal Lobe)' 역할을 수행한다.

모듈 구조:
"""

from .core import IntentionCore, Goal, GoalStatus

__all__ = ['IntentionCore', 'Goal', 'GoalStatus']