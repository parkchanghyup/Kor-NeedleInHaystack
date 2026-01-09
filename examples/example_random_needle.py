"""
랜덤 needle 테스트 예시
이 스크립트는 5개의 needle 중 하나를 랜덤으로 선택하여 테스트하는 예시입니다.
needle과 retrieval_question을 지정하지 않으면 자동으로 랜덤 선택됩니다.
"""

from dotenv import load_dotenv

from core import LLMNeedleHaystackTesterKor
from providers import OpenAI
from evaluators import OpenAIEvaluator

# 환경 변수 로드
load_dotenv()

def main():
    # 테스트할 모델 설정
    model = OpenAI(model_name="gpt-4o-mini")
    
    # 평가에 사용할 모델 설정
    # needle과 retrieval_question을 None으로 두면 자동으로 랜덤 선택됩니다
    evaluator = OpenAIEvaluator(
        model_name="gpt-4o-mini",
        question_asked=None,  # 자동으로 설정됨
        true_answer=None      # 자동으로 설정됨
    )
    
    # 테스터 초기화 (needle과 retrieval_question을 지정하지 않음)
    tester = LLMNeedleHaystackTesterKor(
        model_to_test=model,
        evaluator=evaluator,
        # needle=None,  # 랜덤으로 선택됨
        # retrieval_question=None,  # 랜덤으로 선택됨
        haystack_dir="data/texts",
        results_version=1,
        context_lengths_min=1000,
        context_lengths_max=16000,
        context_lengths_num_intervals=5,
        document_depth_percent_min=0,
        document_depth_percent_max=100,
        document_depth_percent_intervals=5,
        document_depth_percent_interval_type="linear",
        num_concurrent_requests=1,
        save_results=True,
        save_contexts=True,
        final_context_length_buffer=200,
        seconds_to_sleep_between_completions=None,
        print_ongoing_status=True
    )
    
    # evaluator에 needle과 question 설정
    evaluator.question_asked = tester.retrieval_question
    evaluator.true_answer = tester.needle
    
    print("=" * 60)
    print("랜덤 Needle 테스트 시작")
    print("=" * 60)
    print(f"선택된 Needle: {tester.needle.strip()}")
    print(f"선택된 질문: {tester.retrieval_question}")
    print(f"모델: {model.model_name}")
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

