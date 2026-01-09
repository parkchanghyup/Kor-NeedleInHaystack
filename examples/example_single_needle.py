"""
단일 needle 테스트 예시
이 스크립트는 단일 needle을 사용한 한국어 Needle In A Haystack 테스트의 예시입니다.
"""

from dotenv import load_dotenv

from core import LLMNeedleHaystackTesterKor
from providers import OpenAI
from evaluators import OpenAIEvaluator

# 환경 변수 로드
load_dotenv()

def main():
    # 테스트할 needle (찾아야 할 정보)
    needle = "\n서울에서 가장 좋은 일은 햇볕이 좋은 날 한강공원에서 치킨을 먹는 것입니다.\n"
    
    # 모델에게 할 질문
    retrieval_question = "서울에서 가장 좋은 일은 무엇인가요?"
    
    # 테스트할 모델 설정
    model = OpenAI(model_name="gpt-4o-mini")
    
    # 평가에 사용할 모델 설정
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
        haystack_dir="data/texts",  # 한국어 텍스트 파일이 있는 디렉토리
        retrieval_question=retrieval_question,
        results_version=1,
        context_lengths_min=1000,      # 최소 컨텍스트 길이
        context_lengths_max=16000,     # 최대 컨텍스트 길이
        context_lengths_num_intervals=5,  # 테스트할 간격 수 (빠른 테스트를 위해 5로 설정)
        document_depth_percent_min=0,
        document_depth_percent_max=100,
        document_depth_percent_intervals=5,  # 테스트할 깊이 간격 수 (빠른 테스트를 위해 5로 설정)
        document_depth_percent_interval_type="linear",
        num_concurrent_requests=1,
        save_results=True,
        save_contexts=True,
        final_context_length_buffer=200,
        seconds_to_sleep_between_completions=None,
        print_ongoing_status=True
    )
    
    print("=" * 60)
    print("단일 Needle 테스트 시작")
    print("=" * 60)
    print(f"Needle: {needle.strip()}")
    print(f"질문: {retrieval_question}")
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

