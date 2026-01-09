"""
LLM 프로바이더 패키지

다양한 LLM API 프로바이더를 통합된 인터페이스로 제공합니다.
- OpenAI: GPT 시리즈 모델
- Anthropic: Claude 시리즈 모델
- Gemini: Google Gemini 모델
- OpenRouter: 다양한 오픈 모델에 대한 통합 API
- VLLM: 로컬/원격 vLLM 서버
"""

from .model import ModelProvider
from .openai import OpenAI

__all__ = ['ModelProvider', 'OpenAI']

# Anthropic, Gemini, OpenRouter, VLLM은 선택적 의존성이므로 조건부 import
try:
    from .anthropic import Anthropic
    __all__.append('Anthropic')
except ImportError:
    Anthropic = None

try:
    from .gemini import Gemini
    __all__.append('Gemini')
except ImportError:
    Gemini = None

try:
    from .openrouter import OpenRouter
    __all__.append('OpenRouter')
except ImportError:
    OpenRouter = None

try:
    from .vllm import VLLM
    __all__.append('VLLM')
except ImportError:
    VLLM = None

