"""
AIN의 뇌량 (Corpus Callosum):
좌뇌(Fact Core/Logic)와 우뇌(Nexus/Intuition) 사이의 정보 교환을 담당하는 브릿지.

모듈화된 corpus 패키지를 사용합니다.

하위 호환성:
- from corpus_callosum import CorpusCallosum  # 기존 방식
- from corpus import CorpusCallosum           # 새로운 방식
"""

# corpus 패키지에서 CorpusCallosum re-export
from corpus import CorpusCallosum

__all__ = ['CorpusCallosum']
