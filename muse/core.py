"""
Muse Core: AIN의 Muse Generator 클래스
- Dreamer와 Coder의 오케스트레이션
- 진화 상상 메인 로직
"""

from typing import Dict, Any, Optional

from api import OpenRouterClient
from .dreamer import run_dreamer_pipeline, extract_intent
from .coder import run_coder_pipeline, extract_target_files_content
from .parser import parse_coder_output


class Muse:
    """
    AIN의 Muse Generator (Dynamic Tensor Flow):
    2x2 매트릭스 아키텍처를 기반으로 '상상'과 '구현'을 분리한다.
    - Dreamer: Gemini 3 Pro (고차원 추론 및 전략 수립)
    - Coder: Claude 4.5 Opus (정교한 코드 생성 및 버그 수정)
    """

    def __init__(self, dreamer_model: str, coder_model: str, prime_directive: str):
        self.dreamer_client = OpenRouterClient(model=dreamer_model)
        self.coder_client = OpenRouterClient(model=coder_model)
        self.prime_directive = prime_directive

    def _ask_dreamer(self, prompt: str) -> str:
        """
        Dreamer에게 간단한 질문을 하고 응답을 받음
        Inner Monologue 등 외부 모듈에서 사용
        """
        try:
            result = self.dreamer_client.chat([
                {"role": "system", "content": "너는 AIN의 내부 의식이다. 간결하고 성찰적으로 답하라."},
                {"role": "user", "content": prompt}
            ])
            if result.get("success"):
                return result.get("content", "")
            return ""
        except Exception as e:
            print(f"⚠️ Dreamer 질문 실패: {e}")
            return ""

    def imagine(
        self,
        system_context: str,
        user_query: Optional[str] = None,
        evolution_history: Optional[Any] = None,
        error_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        [Muse] Dreamer와 Coder의 협업을 통해 진화를 상상함

        Args:
            system_context: 시스템 코드 스냅샷
            user_query: 사용자 명령 (선택)
            evolution_history: 진화 히스토리 (미사용, 호환성 유지)
            error_context: 에러 컨텍스트 (선택)

        Returns:
            {
                "intent": str,
                "updates": List[Dict],
                "error": Optional[str],
                "no_evolution": bool
            }
        """
        # 1. Dreamer 파이프라인 실행
        dreamer_result = run_dreamer_pipeline(
            dreamer_client=self.dreamer_client,
            system_context=system_context,
            prime_directive=self.prime_directive,
            error_context=error_context,
            user_query=user_query
        )

        if not dreamer_result["success"]:
            return {
                "intent": "Dreaming failed",
                "updates": [],
                "error": dreamer_result.get("error")
            }

        intent_design = dreamer_result["intent_design"]
        intent = dreamer_result["intent"]
        compressed_code = dreamer_result["compressed_code"]

        print(f"📋 [Muse] 추출된 의도: {intent[:100]}...")

        # 2. Coder 파이프라인 실행
        print(f"💻 Coder (Claude 4.5 Opus)가 새로운 모듈을 생성 중...")

        coder_result = run_coder_pipeline(
            coder_client=self.coder_client,
            intent_design=intent_design,
            compressed_code=compressed_code,
            target_files=[]
        )

        if not coder_result["success"]:
            return {
                "intent": "Coding failed after retries",
                "updates": [],
                "error": coder_result.get("error")
            }

        code_output = coder_result["code_output"]

        # 3. 결과 파싱
        parse_result = parse_coder_output(code_output, intent)

        if parse_result.get("no_evolution"):
            return {
                "intent": f"진화 스킵: {parse_result.get('reason', '')}",
                "updates": [],
                "no_evolution": True
            }

        if parse_result.get("error"):
            return {
                "intent": intent,
                "updates": [],
                "error": parse_result["error"]
            }

        return {
            "intent": intent,
            "updates": parse_result["updates"]
        }
