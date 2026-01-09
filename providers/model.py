"""
LLM 프로바이더를 위한 추상 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Optional


class ModelProvider(ABC):
    """
    모든 LLM 프로바이더가 구현해야 하는 추상 기본 클래스입니다.
    
    이 클래스를 상속하여 OpenAI, Anthropic, Gemini 등 다양한 LLM 프로바이더를 구현할 수 있습니다.
    """
    
    @abstractmethod
    async def evaluate_model(self, prompt: str) -> str:
        """
        주어진 프롬프트로 모델을 평가하고 응답을 반환합니다.
        
        Args:
            prompt (str): 모델에 보낼 프롬프트
            
        Returns:
            str: 모델의 응답
        """
        ...

    @abstractmethod
    def generate_prompt(self, context: str, retrieval_question: str) -> str | list[dict[str, str]]:
        """
        컨텍스트와 검색 질문을 기반으로 프롬프트를 생성합니다.
        
        Args:
            context (str): 배경 컨텍스트
            retrieval_question (str): 검색 질문
            
        Returns:
            str | list[dict[str, str]]: 생성된 프롬프트 (문자열 또는 메시지 리스트)
        """
        ...

    @abstractmethod
    def encode_text_to_tokens(self, text: str) -> list[int]:
        """
        텍스트를 토큰 ID 리스트로 인코딩합니다.
        
        Args:
            text (str): 인코딩할 텍스트
            
        Returns:
            list[int]: 토큰 ID 리스트
        """
        ...

    @abstractmethod
    def decode_tokens(self, tokens: list[int], context_length: Optional[int] = None) -> str:
        """
        토큰 ID 리스트를 텍스트로 디코딩합니다.
        
        Args:
            tokens (list[int]): 디코딩할 토큰 ID 리스트
            context_length (Optional[int]): 디코딩할 최대 토큰 수 (None이면 전체)
            
        Returns:
            str: 디코딩된 텍스트
        """
        ...






