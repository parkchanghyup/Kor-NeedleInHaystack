import os
from typing import Optional

from openai import AsyncOpenAI
import tiktoken

from .model import ModelProvider

# LangChain은 선택적 의존성 (get_langchain_runnable 메서드 사용 시에만 필요)
try:
    from operator import itemgetter
    from langchain_openai import ChatOpenAI  
    from langchain.prompts import PromptTemplate
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class OpenAI(ModelProvider):
    """
    OpenAI API와 상호작용하기 위한 래퍼 클래스입니다.
    텍스트 인코딩, 프롬프트 생성, 모델 평가, LangChain 런너블 생성 기능을 제공합니다.

    Attributes:
        model_name (str): 평가 및 상호작용에 사용할 OpenAI 모델 이름
        model (AsyncOpenAI): 비동기 API 호출을 위한 AsyncOpenAI 클라이언트 인스턴스
        tokenizer: 텍스트를 토큰으로 인코딩/디코딩하기 위한 토크나이저 인스턴스
    """
        
    DEFAULT_MODEL_KWARGS: dict = dict(max_tokens  = 300,
                                      temperature = 0)

    def __init__(self,
                 model_name: str = "gpt-4o-mini",
                 model_kwargs: dict = DEFAULT_MODEL_KWARGS):
        """
        특정 모델로 OpenAI 프로바이더를 초기화합니다.

        Args:
            model_name (str): 사용할 OpenAI 모델 이름. 기본값은 'gpt-4o-mini'
            model_kwargs (dict): 모델 설정. 기본값은 {max_tokens: 300, temperature: 0}
        
        Raises:
            ValueError: OPENAI_API_KEY가 환경 변수에 없는 경우
        """
        # OPENAI_API_KEY
        api_key = os.getenv('OPENAI_API_KEY')
        if (not api_key):
            raise ValueError("OPENAI_API_KEY가 환경 변수에 설정되어야 합니다.")

        self.model_name = model_name
        self.model_kwargs = model_kwargs
        self.api_key = api_key
        self.model = AsyncOpenAI(api_key=self.api_key)
        self.tokenizer = tiktoken.encoding_for_model(self.model_name)
    
    async def evaluate_model(self, prompt: str) -> str:
        """
        주어진 프롬프트로 OpenAI 모델을 평가하고 응답을 반환합니다.

        Args:
            prompt (str): 모델에 보낼 프롬프트

        Returns:
            str: 프롬프트에 대한 모델의 응답 내용
        """
        response = await self.model.chat.completions.create(
                model=self.model_name,
                messages=prompt,
                **self.model_kwargs
            )
        return response.choices[0].message.content
    
    def generate_prompt(self, context: str, retrieval_question: str) -> str | list[dict[str, str]]:
        """
        주어진 컨텍스트와 검색 질문을 기반으로 구조화된 프롬프트를 생성합니다.

        Args:
            context (str): 질문과 관련된 컨텍스트 또는 배경 정보
            retrieval_question (str): 모델이 답해야 할 특정 질문

        Returns:
            list[dict[str, str]]: 시스템 및 사용자 메시지의 역할과 내용을 포함하는 구조화된 프롬프트 딕셔너리 리스트
        """
        return [{
                "role": "system",
                "content": "You are a helpful AI bot that answers questions for a user. Keep your response short and direct"
            },
            {
                "role": "user",
                "content": context
            },
            {
                "role": "user",
                "content": f"{retrieval_question} Don't give information outside the document or repeat your findings"
            }]
    
    def encode_text_to_tokens(self, text: str) -> list[int]:
        """
        모델의 토크나이저를 사용하여 주어진 텍스트를 토큰 시퀀스로 인코딩합니다.

        Args:
            text (str): 인코딩할 텍스트

        Returns:
            list[int]: 인코딩된 텍스트를 나타내는 토큰 ID 리스트
        """
        return self.tokenizer.encode(text)
    
    def decode_tokens(self, tokens: list[int], context_length: Optional[int] = None) -> str:
        """
        모델의 토크나이저를 사용하여 토큰 시퀀스를 텍스트 문자열로 디코딩합니다.

        Args:
            tokens (list[int]): 디코딩할 토큰 ID 시퀀스
            context_length (Optional[int], optional): 디코딩할 토큰 수를 지정하는 선택적 길이. 제공되지 않으면 모든 토큰을 디코딩합니다.

        Returns:
            str: 디코딩된 텍스트 문자열
        """
        return self.tokenizer.decode(tokens[:context_length])
    
    def get_langchain_runnable(self, context: str) -> str:
        """
        주어진 컨텍스트와 질문을 기반으로 프롬프트를 구성하고, OpenAI 모델에 쿼리하여
        응답을 반환하는 LangChain 런너블을 생성합니다. 이 메서드는 LangChain 라이브러리를
        활용하여 입력 변수 추출, 프롬프트 생성, 모델 쿼리, 응답 처리의 일련의 작업을 수행합니다.

        Args:
            context (str): 사용자 질문과 관련된 컨텍스트 또는 배경 정보.
            이 컨텍스트는 관련성 있고 정확한 응답을 생성하는 데 도움을 줍니다.

        Returns:
            str: 동적으로 제공된 질문에 대한 모델의 응답을 얻기 위해 실행할 수 있는
            LangChain 런너블 객체. 프롬프트 생성부터 응답 검색까지 전체 프로세스를 캡슐화합니다.

        Raises:
            ImportError: LangChain이 설치되지 않은 경우

        Example:
            런너블 사용 방법:
                - 컨텍스트와 질문을 정의합니다.
                - 이 파라미터들로 런너블을 실행하여 모델의 응답을 얻습니다.
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError(
                "LangChain이 설치되지 않았습니다. "
                "이 기능을 사용하려면 'pip install langchain langchain-openai'를 실행하세요."
            )

        template = """You are a helpful AI bot that answers questions for a user. Keep your response short and direct" \n
        \n ------- \n 
        {context} 
        \n ------- \n
        Here is the user question: \n --- --- --- \n {question} \n Don't give information outside the document or repeat your findings."""
        
        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"],
        )
        # Create a LangChain runnable
        model = ChatOpenAI(temperature=0, model=self.model_name)
        chain = ( {"context": lambda x: context,
                  "question": itemgetter("question")} 
                | prompt 
                | model 
                )
        return chain
    


