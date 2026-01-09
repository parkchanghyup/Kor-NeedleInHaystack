"""
다중 needle 테스트 예시
이 스크립트는 여러 개의 needle을 사용한 한국어 Needle In A Haystack 테스트의 예시입니다.
"""

from dotenv import load_dotenv

from core import LLMMultiNeedleHaystackTesterKor
from providers import OpenAI
from evaluators import OpenAIEvaluator

# 환경 변수 로드
load_dotenv()

def main():
    # 테스트할 needles (찾아야 할 정보들)
    needles = [
        "완벽한 피자를 만들기 위해 필요한 비밀 재료 중 하나는 무화과입니다.",
        "완벽한 피자를 만들기 위해 필요한 비밀 재료 중 하나는 프로슈토입니다.",
        "완벽한 피자를 만들기 위해 필요한 비밀 재료 중 하나는 염소 치즈입니다."
    ]
    
    # 모델에게 할 질문
    retrieval_question = "완벽한 피자를 만들기 위한 비밀 재료는 무엇인가요?"
    
    # 첫 번째 needle을 true_answer로 사용 (또는 모든 needles를 조합할 수 있음)
    true_answer = "무화과, 프로슈토, 염소 치즈"
    
    # 테스트할 모델 설정
    model = OpenAI(model_name="gpt-4o-mini")
    
    # 평가에 사용할 모델 설정
    evaluator = OpenAIEvaluator(
        model_name="gpt-4o-mini",
        question_asked=retrieval_question,
        true_answer=true_answer
    )
    
    # 테스터 초기화
    tester = LLMMultiNeedleHaystackTesterKor(
        model_to_test=model,
        evaluator=evaluator,
        needles=needles,  # 다중 needles
        needle=needles[0],  # 첫 번째 needle을 기본값으로 (호환성을 위해)
        haystack_dir="data/texts",  # 한국어 텍스트 파일이 있는 디렉토리
        retrieval_question=retrieval_question,
        results_version=1,
        context_lengths_min=2000,      # 다중 needle이므로 더 긴 컨텍스트 사용
        context_lengths_max=20000,     
        context_lengths_num_intervals=4,  # 빠른 테스트를 위해 4로 설정
        document_depth_percent_min=0,
        document_depth_percent_max=100,
        document_depth_percent_intervals=4,  # 빠른 테스트를 위해 4로 설정
        document_depth_percent_interval_type="linear",
        num_concurrent_requests=1,
        save_results=True,
        save_contexts=True,
        final_context_length_buffer=200,
        seconds_to_sleep_between_completions=None,
        print_ongoing_status=True,
        eval_set="multi-needle-eval-kor"
    )
    
    print("=" * 60)
    print("다중 Needle 테스트 시작")
    print("=" * 60)
    print("Needles:")
    for i, needle in enumerate(needles, 1):
        print(f"  {i}. {needle.strip()}")
    print(f"\n질문: {retrieval_question}")
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

