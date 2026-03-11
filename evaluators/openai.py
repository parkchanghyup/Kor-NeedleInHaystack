"""
OpenAI 모델을 사용한 응답 평가자
"""

import os
import re
from pathlib import Path

from .evaluator import Evaluator

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


class OpenAIEvaluator(Evaluator):
    """
    OpenAI 모델을 사용하여 LLM 응답을 평가하는 평가자입니다.

    LangChain을 활용하여 응답의 정확성을 평가하고 점수를 부여합니다.

    Attributes:
        model_name (str): 평가에 사용할 OpenAI 모델 이름
        model_kwargs (dict): 모델 설정 (temperature 등)
        true_answer (str): 질문에 대한 정답
        question_asked (str): 모델에게 한 질문
    """

    DEFAULT_MODEL_KWARGS: dict = dict(temperature=0)

    # 평가 기준을 외부 파일에서 로드
    _criteria_cache = None

    @classmethod
    def _load_criteria(cls) -> str:
        """평가 기준을 prompt.txt 파일에서 로드"""
        if cls._criteria_cache is None:
            prompt_file = Path(__file__).parent / "prompt.txt"
            with open(prompt_file, "r", encoding="utf-8") as f:
                cls._criteria_cache = f.read().strip()
        return cls._criteria_cache

    @property
    def CRITERIA(self) -> dict[str, str]:
        """Evaluator 인터페이스 준수를 위한 dict 형식 반환"""
        return {"accuracy": self._load_criteria()}

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        model_kwargs: dict = None,
        true_answer: str = None,
        question_asked: str = None,
    ):
        """
        OpenAI 모델을 사용한 평가자 초기화

        Args:
            model_name: 모델 이름 (기본값: gpt-4o-mini)
            model_kwargs: 모델 설정 (기본값: {temperature: 0})
            true_answer: 질문에 대한 정답
            question_asked: 모델에게 한 질문
        """
        self.model_name = model_name
        self.model_kwargs = model_kwargs or self.DEFAULT_MODEL_KWARGS
        self.true_answer = true_answer
        self.question_asked = question_asked

        # OPENAI_API_KEY 지원
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 환경 변수에 설정되어야 합니다.")

        self.api_key = api_key

        self.evaluator = ChatOpenAI(
            model=self.model_name, openai_api_key=self.api_key, **self.model_kwargs
        )

    def evaluate_response(self, response: str) -> int:
        """
        모델의 응답을 평가하여 점수를 반환합니다.

        Args:
            response: 평가할 모델의 응답

        Returns:
            int: 1~10 사이의 점수 (에러인 경우 0)
        """
        # true_answer와 question_asked 검증
        if not self.true_answer or not self.question_asked:
            raise ValueError("true_answer와 question_asked가 설정되어야 합니다.")

        # 에러 응답인 경우 0점 처리
        if response.startswith("Error:"):
            print(f"경고: 모델 응답이 에러입니다. 점수: 0")
            return 0

        # 한국어 평가 프롬프트 로드
        eval_template = self.CRITERIA["accuracy"]

        prompt = PromptTemplate(
            template=eval_template, input_variables=["input", "reference", "prediction"]
        )

        chain = prompt | self.evaluator

        result = chain.invoke(
            {
                "input": self.question_asked,
                "reference": self.true_answer,
                "prediction": response,
            }
        )

        score_text = result.content.strip()
        numbers = re.findall(r"\b(1|3|5|7|10)\b", score_text)
        if numbers:
            return int(numbers[0])
        else:
            # 숫자를 찾지 못한 경우 기본값 5 반환
            print(f"경고: 점수를 파싱할 수 없습니다. 응답: {score_text}")
            return 5
