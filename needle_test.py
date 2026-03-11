"""
Needle In A Haystack 테스트 실행 스크립트

한국어 텍스트를 사용하여 LLM의 긴 컨텍스트 검색 능력을 테스트합니다.
다양한 컨텍스트 길이와 문서 깊이에서 모델이 특정 정보(needle)를 
얼마나 잘 찾아내는지 평가합니다.

사용법:
    # 기본 실행 (OpenAI)
    python needle_test.py
    
    # 특정 프로바이더 사용
    python needle_test.py --provider anthropic --model_name claude-3-5-sonnet-latest
    python needle_test.py --provider gemini --model_name gemini-2.5-flash
    python needle_test.py --provider openrouter --model_name google/gemma-3-27b-it
    python needle_test.py --provider vllm --model_name your-model-name
    
    # 다중 needle 테스트
    python needle_test.py --multi_needle true
    
    # 컨텍스트 길이 범위 설정
    python needle_test.py --context_lengths_min 1000 --context_lengths_max 32000
    
    # 결과 저장 위치: results_kor/, contexts_kor/
    # 결과 분석: python tools/analyze_results.py

지원 프로바이더:
    - openai: OpenAI GPT 모델
    - anthropic: Anthropic Claude 모델
    - gemini: Google Gemini 모델
    - openrouter: OpenRouter를 통한 다양한 모델
    - vllm: vLLM으로 서빙되는 로컬/원격 모델

지원 Evaluator:
    - openai: OpenAI 모델로 평가
    - gemini: Gemini 모델로 평가
"""

from dataclasses import dataclass, field
from typing import Optional, List

from dotenv import load_dotenv
from jsonargparse import CLI

from core import LLMNeedleHaystackTesterKor, LLMMultiNeedleHaystackTesterKor
from evaluators import Evaluator, OpenAIEvaluator
from providers import ModelProvider, OpenAI

# 선택적 import
try:
    from evaluators import GeminiEvaluator
except ImportError:
    GeminiEvaluator = None

try:
    from providers import Anthropic
except ImportError:
    Anthropic = None

try:
    from providers import Gemini
except ImportError:
    Gemini = None

try:
    from providers import OpenRouter
except ImportError:
    OpenRouter = None

try:
    from providers import VLLM
except ImportError:
    VLLM = None

load_dotenv()

@dataclass
class CommandArgs():
    """커맨드 라인 인자를 정의하는 데이터클래스"""
    provider: str = "openai"
    evaluator: str = "openai"
    model_name: str = "gpt-4o-mini"
    evaluator_model_name: Optional[str] = "gpt-4o-mini"
    needle: Optional[str] = None
    haystack_dir: Optional[str] = "data/texts"
    retrieval_question: Optional[str] = None
    results_version: Optional[int] = 1
    context_lengths_min: Optional[int] = 1000
    context_lengths_max: Optional[int] = 16000
    context_lengths_num_intervals: Optional[int] = 35
    context_lengths: Optional[List[int]] = None
    document_depth_percent_min: Optional[int] = 0
    document_depth_percent_max: Optional[int] = 100
    document_depth_percent_intervals: Optional[int] = 35
    document_depth_percents: Optional[List[int]] = None
    document_depth_percent_interval_type: Optional[str] = "linear"
    num_concurrent_requests: Optional[int] = 1
    save_results: Optional[bool] = True
    save_contexts: Optional[bool] = True
    final_context_length_buffer: Optional[int] = 200
    seconds_to_sleep_between_completions: Optional[float] = None
    print_ongoing_status: Optional[bool] = True
    # LangSmith 파라미터
    eval_set: Optional[str] = "multi-needle-eval-kor"
    # Multi-needle 파라미터
    multi_needle: Optional[bool] = False
    needles: List[str] = field(default_factory=lambda: [
        "완벽한 피자를 만들기 위해 필요한 비밀 재료 중 하나는 무화과입니다.",
        "완벽한 피자를 만들기 위해 필요한 비밀 재료 중 하나는 프로슈토입니다.",
        "완벽한 피자를 만들기 위해 필요한 비밀 재료 중 하나는 염소 치즈입니다."
    ])

