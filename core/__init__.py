"""
한국어 버전 LLM Needle In A Haystack 테스트를 위한 핵심 모듈

이 패키지는 LLM의 긴 컨텍스트 검색 능력을 테스트하기 위한 핵심 클래스들을 제공합니다.
- LLMNeedleHaystackTesterKor: 단일 needle 테스트
- LLMMultiNeedleHaystackTesterKor: 다중 needle 테스트
"""
from .single_needle import LLMNeedleHaystackTesterKor
from .multi_needle import LLMMultiNeedleHaystackTesterKor

__all__ = ['LLMNeedleHaystackTesterKor', 'LLMMultiNeedleHaystackTesterKor']






