"""
Google Gemini 모델을 위한 프로바이더 (New google-genai API)
"""

import os
from typing import Optional
from google import genai
from google.genai import types
import tiktoken
from .model import ModelProvider


class Gemini(ModelProvider):
    """
    Google Gemini API(google-genai)를 사용하는 프로바이더입니다.

    Gemini 모델 시리즈(gemini-1.5-flash, gemini-2.0-flash-lite 등)를 지원합니다.

    Attributes:
        model_name (str): 사용할 Gemini 모델 이름
        model_kwargs (dict): 모델 설정 (temperature 등)
        api_key (str): Google API 키
    """

    def __init__(self, model_name: str = "gemini-2.5-flash", model_kwargs: dict = None):
        """
        Gemini 프로바이더를 초기화합니다.

        Args:
            model_name (str): 사용할 Gemini 모델 이름. 기본값은 'gemini-2.5-flash'
            model_kwargs (dict): 모델 설정. 기본값은 None (빈 딕셔너리로 처리)

        Raises:
            ValueError: API 키가 환경 변수에 없는 경우
        """
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY가 환경 변수에 설정되어야 합니다.")

        self.model_name = model_name
        self.model_kwargs = model_kwargs or {}
        self.api_key = api_key

        # 새로운 google.genai API 사용
        self.client = genai.Client(api_key=api_key)

        # 주의: Gemini 모델의 실제 토크나이저와 cl100k_base(OpenAI)는 한국어에서
        # 토큰 수 차이가 클 수 있습니다. 이로 인해 컨텍스트 길이 계산이 부정확할 수 있으나,
        # google-genai API가 토큰 ID 리스트 반환을 지원하지 않아 encode/decode 인터페이스를
        # 유지하기 위해 tiktoken을 근사치로 사용합니다.
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        import warnings
        warnings.warn(
            "Gemini 프로바이더는 tiktoken(cl100k_base)을 근사 토크나이저로 사용합니다. "
            "한국어 텍스트에서 실제 Gemini 토큰 수와 차이가 있을 수 있습니다.",
            stacklevel=2
        )

    async def evaluate_model(self, prompt: str) -> str:
        """
        주어진 프롬프트로 Gemini 모델을 평가하고 응답을 반환합니다.

        Args:
            prompt (str): 모델에 보낼 프롬프트

        Returns:
            str: 모델의 응답. 에러 발생 시 "Error: ..." 형식으로 반환
        """
        try:
            # 새로운 API 사용
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(**self.model_kwargs)
                if self.model_kwargs
                else None,
            )
            return response.text
        except Exception as e:
            # 안전성 차단 또는 기타 에러 처리
            return f"Error: {str(e)}"

    def generate_prompt(self, context: str, retrieval_question: str) -> str:
        """
        컨텍스트와 검색 질문을 기반으로 프롬프트를 생성합니다.

        Args:
            context (str): 배경 컨텍스트
            retrieval_question (str): 검색 질문

        Returns:
            str: 생성된 프롬프트
        """
        return f"""You are a helpful AI bot that answers questions for a user. Keep your response short and direct.
        
Context:
{context}

Question:
{retrieval_question}

Don't give information outside the document or repeat your findings."""

    def encode_text_to_tokens(self, text: str) -> list[int]:
        """
        텍스트를 토큰 ID 리스트로 인코딩합니다.

        Args:
            text (str): 인코딩할 텍스트

        Returns:
            list[int]: 토큰 ID 리스트
        """
        return self.tokenizer.encode(text)

    def decode_tokens(
        self, tokens: list[int], context_length: Optional[int] = None
    ) -> str:
        """
        토큰 ID 리스트를 텍스트로 디코딩합니다.

        Args:
            tokens (list[int]): 디코딩할 토큰 ID 리스트
            context_length (Optional[int]): 디코딩할 최대 토큰 수 (None이면 전체)

        Returns:
            str: 디코딩된 텍스트
        """
        return self.tokenizer.decode(tokens[:context_length])