def get_model_to_test(args: CommandArgs) -> ModelProvider:
    """
    제공된 커맨드 인자를 기반으로 적절한 모델 프로바이더를 결정하고 반환합니다.
    
    Args:
        args (CommandArgs): CommandArgs 데이터클래스 인스턴스로 파싱된 커맨드 라인 인자.
        
    Returns:
        ModelProvider: 지정된 모델 프로바이더 클래스의 인스턴스.
    
    Raises:
        ValueError: 지정된 프로바이더가 지원되지 않는 경우.
    """
    match args.provider.lower():
        case "openai":
            return OpenAI(model_name=args.model_name)
        case "anthropic":
            if Anthropic is None:
                raise ValueError("Anthropic 프로바이더를 사용하려면 'anthropic' 패키지를 설치해야 합니다.")
            return Anthropic(model_name=args.model_name)
        case "gemini":
            if Gemini is None:
                raise ValueError("Gemini 프로바이더를 사용하려면 'google-generativeai' 패키지를 설치해야 합니다.")
            return Gemini(model_name=args.model_name)
        case "openrouter":
            if OpenRouter is None:
                raise ValueError("OpenRouter 프로바이더를 사용하려면 'openai' 패키지를 설치해야 합니다.")
            return OpenRouter(model_name=args.model_name)
        case "vllm":
            if VLLM is None:
                raise ValueError("VLLM 프로바이더를 사용하려면 'openai' 및 'tiktoken' 패키지를 설치해야 합니다.")
            return VLLM(model_name=args.model_name)
        case _:
            raise ValueError(f"유효하지 않은 프로바이더: {args.provider}")

def get_evaluator(args: CommandArgs, needle=None, retrieval_question=None) -> Evaluator:
    """
    제공된 커맨드 인자를 기반으로 적절한 evaluator를 선택하고 반환합니다.
    
    Args:
        args (CommandArgs): CommandArgs 데이터클래스 인스턴스로 파싱된 커맨드 라인 인자.
        needle: 실제 사용될 needle (tester에서 결정된 값)
        retrieval_question: 실제 사용될 질문 (tester에서 결정된 값)
        
    Returns:
        Evaluator: 지정된 evaluator 클래스의 인스턴스.
        
    Raises:
        ValueError: 지정된 evaluator가 지원되지 않는 경우.
    """
    # Multi-needle 테스트인 경우 needles를 문자열로 결합
    if args.multi_needle and hasattr(args, 'needles'):
        true_answer = " ".join(args.needles)
    else:
        true_answer = needle if needle is not None else args.needle
    
    question = retrieval_question if retrieval_question is not None else args.retrieval_question
    
    match args.evaluator.lower():
        case "openai":
            return OpenAIEvaluator(model_name=args.evaluator_model_name,
                                   question_asked=question,
                                   true_answer=true_answer)
        case "gemini":
            if GeminiEvaluator is None:
                raise ValueError("Gemini evaluator를 사용하려면 'google-generativeai' 패키지를 설치해야 합니다.")
            return GeminiEvaluator(model_name=args.evaluator_model_name,
                                   question_asked=question,
                                   true_answer=true_answer)
        case _:
            raise ValueError(f"유효하지 않은 evaluator: {args.evaluator}")

def main():
    """
    커맨드 라인 인자를 기반으로 테스팅 프로세스를 실행하는 메인 함수.
    
    커맨드 라인 인자를 파싱하고, 적절한 모델 프로바이더와 evaluator를 선택하며,
    단일 needle 또는 다중 needle 시나리오에 대한 테스팅 프로세스를 시작합니다.
    """
    args = CLI(CommandArgs, as_positional=False)
    args.model_to_test = get_model_to_test(args)
    
    if args.multi_needle:
        print("다중 needle 테스팅")
        args.evaluation_model = get_evaluator(args)
        tester = LLMMultiNeedleHaystackTesterKor(**args.__dict__)
    else: 
        print("단일 needle 테스팅")
        args.evaluation_model = get_evaluator(args)
        tester = LLMNeedleHaystackTesterKor(**args.__dict__)
        # tester가 생성된 후 실제 needle과 question으로 evaluator의 값 업데이트
        tester.evaluation_model.true_answer = tester.needle
        tester.evaluation_model.question_asked = tester.retrieval_question
    
    tester.start_test()

if __name__ == "__main__":
    main()

