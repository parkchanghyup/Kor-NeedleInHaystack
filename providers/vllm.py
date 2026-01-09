"""
vLLM 서버를 위한 프로바이더
"""

import os
from typing import Optional

from openai import AsyncOpenAI
import tiktoken

from .model import ModelProvider


class VLLM(ModelProvider):
    """
    vLLM serve로 띄운 모델을 사용하는 프로바이더입니다.
    
    vLLM은 OpenAI 호환 API를 제공하므로 OpenAI 클라이언트를 재활용합니다.
    로컬 또는 원격 vLLM 서버에 연결하여 모델을 사용할 수 있습니다.
    
    사용 예시:
        1. vLLM 서버 시작:
           vllm serve <model_name> --host 0.0.0.0 --port 8000
        
        2. 환경 변수 설정:
           export VLLM_API_BASE="http://localhost:8000/v1"
           export VLLM_MODEL_NAME="your-model-name"
    
    지원 모델:
        - vLLM에서 지원하는 모든 HuggingFace 모델
        - Llama, Mistral, Qwen, Gemma 등
    
    Attributes:
        model_name (str): 사용할 모델 이름
        api_base (str): vLLM 서버 주소
        model_kwargs (dict): 모델 설정 (temperature, max_tokens 등)
    """
    
    def __init__(self, 
                 model_name: str = None,
                 api_base: str = None,
                 api_key: str = "EMPTY",
                 model_kwargs: dict = None):
        """
        vLLM 프로바이더 초기화
        
        Args:
            model_name: 모델 이름 (환경 변수 VLLM_MODEL_NAME 또는 직접 지정)
            api_base: vLLM 서버 주소 (환경 변수 VLLM_API_BASE 또는 직접 지정)
            api_key: API 키 (vLLM은 기본적으로 인증 불필요, "EMPTY" 사용)
            model_kwargs: 모델 설정 (temperature, max_tokens 등)
        """
        # API 베이스 URL 확인 (우선순위: 파라미터 > 환경 변수 > 기본값)
        self.api_base = api_base or os.getenv('VLLM_API_BASE', 'http://localhost:8000/v1')
        
        # 모델 이름 확인 (우선순위: 파라미터 > 환경 변수)
        self.model_name = model_name or os.getenv('VLLM_MODEL_NAME')
        if not self.model_name:
            raise ValueError(
                "모델 이름이 지정되지 않았습니다. "
                "VLLM_MODEL_NAME 환경 변수를 설정하거나 model_name 파라미터를 전달하세요."
            )
        
        # API 키 (vLLM은 기본적으로 인증이 필요 없지만 OpenAI 클라이언트 호환을 위해 설정)
        self.api_key = api_key or os.getenv('VLLM_API_KEY', 'EMPTY')
        
        self.model_kwargs = model_kwargs or {}
        
        # vLLM API 엔드포인트로 OpenAI 클라이언트 생성
        self.client = AsyncOpenAI(
            base_url=self.api_base,
            api_key=self.api_key,
        )
        
        # 토큰 인코딩 (OpenAI 표준 사용)
        # 참고: 실제 모델의 토크나이저와 다를 수 있으나 근사치로 사용
        self.encoding = tiktoken.get_encoding("cl100k_base")

    async def evaluate_model(self, prompt: str | list[dict[str, str]]) -> str:
        """
        vLLM API를 통해 모델 평가
        
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
            openai_api_base=self.api_base,
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

