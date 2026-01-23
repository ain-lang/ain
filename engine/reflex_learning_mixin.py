"""
Engine Reflex Learning Mixin
============================
AINCore에 Reflex Learning 기능을 추가하는 Mixin

ReflexLearner를 내부적으로 사용하여 System 2(Evolution)에서
학습한 패턴을 System 1(Reflex)으로 이관하는 기능을 제공한다.

Usage:
    class AINCore(ReflexLearningMixin, ...):
        pass

    ain = AINCore()
    # 주기적 또는 수동으로 학습 사이클 실행
    await ain.run_reflex_learning_cycle()
"""

import asyncio
from typing import List, Dict, Any, Optional

try:
    from engine.reflex_store import ReflexStore
    HAS_REFLEX_STORE = True
except ImportError:
    HAS_REFLEX_STORE = False


class ReflexLearningMixin:
    """
    Reflex Learning 기능을 제공하는 Mixin

    AINCore에 상속되어 반사 행동 학습 기능을 노출한다.

    Required attributes from AINCore:
    """

    _reflex_learner: Optional[Any] = None
    _reflex_store_instance: Optional[Any] = None

    def _get_reflex_learner(self):
        """ReflexLearner 인스턴스를 lazy-load로 가져온다."""
        if self._reflex_learner is None:
            try:
                from .reflex_learner import ReflexLearner
                if hasattr(self, 'nexus') and hasattr(self, 'muse'):
                    self._reflex_learner = ReflexLearner(self.nexus, self.muse)
                else:
                    print("⚠️ ReflexLearner 초기화 실패: Nexus 또는 Muse가 없습니다.")
            except ImportError:
                print("⚠️ ReflexLearner 모듈을 찾을 수 없습니다.")
        return self._reflex_learner

    def _get_reflex_store(self):
        """ReflexStore 인스턴스 확보 (AINCore에 없으면 로컬 생성 시도)"""
        if hasattr(self, 'reflex_store') and self.reflex_store:
            return self.reflex_store
        
        if self._reflex_store_instance:
            return self._reflex_store_instance

        if HAS_REFLEX_STORE:
            try:
                self._reflex_store_instance = ReflexStore()
                return self._reflex_store_instance
            except Exception as e:
                print(f"⚠️ ReflexStore 로컬 생성 실패: {e}")
        
        return None

    async def run_reflex_learning_cycle(self) -> Dict[str, Any]:
        """
        반사 행동 학습 사이클을 실행한다.
        
        System 2(진화/대화 기록)를 분석하여 반복적인 패턴을 찾고,
        이를 System 1(반사 행동) 후보로 제안 및 저장한다.
        
        Returns:
            학습 결과 리포트 (생성된 후보 수, 상태 등)
        """
        learner = self._get_reflex_learner()
        if not learner:
            return {"status": "failed", "reason": "learner_not_available"}

        print("🧠 [Reflex Learning] System 2 → System 1 지식 이관 시작...")
        
        try:
            candidates = await learner.propose_new_reflexes()
            
            if not candidates:
                print("💤 [Reflex Learning] 새로운 반사 행동 패턴이 감지되지 않았습니다.")
                return {"status": "no_candidates", "count": 0}

            print(f"✨ [Reflex Learning] {len(candidates)}개의 새로운 반사 행동 후보 발견!")
            for cand in candidates:
                cand_dict = cand.to_dict() if hasattr(cand, 'to_dict') else cand
                print(f"   - [{cand_dict.get('type')}] {cand_dict.get('name')}: {cand_dict.get('pattern')}")

            store = self._get_reflex_store()
            saved_count = 0
            if store and hasattr(store, 'add_candidate'):
                for cand in candidates:
                    try:
                        cand_dict = cand.to_dict() if hasattr(cand, 'to_dict') else cand
                        store.add_candidate(cand_dict)
                        saved_count += 1
                    except AttributeError:
                        print("⚠️ ReflexStore에 add_candidate 메서드가 없습니다.")
                        break
                    except Exception as e:
                        print(f"⚠️ 후보 저장 중 오류: {e}")
                
                if saved_count > 0:
                    print(f"💾 [Reflex Learning] {saved_count}개의 후보를 저장소에 등록했습니다.")
            else:
                print("⚠️ ReflexStore를 사용할 수 없어 후보를 저장하지 못했습니다.")

            return {
                "status": "success", 
                "candidates_found": len(candidates),
                "candidates_saved": saved_count
            }

        except Exception as e:
            print(f"❌ [Reflex Learning] 학습 중 오류 발생: {e}")
            return {"status": "error", "error": str(e)}

    async def propose_reflexes(self, lookback: int = 50) -> List[Dict[str, Any]]:
        """
        최근 진화 기록을 분석하여 새로운 반사 행동 후보를 제안한다.

        Args:
            lookback: 분석할 최근 기록 수

        Returns:
            ReflexCandidate 딕셔너리 리스트
        """
        learner = self._get_reflex_learner()
        if not learner:
            return []

        try:
            candidates = await learner.propose_new_reflexes(lookback=lookback)
            return [c.to_dict() if hasattr(c, 'to_dict') else c for c in candidates]
        except Exception as e:
            print(f"⚠️ [ReflexLearningMixin] 제안 실패: {e}")
            return []

    def get_learned_reflex_candidates(self) -> List[Dict[str, Any]]:
        """학습된 모든 반사 행동 후보를 반환한다."""
        learner = self._get_reflex_learner()
        if not learner:
            return []

        try:
            candidates = learner.get_learned_candidates()
            return [c.to_dict() if hasattr(c, 'to_dict') else c for c in candidates]
        except Exception as e:
            print(f"⚠️ [ReflexLearningMixin] 후보 조회 실패: {e}")
            return []

    def clear_reflex_candidates(self):
        """학습된 반사 행동 후보를 초기화한다."""
        learner = self._get_reflex_learner()
        if learner:
            try:
                learner.clear_candidates()
            except Exception as e:
                print(f"⚠️ [ReflexLearningMixin] 후보 초기화 실패: {e}")

    def export_reflex_candidates_json(self) -> str:
        """학습된 후보들을 JSON 문자열로 내보낸다."""
        learner = self._get_reflex_learner()
        if not learner:
            return "[]"

        try:
            return learner.export_candidates_to_json()
        except Exception as e:
            print(f"⚠️ [ReflexLearningMixin] JSON 내보내기 실패: {e}")
            return "[]"