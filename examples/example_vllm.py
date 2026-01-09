"""
vLLM 프로바이더 사용 예시

사용 전 준비:
1. vLLM 설치:
   pip install vllm

2. vLLM 서버 시작:
   vllm serve google/gemma-2-9b-it --host 0.0.0.0 --port 8000
   
   또는 GPU 메모리가 부족한 경우:
   vllm serve google/gemma-2-9b-it --host 0.0.0.0 --port 8000 --gpu-memory-utilization 0.8

3. 환경 변수 설정:
   export VLLM_API_BASE="http://localhost:8000/v1"
   export VLLM_MODEL_NAME="google/gemma-2-9b-it"
"""

from dotenv import load_dotenv

from core import LLMNeedleHaystackTesterKor
from providers import VLLM
from evaluators import OpenAIEvaluator

# 환경 변수 로드
load_dotenv()

def main():
    # vLLM 프로바이더 초기화
    # 방법 1: 환경 변수 사용 (VLLM_API_BASE, VLLM_MODEL_NAME)
    model = VLLM(
        model_kwargs={
            "temperature": 0.0,
            "max_tokens": 300,
        }
    )
    
    # 방법 2: 직접 지정
    # model = VLLM(
    #     model_name="google/gemma-2-9b-it",
    #     api_base="http://localhost:8000/v1",
    #     model_kwargs={
    #         "temperature": 0.0,
    #         "max_tokens": 300,
    #     }
    # )
    
    # 테스트할 needle과 질문
    needle = "특별한 마법의 도시 이름은 '무지개성'입니다."
    retrieval_question = "특별한 마법의 도시 이름은 무엇인가요?"
    
    # 평가에 사용할 모델 설정 (OpenAI 사용)
    evaluator = OpenAIEvaluator(
        model_name="gpt-4o-mini",
        question_asked=retrieval_question,
        true_answer=needle
    )
    
    # 테스터 초기화
    tester = LLMNeedleHaystackTesterKor(
        model_to_test=model,
        evaluator=evaluator,
        needle=needle,
        haystack_dir="data/texts",
        retrieval_question=retrieval_question,
        results_version=1,
        context_lengths_min=1000,
        context_lengths_max=10000,
        context_lengths_num_intervals=3,
        document_depth_percent_min=0,
        document_depth_percent_max=100,
        document_depth_percent_intervals=3,
        num_concurrent_requests=1,
        save_results=True,
        save_contexts=True,
        final_context_length_buffer=200,
        print_ongoing_status=True
    )
    
    print("=" * 60)
    print("vLLM 프로바이더 테스트 시작")
    print("=" * 60)
    print(f"Needle: {needle}")
    print(f"질문: {retrieval_question}")
    print(f"모델: {model.model_name}")
    print(f"평가 모델: {evaluator.model_name}")
    print("=" * 60)
    
    # 테스트 실행
    tester.start_test()
    
    # 결과 가져오기
    results = tester.get_results()
    
    print("\n" + "=" * 60)
    print("테스트 완료!")
    print("=" * 60)
    print(f"총 테스트 수: {len(results)}")
    print(f"결과 저장 위치: results_kor/")
    print(f"컨텍스트 저장 위치: contexts_kor/")
    
    # 평균 점수 계산
    if results:
        avg_score = sum(r['score'] for r in results) / len(results)
        print(f"평균 점수: {avg_score:.2f}/10")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
