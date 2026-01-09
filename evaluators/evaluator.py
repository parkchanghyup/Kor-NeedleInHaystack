"""
LLM 응답 평가를 위한 추상 기본 클래스
"""

from abc import ABC, abstractmethod


class Evaluator(ABC):
    """
    모든 평가자(Evaluator)가 구현해야 하는 추상 기본 클래스입니다.
    
    LLM의 응답을 평가하고 점수를 부여하는 역할을 합니다.
    
    Attributes:
        CRITERIA (dict[str, str]): 평가 기준을 담고 있는 딕셔너리
    """
    
    CRITERIA: dict[str, str]

    @abstractmethod
    def evaluate_response(self, response: str) -> int:
        """
        모델의 응답을 평가하여 점수를 반환합니다.
        
        Args:
            response (str): 평가할 모델의 응답
            
        Returns:
            int: 평가 점수 (일반적으로 1-10 사이)
        """
        ...






