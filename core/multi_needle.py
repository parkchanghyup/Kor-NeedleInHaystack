"""
다중 Needle 테스트를 위한 핵심 모듈
"""

import asyncio
import json
import os
import time
from typing import List, Optional
from asyncio import Semaphore
from datetime import datetime, timezone

# 내부 evaluators와 providers 임포트
from evaluators import Evaluator
from providers import ModelProvider
from .single_needle import LLMNeedleHaystackTesterKor


class LLMMultiNeedleHaystackTesterKor(LLMNeedleHaystackTesterKor):
    """
    한국어 버전의 다중 Needle을 지원하는 LLM Haystack 테스터입니다.
    
    LLMNeedleHaystackTesterKor를 확장하여 하나의 haystack에서 
    여러 개의 needle을 동시에 테스트할 수 있습니다.
    각 needle은 문서의 서로 다른 위치에 균등하게 분산되어 삽입됩니다.
    
    주요 기능:
        - 여러 개의 needle을 컨텍스트 전체에 균등 분산
        - 각 needle의 삽입 위치 추적
        - 모든 needle을 정확히 찾았는지 평가
    
    Attributes:
        needles (List[str]): haystack에 삽입할 needle(사실)들의 리스트
        model_to_test (ModelProvider): 테스트할 LLM 프로바이더
        evaluator (Evaluator): 응답 평가자
        print_ongoing_status (bool): 진행 상태 메시지 출력 여부
        eval_set (str): 평가 세트 식별자
        insertion_percentages (List[float]): 각 needle의 실제 삽입 위치 (%)
    """
    def __init__(self, *args, 
                 needles: List[str] = None,
                 model_to_test: Optional[ModelProvider] = None,
                 evaluator: Optional[Evaluator] = None,
                 evaluation_model: Optional[Evaluator] = None,
                 print_ongoing_status: bool = True,
                 eval_set: str = "multi-needle-eval-kor",
                 **kwargs):

        # 다중 needle 테스트에서는 부모 클래스의 랜덤 needle 선택을 방지하기 위해
        # needles의 첫 번째 항목을 needle로 전달
        if needles and 'needle' not in kwargs:
            kwargs.setdefault('needle', needles[0])
        if needles and 'retrieval_question' not in kwargs:
            kwargs.setdefault('retrieval_question', f"다음 정보들을 모두 찾아주세요: {', '.join(needles)}")

        super().__init__(*args, model_to_test=model_to_test, evaluator=evaluator,
                         evaluation_model=evaluation_model, **kwargs)
        self.needles = needles if needles is not None else []
        self.eval_set = eval_set
        self.insertion_percentages: List[float] = []

    async def insert_needles(self, context: str, depth_percent: float, context_length: int) -> str:
        """
        원래 컨텍스트 문자열에 여러 개의 needle(특정 사실 또는 정보 조각)을 지정된 깊이 
        퍼센트에 삽입하여, 이러한 needle을 컨텍스트 전체에 효과적으로 분산시킵니다. 이 메서드는 
        needle의 배치 깊이에 따라 더 큰 텍스트 본문(haystack)에서 특정 정보(needle)를 검색하는 
        모델의 능력을 테스트하도록 설계되었습니다.

        메서드는 먼저 컨텍스트와 각 needle을 토큰으로 인코딩하여 토큰 단위의 길이를 계산합니다. 
        그런 다음 최종 버퍼 길이를 수용하도록 컨텍스트 길이를 조정합니다. 이는 총 토큰 수
        (컨텍스트 + needle)가 최대 허용 컨텍스트 길이를 초과하지 않도록 보장하는 데 중요하며, 
        그렇지 않으면 정보가 잘릴 수 있습니다.

        이 접근 방식은 첫 번째 needle의 초기 삽입 지점을 이전과 같이 계산하지만, 나머지 컨텍스트 
        길이를 기반으로 나머지 needle에 대한 균등한 간격을 계산합니다. 첫 번째 삽입 후 needle이 
        컨텍스트 전체에 가능한 한 균등하게 분산되도록 보장합니다.
        
        Args:
            context: 원래 컨텍스트 문자열
            depth_percent: needle을 삽입할 깊이 퍼센트
            context_length: 최종 버퍼로 조정된 토큰 단위의 총 컨텍스트 길이
        
        Returns:
            str: needle이 삽입된 새 컨텍스트
        """
        tokens_context = self.model_to_test.encode_text_to_tokens(context)
        context_length -= self.final_context_length_buffer

        # 모든 needle의 총 길이를 토큰으로 계산
        total_needles_length = sum(len(self.model_to_test.encode_text_to_tokens(needle)) for needle in self.needles)

        # 컨텍스트 길이가 needle을 고려하도록 보장
        if len(tokens_context) + total_needles_length > context_length:
            tokens_context = tokens_context[:context_length - total_needles_length]
        
        # needle을 균등하게 분산시키기 위해 삽입해야 하는 간격을 계산합니다.
        depth_percent_interval = (100 - depth_percent) / len(self.needles)
        
        # 현재 컨텍스트에 대한 삽입 퍼센트 리스트 재설정
        self.insertion_percentages = []

        # 계산된 지점에 needle 삽입
        for needle in self.needles:

            tokens_needle = self.model_to_test.encode_text_to_tokens(needle)

            if depth_percent == 100:
                # 깊이 퍼센트가 100이면 (needle이 문서의 마지막 항목) 끝에 배치
                tokens_context = tokens_context + tokens_needle
            else:
                # needle을 삽입할 위치(토큰 기준) 가져오기
                insertion_point = int(len(tokens_context) * (depth_percent / 100))
                original_insertion_point = insertion_point

                # tokens_new_context는 needle 이전의 토큰을 나타냄
                tokens_new_context = tokens_context[:insertion_point]

                # needle을 문장 구분점에 배치하고 싶으므로 먼저 '.'가 어떤 토큰인지 확인
                period_tokens = self.model_to_test.encode_text_to_tokens('.')
                
                # 첫 번째 마침표를 찾을 때까지 역방향으로 반복
                while tokens_new_context and tokens_new_context[-1] not in period_tokens:
                    insertion_point -= 1
                    tokens_new_context = tokens_context[:insertion_point]
                
                # 마침표를 찾지 못하면 원래 삽입 지점을 사용
                if not tokens_new_context:
                    insertion_point = original_insertion_point

                tokens_context = tokens_context[:insertion_point] + tokens_needle + tokens_context[insertion_point:]

                # 로그 
                insertion_percentage = (insertion_point / len(tokens_context)) * 100
                self.insertion_percentages.append(insertion_percentage)
                if self.print_ongoing_status:
                    print(f"'{needle}' 삽입 위치: 컨텍스트의 {insertion_percentage:.2f}%, 현재 총 길이: {len(tokens_context)} 토큰")
                
                # 다음 needle을 위해 깊이 조정
                depth_percent += depth_percent_interval  

        new_context = self.model_to_test.decode_tokens(tokens_context)
        return new_context

    def encode_and_trim(self, context: str, context_length: int) -> str:
        """
        컨텍스트를 토큰으로 인코딩하고 지정된 길이로 자릅니다.
        
        Args:
            context: 인코딩하고 자를 컨텍스트
            context_length: 토큰 단위의 원하는 컨텍스트 길이
        
        Returns:
            str: 인코딩되고 자른 컨텍스트
        """
        tokens = self.model_to_test.encode_text_to_tokens(context)
        if len(tokens) > context_length:
            context = self.model_to_test.decode_tokens(tokens, context_length)
        return context

    async def generate_context(self, context_length: int, depth_percent: float) -> str:
        """
        지정된 길이의 컨텍스트를 생성하고 주어진 깊이 퍼센트에 needle을 삽입합니다.
        
        Args:
            context_length: 토큰 단위의 총 컨텍스트 길이
            depth_percent: needle 삽입을 위한 깊이 퍼센트
        
        Returns:
            str: needle이 삽입된 컨텍스트
        """
        context = self.read_context_files()
        context = self.encode_and_trim(context, context_length)
        context = await self.insert_needles(context, depth_percent, context_length)
        return context
    
    async def evaluate_and_log(self, context_length: int, depth_percent: float) -> None:
        """
        생성된 컨텍스트로 모델의 성능을 평가하고 결과를 로그합니다.
        
        Args:
            context_length: 토큰 단위의 컨텍스트 길이
            depth_percent: needle 삽입을 위한 깊이 퍼센트
        """
        if self.print_ongoing_status:
            print(f"\n=== 평가 시작: 길이={context_length}, 깊이={depth_percent}% ===")
        
        if self.save_results:
            if self.result_exists(context_length, depth_percent):
                if self.print_ongoing_status:
                    print("결과가 이미 존재합니다. 건너뜁니다.")
                return

        self.notify_progress(
            "running",
            context_length=context_length,
            depth_percent=depth_percent,
            message=f"{self.completed_tests + 1}/{self.total_tests} 테스트 실행 중"
        )

        # 필요한 길이의 컨텍스트를 생성하고 needle 문장 배치
        context = await self.generate_context(context_length, depth_percent)

        test_start_time = time.time()

        # 평가할 모델에 보낼 메시지 준비
        prompt = self.model_to_test.generate_prompt(context, self.retrieval_question)
        
        # 모델이 랜덤 사실을 추출하는 질문에 답할 수 있는지 확인
        response = await self.model_to_test.evaluate_model(prompt)
        
        is_model_error = isinstance(response, str) and response.startswith("Error:")
        error_message = response[len("Error:"):].strip() if is_model_error else None

        # 응답을 배치한 실제 needle과 비교
        score = self.evaluation_model.evaluate_response(response)

        test_end_time = time.time()
        test_elapsed_time = test_end_time - test_start_time

        results = {
            # 'context' : context, # 모델이 검색하도록 요청받은 컨텍스트를 저장하려면 이 줄의 주석을 해제하세요. 경고: 매우 커집니다.
            'model' : self.model_to_test.model_name,
            'context_length' : int(context_length),
            'depth_percent' : float(depth_percent),
            'version' : self.results_version,
            'needles' : self.needles,  # multi_needle에서는 복수형 사용
            'needles_insertion_positions' : self.insertion_percentages,  # needle 삽입 위치 추가
            'model_response' : response,
            'is_model_error' : is_model_error,
            'error_message' : error_message,
            'score' : score,
            'test_duration_seconds' : test_elapsed_time,
            'test_timestamp_utc' : datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S%z')
        }

        self.testing_results.append(results)
        self.completed_tests += 1
        self.notify_progress(
            "running",
            context_length=context_length,
            depth_percent=depth_percent,
            message=f"{self.completed_tests}/{self.total_tests} 테스트 완료"
        )

        if self.print_ongoing_status:
            print ("-- 테스트 요약 -- ")
            print (f"소요 시간: {test_elapsed_time:.1f}초")
            print (f"컨텍스트: {context_length} 토큰")
            print (f"깊이: {depth_percent}%")
            print (f"점수: {score}")
            print (f"응답: {response}\n")

        # 파일 이름에 사용할 수 없는 문자 제거 (/, :, 등)
        safe_model_name = self.model_name.replace(".", "_").replace("/", "_").replace(":", "_")
        context_file_location = f'{safe_model_name}_len_{context_length}_depth_{int(depth_percent)}'

        if self.save_contexts:
            results['file_name'] = context_file_location

            os.makedirs('contexts_kor', exist_ok=True)

            with open(f'contexts_kor/{context_file_location}_context.txt', 'w', encoding='utf-8') as f:
                f.write(context)
            
        if self.save_results:
            os.makedirs('results_kor', exist_ok=True)

            with open(f'results_kor/{context_file_location}_results.json', 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)

        if self.seconds_to_sleep_between_completions:
            await asyncio.sleep(self.seconds_to_sleep_between_completions)

    async def bound_evaluate_and_log(self, sem, *args):
            async with sem:
                await self.evaluate_and_log(*args)

    async def run_test(self):
        sem = Semaphore(self.num_concurrent_requests)
        self.notify_progress("preparing", message="다중 needle 테스트 조합을 준비하고 있습니다.")

        # 각 context_lengths와 depths의 반복을 실행
        tasks = []
        for context_length in self.context_lengths:
            for depth_percent in self.document_depth_percents:
                task = self.bound_evaluate_and_log(sem, context_length, depth_percent)
                tasks.append(task)

        # 모든 작업이 완료될 때까지 대기
        await asyncio.gather(*tasks)

    def print_start_test_summary(self) -> None:
        """테스트 시작 요약을 출력합니다."""
        print ("\n")
        print ("Needle In A Haystack 테스팅 시작...")
        print (f"- 모델: {self.model_name}")
        print (f"- 컨텍스트 길이: {len(self.context_lengths)}개, 최소: {min(self.context_lengths)}, 최대: {max(self.context_lengths)}")
        print (f"- 문서 깊이: {len(self.document_depth_percents)}개, 최소: {min(self.document_depth_percents)}%, 최대: {max(self.document_depth_percents)}%")
        print (f"- Needles: {self.needles}")
        print ("\n\n")

    def start_test(self) -> None:
        """테스트를 시작합니다."""
        if self.print_ongoing_status:
            self.print_start_test_summary()
        asyncio.run(self.run_test())

