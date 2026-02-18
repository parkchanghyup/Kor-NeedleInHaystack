"""
Google Gemini 모델을 사용한 응답 evaluators
"""

import os
import re
from pathlib import Path

from google import genai
from google.genai import types

from .evaluator import Evaluator


class GeminiEvaluator(Evaluator):
    """
    Google Gemini 모델(google-genai)을 사용하여 LLM 응답을 평가하는 evaluatros입니다.

    Attributes:
        model_name (str): 평가에 사용할 Gemini 모델명
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
        model_name: str = "gemini-2.5-flash",
        model_kwargs: dict = None,
        true_answer: str = None,
        question_asked: str = None,
    ):
        """
        Gemini 모델을 사용한 평가자 초기화

        Args:
            model_name: 모델 이름 (기본값: gemini-2.5-flash)
            model_kwargs: 모델 설정 (기본값: {temperature: 0})
            true_answer: 질문에 대한 정답
            question_asked: 모델에게 한 질문
        """
        self.model_name = model_name
        self.model_kwargs = model_kwargs or self.DEFAULT_MODEL_KWARGS
        self.true_answer = true_answer
        self.question_asked = question_asked

        # GOOGLE_API_KEY
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY가 환경 변수에 설정되어야 합니다.")

        self.api_key = api_key

        # 새로운 google.genai API 사용
        self.client = genai.Client(api_key=api_key)

    def evaluate_response(self, response: str) -> int:
        """
        모델의 응답을 평가하여 점수를 반환합니다.

        Args:
            response: 평가할 모델의 응답

        Returns:
            int: 0~10 사이의 점수 (에러인 경우 0)
        """
        # true_answer와 question_asked 검증
        if not self.true_answer or not self.question_asked:
            raise ValueError("true_answer와 question_asked가 설정되어야 합니다.")

        # 에러 응답인 경우 0점 처리
        if response.startswith("Error:"):
            print(f"경고: 모델 응답이 에러입니다. 점수: 0")
            return 0

        # 평가 프롬프트 구성 (prompt.txt 템플릿 사용)
        template = self.CRITERIA["accuracy"]

        # 템플릿 변수 치환
        eval_prompt = template.format(
            input=self.question_asked, reference=self.true_answer, prediction=response
        )

        try:
            # 새로운 API 사용 (동기)
            result = self.client.models.generate_content(
                model=self.model_name,
                contents=eval_prompt,
                config=types.GenerateContentConfig(**self.model_kwargs)
                if self.model_kwargs
                else None,
            )
            score_text = result.text.strip()

            # 응답에서 숫자만 추출 (더 유연한 방식 사용)
            # 예: "점수는 10점입니다." -> 10 추출
            match = re.search(r"(\d+)", score_text)
            if match:
                score = int(match.group(1))
                # 1~10 범위로 보정 (Gemini가 8, 9점 등을 줄 수도 있으므로)
                return max(1, min(10, score))
            else:
                # 숫자를 찾지 못한 경우 기본값 5 반환
                print(f"경고: 점수를 파싱할 수 없습니다. 응답: {score_text}")
                return 5

        except Exception as e:
            print(f"평가 중 오류 발생: {str(e)}")
            return 5
