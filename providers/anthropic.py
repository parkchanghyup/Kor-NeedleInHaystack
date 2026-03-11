"""
Anthropic Claude 모델을 위한 프로바이더
"""

import os
from typing import Optional
from anthropic import AsyncAnthropic
from .model import ModelProvider

# Anthropic tokenizer는 선택적 의존성
try:
    from anthropic import Anthropic as AnthropicModel
    TOKENIZER_AVAILABLE = True
except ImportError:
    TOKENIZER_AVAILABLE = False
    # tiktoken을 대체 토크나이저로 사용
    import tiktoken


class Anthropic(ModelProvider):
    """
    Anthropic Claude API를 사용하는 프로바이더입니다.
    
    Claude 모델 시리즈(claude-3-opus, claude-3-sonnet 등)를 지원합니다.
    
    Attributes:
        model_name (str): 사용할 Claude 모델 이름
        model_kwargs (dict): 모델 설정 (max_tokens, temperature 등)
        api_key (str): Anthropic API 키
    """
    
    DEFAULT_MODEL_KWARGS: dict = dict(max_tokens=300, temperature=0)

    def __init__(self, model_name: str = 'claude-3-5-sonnet-latest', model_kwargs: dict = DEFAULT_MODEL_KWARGS):
        """
        Anthropic 프로바이더를 초기화합니다.
        
        Args:
            model_name (str): 사용할 Claude 모델 이름. 기본값은 'claude-3-5-sonnet-latest'
            model_kwargs (dict): 모델 설정. 기본값은 {max_tokens: 300, temperature: 0}
            
        Raises:
            ValueError: 모델 이름에 'claude'가 포함되지 않거나 API 키가 없는 경우
        """
        if 'claude' not in model_name:
            raise ValueError("Anthropic 프로바이더는 모델 이름에 'claude'가 포함되어야 합니다.")
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError('ANTHROPIC_API_KEY가 환경 변수에 설정되어야 합니다.')
        self.model_name = model_name
        self.model_kwargs = model_kwargs
        self.api_key = api_key
        self.model = AsyncAnthropic(api_key=self.api_key)
        
        # 토크나이저 설정
        if TOKENIZER_AVAILABLE:
            self.tokenizer = AnthropicModel().get_tokenizer()
            self.use_anthropic_tokenizer = True
        else:
            # tiktoken을 대체로 사용
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
            self.use_anthropic_tokenizer = False

    SYSTEM_PROMPT = "You are a helpful AI bot that answers questions for a user. Keep your response short and direct"

    async def evaluate_model(self, prompt: dict) -> str:
        """
        Anthropic Messages API를 사용하여 모델 평가
        
        Args:
            prompt: generate_prompt()에서 반환된 딕셔너리 (system, messages 포함)
            
        Returns:
            str: 모델의 응답
        """
        try:
            response = await self.model.messages.create(
                model=self.model_name,
                system=prompt["system"],
                messages=prompt["messages"],
                **self.model_kwargs
            )
            return response.content[0].text
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_prompt(self, context: str, retrieval_question: str) -> dict:
        """
        컨텍스트와 질문으로 Anthropic 형식의 프롬프트 생성
        
        Args:
            context: 배경 컨텍스트
            retrieval_question: 검색 질문
            
        Returns:
            dict: system 프롬프트와 messages를 포함하는 딕셔너리
        """
        return {
            "system": self.SYSTEM_PROMPT,
            "messages": [
                {"role": "user", "content": context},
                {"role": "user", "content": f"{retrieval_question} Don't give information outside the document or repeat your findings"}
            ]
        }

    def encode_text_to_tokens(self, text: str) -> list[int]:
        """텍스트를 토큰으로 인코딩"""
        if self.use_anthropic_tokenizer:
            return self.tokenizer.encode(text).ids
        else:
            return self.tokenizer.encode(text)

    def decode_tokens(self, tokens: list[int], context_length: Optional[int] = None) -> str:
        """토큰을 텍스트로 디코딩"""
        return self.tokenizer.decode(tokens[:context_length])
