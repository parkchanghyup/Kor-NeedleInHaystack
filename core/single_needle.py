"""
단일 Needle 테스트를 위한 핵심 모듈
"""

import asyncio
import glob
import json
import os
import time
import random
from typing import Optional, List, Union

import numpy as np

# 내부 evaluators와 providers 임포트
from evaluators import Evaluator
from providers import ModelProvider

from asyncio import Semaphore
from datetime import datetime, timezone


class LLMNeedleHaystackTesterKor:
    """
    한국어 버전의 LLM Needle In A Haystack 테스터입니다.
    
    긴 한국어 텍스트(Haystack) 내에 특정 정보(Needle)를 삽입하고,
    LLM이 해당 정보를 정확하게 찾아낼 수 있는지 테스트합니다.
    
    주요 기능:
        - 다양한 컨텍스트 길이에서 테스트
        - 다양한 문서 깊이(needle 삽입 위치)에서 테스트
        - 비동기 병렬 처리 지원
        - 결과 자동 저장 및 중단 후 재개 지원
    
    Attributes:
        needle (str): 찾아야 할 정보 (needle)
        haystack_dir (str): 배경 텍스트 파일이 있는 디렉토리
        retrieval_question (str): 모델에게 할 질문
        model_to_test (ModelProvider): 테스트할 LLM 프로바이더
        evaluation_model (Evaluator): 응답 평가자
        context_lengths (list): 테스트할 컨텍스트 길이 리스트
        document_depth_percents (list): 테스트할 문서 깊이 퍼센트 리스트
    """
    
    # 기본 needle 후보들과 해당 질문들
    DEFAULT_NEEDLES = [
        {
            "needle": "달빛을 연료로 움직이는 도시는 새벽이 되면 천천히 지면으로 가라앉는다.",
            "retrieval_question": "달빛을 연료로 움직이는 도시는 언제 지면으로 가라앉나요?"
        },
        {
            "needle": "유니콘을 만나기위해서는 파란색 말의 꿈을 꾸어야합니다.",
            "retrieval_question": "유니콘을 만나기 위해서는 어떤 꿈을 꾸어야 하나요?"
        },
        {
            "needle": "파손된 19번 지도는 북쪽이 아닌 '어제' 방향을 가리키고 있었다.",
            "retrieval_question": "파손된 19번 지도는 어느 방향을 가리키고 있었나요?"
        },
        {
            "needle": "세 번째 관찰일지에는 \"물이 소리를 내며 얼었다\"는 문장이 반복되어 있다.",
            "retrieval_question": "세 번째 관찰일지에 반복되어 있는 문장은 무엇인가요?"
        },
        {
            "needle": "맛있는 피자를 만들기 위한 비밀 재료는 시나몬 입니다.",
            "retrieval_question": "맛있는 피자를 만들기 위한 비밀 재료는 무엇인가요?"
        }
    ]
    
    @classmethod
    def load_needle_configs(cls) -> List[dict]:
        """
        JSON 파일에서 needle 설정을 로드합니다.
        파일이 없으면 DEFAULT_NEEDLES를 반환합니다.
        
        Returns:
            List[dict]: needle 설정 리스트
        """
        config_path = os.path.join(os.path.dirname(__file__), 'needle_configs.json')
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"needle_configs.json 로드 실패: {e}. 기본값을 사용합니다.")
        return cls.DEFAULT_NEEDLES
    
    def __init__(self,
                 model_to_test: Optional[ModelProvider] = None,
                 evaluator: Optional[Evaluator] = None,
                 evaluation_model: Optional[Evaluator] = None,
                 needle: Optional[str] = None,
                 haystack_dir: str = "data/texts",
                 retrieval_question: Optional[str] = None,
                 results_version: int = 1,
                 context_lengths_min: int = 1000,
                 context_lengths_max: int = 16000,
                 context_lengths_num_intervals: int = 35,
                 context_lengths: Optional[List[int]] = None,
                 document_depth_percent_min: int = 0,
                 document_depth_percent_max: int = 100,
                 document_depth_percent_intervals: int = 35,
                 document_depth_percents: Optional[List[int]] = None,
                 document_depth_percent_interval_type: str = "linear",
                 num_concurrent_requests: int = 1,
                 save_results: bool = True,
                 save_contexts: bool = True,
                 final_context_length_buffer: int = 200,
                 seconds_to_sleep_between_completions: Optional[float] = None,
                 print_ongoing_status: bool = True,
                 **kwargs):
        """
        한국어 버전 Needle Haystack Tester 초기화
        
        :model_to_test: 테스트할 모델. 기본값은 None.
        :evaluator: 모델 응답을 평가할 evaluator. 기본값은 None.
        :param needle: haystack에서 찾을 needle(바늘). 기본값은 None.
        :param haystack_dir: 배경 컨텍스트로 사용할 텍스트 파일 디렉토리. 기본값은 data/texts.
        :param retrieval_question: 모델에게 정보 검색을 요청할 질문.
        :param results_version: 같은 모델, 컨텍스트 길이, depth % 조합을 여러 번 시도하려면 버전을 변경하세요
        :param num_concurrent_requests: 동시 요청 수, 기본값 = 1. Rate limit에 주의하세요.
        :param save_results: 결과를 파일로 저장할지 여부. 기본값 = True
        :param save_contexts: 컨텍스트를 파일로 저장할지 여부. 경고: 매우 길어질 수 있습니다! 기본값은 True.
        :param final_context_length_buffer: 출력 컨텍스트를 위해 입력 컨텍스트에서 남겨둘 여유 공간. 기본값 200 토큰
        :param context_lengths_min: 컨텍스트의 최소 길이. 기본값은 1000.
        :param context_lengths_max: 컨텍스트의 최대 길이. 기본값은 16000.
        :param context_lengths_num_intervals: 컨텍스트 길이의 간격 수. 기본값은 35.
        :param context_lengths: 컨텍스트의 길이들. 기본값은 None.
        :param document_depth_percent_min: 문서의 최소 깊이 퍼센트. 기본값은 0.
        :param document_depth_percent_max: 문서의 최대 깊이 퍼센트. 기본값은 100.
        :param document_depth_percent_intervals: 문서 깊이 퍼센트의 간격 수. 기본값은 35.
        :param document_depth_percents: 문서의 깊이 퍼센트들. 기본값은 None.
        :param document_depth_percent_interval_type: 문서 깊이 퍼센트의 간격 타입. 'linear' 또는 'sigmoid' 중 하나여야 함. 기본값은 'linear'.
        :param seconds_to_sleep_between_completions: completion 사이에 대기할 초 수. 기본값은 None.
        :param print_ongoing_status: 진행 상태를 출력할지 여부. 기본값은 True.
        :param kwargs: 추가 인자들.
        """
        if not model_to_test:
            raise ValueError("테스트할 언어 모델이 제공되어야 합니다.")
        
        # needle과 retrieval_question이 제공되지 않은 경우 랜덤으로 선택
        if needle is None or retrieval_question is None:
            needle_configs = self.load_needle_configs()
            selected_needle_config = random.choice(needle_configs)
            if needle is None:
                needle = selected_needle_config["needle"]
            if retrieval_question is None:
                retrieval_question = selected_needle_config["retrieval_question"]
        
        if not needle or not haystack_dir or not retrieval_question:
            raise ValueError("Needle, haystack, retrieval_question이 제공되어야 합니다.")

        self.needle = needle
        self.haystack_dir = haystack_dir
        self.retrieval_question = retrieval_question
        self.results_version = results_version
        self.num_concurrent_requests = num_concurrent_requests
        self.save_results = save_results
        self.final_context_length_buffer = final_context_length_buffer
        self.save_contexts = save_contexts
        self.seconds_to_sleep_between_completions = seconds_to_sleep_between_completions
        self.print_ongoing_status = print_ongoing_status
        self.testing_results = []

        if context_lengths is None:
            if context_lengths_min is None or context_lengths_max is None or context_lengths_num_intervals is None:
                raise ValueError("context_lengths_min, context_lengths_max, context_lengths_intervals가 채워져야 하거나 context_lengths_list가 제공되어야 합니다.")
            else:
                self.context_lengths = np.round(np.linspace(context_lengths_min, context_lengths_max, num=context_lengths_num_intervals, endpoint=True)).astype(int)
        else:
            self.context_lengths = context_lengths

        if document_depth_percent_interval_type not in [None, "linear", "sigmoid"]:
            raise ValueError("document_depth_percent_interval_type은 None, 'linear' 또는 'sigmoid' 중 하나여야 합니다.")

        if document_depth_percents is None:
            if document_depth_percent_min is None or document_depth_percent_max is None or document_depth_percent_intervals is None:
                raise ValueError("document_depth_percent_min, document_depth_percent_max, document_depth_percent_intervals가 채워져야 하거나 document_depth_percents가 제공되어야 합니다.")
            
            if document_depth_percent_interval_type == 'linear':
                self.document_depth_percents = np.round(np.linspace(document_depth_percent_min, document_depth_percent_max, num=document_depth_percent_intervals, endpoint=True)).astype(int)
            elif document_depth_percent_interval_type == 'sigmoid':
                self.document_depth_percents = [self.logistic(x) for x in np.linspace(document_depth_percent_min, document_depth_percent_max, document_depth_percent_intervals)]
            else:
                raise ValueError("document_depth_percents가 None이면 document_depth_percent_interval_type은 'sigmoid' 또는 'linear'여야 합니다.")
        else:
            self.document_depth_percents = document_depth_percents
        
        self.model_to_test = model_to_test
        self.model_name = self.model_to_test.model_name
        
        self.evaluation_model = evaluation_model if evaluation_model is not None else evaluator

    def logistic(self, x: float, L: int = 100, x0: int = 50, k: float = .1) -> float:
        """로지스틱 함수를 사용하여 값을 변환합니다."""
        if x in [0, 100]:
            return x
        x = -k * (x - x0)
        return np.round(L * self.sigmoid(x), 3)
    
    def sigmoid(self, x: float) -> float:
        """시그모이드 함수를 계산합니다."""
        return 1 / (1 + np.exp(-x))
    
    async def bound_evaluate_and_log(self, sem, *args):
        async with sem:
            await self.evaluate_and_log(*args)

    async def run_test(self):
        sem = Semaphore(self.num_concurrent_requests)

        # 각 context_lengths와 depths의 반복을 실행
        tasks = []
        for context_length in self.context_lengths:
            for depth_percent in self.document_depth_percents:
                task = self.bound_evaluate_and_log(sem, context_length, depth_percent)
                tasks.append(task)

        # 모든 작업이 완료될 때까지 대기
        await asyncio.gather(*tasks)

    async def evaluate_and_log(self, context_length: int, depth_percent: float) -> None:
        # 이미 길이/퍼센트/버전을 확인했는지 체크
        # 프로그램이 중단되고 나중에 다시 시작하려는 경우에 도움이 됩니다
        if self.save_results:
            if self.result_exists(context_length, depth_percent):
                return

        # 필요한 길이의 컨텍스트를 생성하고 needle 문장을 배치
        context = await self.generate_context(context_length, depth_percent)

        # 평가할 모델에 보낼 메시지 준비
        prompt = self.model_to_test.generate_prompt(context, self.retrieval_question)

        test_start_time = time.time()

        # 모델이 랜덤 사실을 추출하는 질문에 답할 수 있는지 확인
        response = await self.model_to_test.evaluate_model(prompt)

        test_end_time = time.time()
        test_elapsed_time = test_end_time - test_start_time

        # 응답을 배치한 실제 needle과 비교
        score = self.evaluation_model.evaluate_response(response)

        results = {
            # 'context' : context, # 모델이 검색하도록 요청받은 컨텍스트를 저장하려면 이 줄의 주석을 해제하세요. 경고: 매우 커집니다.
            'model' : self.model_name,
            'context_length' : int(context_length),
            'depth_percent' : float(depth_percent),
            'version' : self.results_version,
            'needle' : self.needle,
            'model_response' : response,
            'score' : score,
            'test_duration_seconds' : test_elapsed_time,
            'test_timestamp_utc' : datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S%z')
        }

        self.testing_results.append(results)

        if self.print_ongoing_status:
            print (f"-- 테스트 요약 -- ")
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

    def result_exists(self, context_length: int, depth_percent: float) -> bool:
        """
        결과가 이미 평가되었는지 확인.
        파일명 패턴으로 빠르게 후보를 찾고, version만 파일 내부에서 검증합니다.
        
        Returns:
            bool: 결과가 존재하면 True, 아니면 False
        """
        results_dir = 'results_kor'
        if not os.path.exists(results_dir):
            return False
        
        safe_model_name = self.model_name.replace(".", "_").replace("/", "_").replace(":", "_")
        expected_filename = f'{safe_model_name}_len_{context_length}_depth_{int(depth_percent)}_results.json'
        filepath = os.path.join(results_dir, expected_filename)
        
        if not os.path.exists(filepath):
            return False
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                result = json.load(f)
                return result.get('version', 1) == self.results_version
        except (json.JSONDecodeError, KeyError):
            return False

    async def generate_context(self, context_length: int, depth_percent: float) -> str:
        """
        지정된 길이와 깊이의 컨텍스트를 생성합니다.
        
        Args:
            context_length: 토큰 단위의 컨텍스트 길이
            depth_percent: needle 삽입 깊이 (%)
            
        Returns:
            str: needle이 삽입된 컨텍스트
        """
        # haystack dir 파일들을 문자열로 로드
        context = self.read_context_files()

        # haystack dir 에세이를 원하는 컨텍스트 길이로 자르기
        context = self.encode_and_trim(context, context_length)

        # 깊이 퍼센트에 따라 랜덤 문장 삽입
        context = self.insert_needle(context, depth_percent, context_length)

        return context
    
    def insert_needle(self, context: str, depth_percent: float, context_length: int) -> str:
        """
        컨텍스트에 needle을 삽입합니다.
        
        Args:
            context: 원본 컨텍스트
            depth_percent: needle 삽입 깊이 (%)
            context_length: 토큰 단위의 컨텍스트 길이
            
        Returns:
            str: needle이 삽입된 컨텍스트
        """
        tokens_needle = self.model_to_test.encode_text_to_tokens(self.needle)
        tokens_context = self.model_to_test.encode_text_to_tokens(context)

        # 시스템 메시지, 사용자 질문 및 응답을 고려하여 컨텍스트 길이를 150 버퍼만큼 줄입니다.
        context_length -= self.final_context_length_buffer

        # 컨텍스트 + needle이 컨텍스트 길이보다 길면 needle 길이만큼 컨텍스트에서 토큰 제거
        if len(tokens_context) + len(tokens_needle) > context_length:
            tokens_context = tokens_context[:context_length - len(tokens_needle)]

        if depth_percent == 100:
            # 깊이 퍼센트가 100이면 (needle이 문서의 마지막 항목) 끝에 배치
            tokens_new_context = tokens_context + tokens_needle
        else:
            # needle을 삽입할 위치(토큰 기준) 가져오기
            insertion_point = int(len(tokens_context) * (depth_percent / 100))
            original_insertion_point = insertion_point

            # tokens_new_context는 needle 이전의 토큰을 나타냄
            tokens_new_context = tokens_context[:insertion_point]

            # needle을 문장 구분점에 배치하고 싶으므로 먼저 '.'가 어떤 토큰인지 확인
            period_tokens = self.model_to_test.encode_text_to_tokens('.')
            
            # 첫 번째 마침표를 찾을 때까지 역방향으로 반복
            # 마침표를 찾지 못하면 원래 삽입 지점을 사용
            while tokens_new_context and tokens_new_context[-1] not in period_tokens:
                insertion_point -= 1
                tokens_new_context = tokens_context[:insertion_point]

            if not tokens_new_context:
                insertion_point = original_insertion_point
                tokens_new_context = tokens_context[:insertion_point]

            tokens_new_context += tokens_needle + tokens_context[insertion_point:]

        # 문자열로 다시 변환하여 반환
        new_context = self.model_to_test.decode_tokens(tokens_new_context)
        return new_context

    def get_context_length_in_tokens(self, context: str) -> int:
        """컨텍스트의 토큰 길이를 반환합니다."""
        return len(self.model_to_test.encode_text_to_tokens(context))

    def read_context_files(self) -> str:
        """haystack 디렉토리에서 컨텍스트 파일들을 읽어옵니다."""
        context = ""
        max_context_length = max(self.context_lengths)
        # kor_version 패키지의 루트 디렉토리 찾기 (core의 부모)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        while self.get_context_length_in_tokens(context) < max_context_length:
            for file in sorted(glob.glob(os.path.join(base_dir, self.haystack_dir, "*.txt"))):
                with open(file, 'r', encoding='utf-8') as f:
                    context += f.read()
        return context

    def encode_and_trim(self, context: str, context_length: int) -> str:
        """
        컨텍스트를 인코딩하고 지정된 길이로 자릅니다.
        
        Args:
            context: 원본 컨텍스트
            context_length: 토큰 단위의 목표 길이
            
        Returns:
            str: 잘린 컨텍스트
        """
        tokens = self.model_to_test.encode_text_to_tokens(context)
        if len(tokens) > context_length:
            context = self.model_to_test.decode_tokens(tokens, context_length)
        return context
    
    def get_results(self) -> List[dict]:
        """테스트 결과를 반환합니다."""
        return self.testing_results
    
    def print_start_test_summary(self) -> None:
        """테스트 시작 요약을 출력합니다."""
        print ("\n")
        print ("Needle In A Haystack 테스팅 시작...")
        print (f"- 모델: {self.model_name}")
        print (f"- 컨텍스트 길이: {len(self.context_lengths)}개, 최소: {min(self.context_lengths)}, 최대: {max(self.context_lengths)}")
        print (f"- 문서 깊이: {len(self.document_depth_percents)}개, 최소: {min(self.document_depth_percents)}%, 최대: {max(self.document_depth_percents)}%")
        print (f"- Needle: {self.needle.strip()}")
        print ("\n\n")

    def start_test(self) -> None:
        """테스트를 시작합니다."""
        if self.print_ongoing_status:
            self.print_start_test_summary()
        asyncio.run(self.run_test())

