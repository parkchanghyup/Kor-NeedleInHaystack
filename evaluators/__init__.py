"""
LLM 응답 평가자(Evaluator) 패키지

모델의 응답을 평가하고 점수를 부여하는 평가자들을 제공합니다.
- OpenAIEvaluator: OpenAI 모델을 사용한 평가
- GeminiEvaluator: Google Gemini 모델을 사용한 평가
"""

from .evaluator import Evaluator
from .openai import OpenAIEvaluator

__all__ = ['Evaluator', 'OpenAIEvaluator']

# Gemini Evaluator는 선택적 의존성이므로 조건부 import
try:
    from .gemini import GeminiEvaluator
    __all__.append('GeminiEvaluator')
except ImportError:
    GeminiEvaluator = None

