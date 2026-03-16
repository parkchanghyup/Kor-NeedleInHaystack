import asyncio
import uuid
import time
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

# 기존 needle_test.py 코어 등 모듈 임포트
from core.single_needle import LLMNeedleHaystackTesterKor
from core.multi_needle import LLMMultiNeedleHaystackTesterKor
from evaluators import OpenAIEvaluator
from providers import OpenAI

# 선택적 임포트는 needle_test.py와 유사하게 처리
try:
    from evaluators import GeminiEvaluator
except ImportError:
    GeminiEvaluator = None

try:
    from evaluators import OpenRouterEvaluator
except ImportError:
    OpenRouterEvaluator = None

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

router = APIRouter()

# 전역 상태 저장소 (메모리) - 실제 프로덕션에선 Redis/DB 사용 권장
tasks_store: Dict[str, Dict[str, Any]] = {}

class TestRunRequest(BaseModel):
    provider: str = Field(default="openai")
    evaluator: str = Field(default="openai")
    model_name: str = Field(default="gpt-4o-mini")
    evaluator_model_name: Optional[str] = Field(default="gpt-4o-mini")
    multi_needle: bool = Field(default=False)
    
    context_lengths_min: int = Field(default=1000)
    context_lengths_max: int = Field(default=16000)
    context_lengths_num_intervals: int = Field(default=5)
    
    document_depth_percent_min: int = Field(default=0)
    document_depth_percent_max: int = Field(default=100)
    document_depth_percent_intervals: int = Field(default=5)

def get_model_provider(provider: str, model_name: str):
    provider = provider.lower()
    if provider == "openai":
        return OpenAI(model_name=model_name)
    elif provider == "anthropic" and Anthropic:
        return Anthropic(model_name=model_name)
    elif provider == "gemini" and Gemini:
        return Gemini(model_name=model_name)
    elif provider == "openrouter" and OpenRouter:
        return OpenRouter(model_name=model_name)
    elif provider == "vllm" and VLLM:
        return VLLM(model_name=model_name)
    raise ValueError(f"지원하지 않는 프로바이더 또는 설치되지 않은 모듈: {provider}")

def get_evaluator_instance(evaluator: str, model_name: str):
    evaluator = evaluator.lower()
    # 임시 true_answer/question 사용, Tester 내부에서 업데이트 됨
    if evaluator == "openai":
        return OpenAIEvaluator(model_name=model_name, question_asked="temp", true_answer="temp")
    elif evaluator == "gemini" and GeminiEvaluator:
        return GeminiEvaluator(model_name=model_name, question_asked="temp", true_answer="temp")
    elif evaluator == "openrouter" and OpenRouterEvaluator:
        return OpenRouterEvaluator(model_name=model_name, question_asked="temp", true_answer="temp")
    raise ValueError(f"지원하지 않는 Evaluator: {evaluator}")


async def run_tester_job(task_id: str, req: TestRunRequest):
    """백그라운드에서 실행될 실제 테스트 런 함수"""
    try:
        tasks_store[task_id]["status"] = "running"
        tasks_store[task_id]["message"] = "테스트 초기화 중..."

        model_to_test = get_model_provider(req.provider, req.model_name)
        evaluation_model = get_evaluator_instance(req.evaluator, req.evaluator_model_name)

        tester_kwargs = {
            "model_to_test": model_to_test,
            "evaluation_model": evaluation_model,
            "context_lengths_min": req.context_lengths_min,
            "context_lengths_max": req.context_lengths_max,
            "context_lengths_num_intervals": req.context_lengths_num_intervals,
            "document_depth_percent_min": req.document_depth_percent_min,
            "document_depth_percent_max": req.document_depth_percent_max,
            "document_depth_percent_intervals": req.document_depth_percent_intervals,
            "print_ongoing_status": False,
            "save_results": True,
            "save_contexts": False, # 웹 환경에서는 용량 고려하여 False 기본값
        }

        tasks_store[task_id]["message"] = "테스트 실행 중..."
        
        start_time = time.time()
        
        if req.multi_needle:
            tester = LLMMultiNeedleHaystackTesterKor(**tester_kwargs)
        else:
            tester = LLMNeedleHaystackTesterKor(**tester_kwargs)
            tester.evaluation_model.true_answer = tester.needle
            tester.evaluation_model.question_asked = tester.retrieval_question
            
        # 백그라운드 테스트 실행 (비동기)
        await tester.run_test()
        
        elapsed = time.time() - start_time
        results = tester.get_results()
        
        tasks_store[task_id]["status"] = "completed"
        tasks_store[task_id]["message"] = "테스트가 완료되었습니다."
        tasks_store[task_id]["detailed_results"] = results
        tasks_store[task_id]["time_elapsed"] = elapsed

    except Exception as e:
        tasks_store[task_id]["status"] = "failed"
        tasks_store[task_id]["message"] = f"에러 발생: {str(e)}"
        print(f"Task Failed: {e}")

@router.post("/run")
async def run_test(req: TestRunRequest, background_tasks: BackgroundTasks):
    """
    새로운 Needle in a Haystack 테스트 런을 예약합니다.
    """
    task_id = str(uuid.uuid4())
    tasks_store[task_id] = {
        "status": "queued",
        "message": "작업 예약됨",
        "detailed_results": None,
        "time_elapsed": 0.0
    }
    
    background_tasks.add_task(run_tester_job, task_id, req)
    
    return {"task_id": task_id, "status": "queued"}

@router.get("/status/{task_id}")
async def get_test_status(task_id: str):
    """
    현재 태스크의 진행 상태를 반환합니다.
    """
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail="Task ID not found")
        
    task = tasks_store[task_id]
    return {
        "task_id": task_id,
        "status": task["status"],
        "message": task["message"],
    }

@router.get("/results/{task_id}")
async def get_test_results(task_id: str):
    """
    완료된 태스크의 전체 상세 결과를 반환합니다.
    """
    if task_id not in tasks_store:
        raise HTTPException(status_code=404, detail="Task ID not found")
        
    task = tasks_store.get(task_id)
    if task["status"] != "completed":
        return {"task_id": task_id, "status": task["status"], "detail": "Test not yet completed."}
        
    return {
        "task_id": task_id,
        "results": task.get("detailed_results", []),
        "time_elapsed": task.get("time_elapsed", 0)
    }
