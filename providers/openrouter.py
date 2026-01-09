"""
OpenRouter API를 위한 프로바이더
"""

import os
from typing import Optional

from openai import AsyncOpenAI
import tiktoken

from .model import ModelProvider


class OpenRouter(ModelProvider):
    """
    OpenRouter API를 사용하는 프로바이더입니다.
    
    OpenAI 호환 API를 사용하므로 OpenAI 클라이언트를 재활용합니다.
    다양한 오픈소스 모델에 통합 API로 접근할 수 있습니다.
    
    지원 모델 예시:
        - google/gemma-2-9b-it
        - meta-llama/llama-3.1-8b-instruct
        - mistralai/mistral-7b-instruct
        - qwen/qwen-2-7b-instruct
        - 기타 (https://openrouter.ai/models 참고)
    
    Attributes:
        model_name (str): 사용할 모델 이름 (예: "google/gemma-2-9b-it")
        model_kwargs (dict): 모델 설정 (temperature, max_tokens 등)
        api_key (str): OpenRouter API 키
    """
    
    def __init__(self, 
                 model_name: str = "google/gemma-2-9b-it",
                 model_kwargs: dict = None):
        """
        OpenRouter 프로바이더 초기화
        
        Args:
            model_name: OpenRouter 모델 이름 (예: "google/gemma-2-9b-it")
            model_kwargs: 모델 설정 (temperature, max_tokens 등)
        """
        # API 키 확인 (우선순위: OPENROUTER_API_KEY > NIAH_MODEL_API_KEY)
        api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('NIAH_MODEL_API_KEY')
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY 또는 NIAH_MODEL_API_KEY가 환경 변수에 설정되어야 합니다.")
        
        self.model_name = model_name
        self.model_kwargs = model_kwargs or {}
        self.api_key = api_key
        
        # OpenRouter API 엔드포인트로 OpenAI 클라이언트 생성
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=self.api_key,
        )
        
        # 토큰 인코딩 (OpenAI 표준 사용)
        self.encoding = tiktoken.get_encoding("cl100k_base")

    async def evaluate_model(self, prompt: str | list[dict[str, str]]) -> str:
        """
        OpenRouter API를 통해 모델 평가
        
        Args:
            prompt: 평가할 프롬프트 (문자열 또는 메시지 리스트)
            
        Returns:
            str: 모델의 응답
        """
        try:
            # prompt가 문자열이면 user 메시지로 변환
            if isinstance(prompt, str):
                messages = [{"role": "user", "content": prompt}]
            else:
                messages = prompt
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                **self.model_kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"

    def get_langchain_runnable(self, context: str):
        """
        컨텍스트가 바인딩된 LangChain Runnable을 반환합니다.
        
        Args:
            context (str): 바인딩할 컨텍스트
            
        Returns:
            Chain: question만 입력받는 LangChain 체인
        """
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser

        model = ChatOpenAI(
            model=self.model_name,
            openai_api_key=self.api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            **self.model_kwargs
        )

        template = """You are a helpful AI bot that answers questions for a user. Keep your response short and direct.

Context:
{context}

Question:
{question}

Don't give information outside the document or repeat your findings."""

        prompt = ChatPromptTemplate.from_template(template)
        
        # context를 partial로 바인딩하여 question만 입력받는 체인 생성
        chain = prompt.partial(context=context) | model | StrOutputParser()
        return chain

    def generate_prompt(self, context: str, retrieval_question: str) -> str:
        """
        컨텍스트와 질문으로 프롬프트 생성
        
        Args:
            context: 배경 컨텍스트
            retrieval_question: 검색 질문
            
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
        텍스트를 토큰으로 인코딩
        
        Args:
            text: 인코딩할 텍스트
            
        Returns:
            list[int]: 토큰 ID 리스트
        """
        return self.encoding.encode(text)

    def decode_tokens(self, tokens: list[int], context_length: Optional[int] = None) -> str:
        """
        토큰을 텍스트로 디코딩
        
        Args:
            tokens: 디코딩할 토큰 ID 리스트
            context_length: 디코딩할 최대 길이 (None이면 전체)
            
        Returns:
            str: 디코딩된 텍스트
        """
        return self.encoding.decode(tokens[:context_length])

