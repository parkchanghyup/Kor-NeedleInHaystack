from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import test_runner

app = FastAPI(
    title="Kor-NeedleInHaystack Web API",
    description="API for running and monitoring LLM Needle In A Haystack tests",
    version="1.0.0",
)

# CORS 설정 (프론트엔드 연동을 위해 모든 오리진 또는 특정 오리진 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 서비스 시 프론트엔드 도메인으로 제한 필요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(test_runner.router, prefix="/api/test", tags=["Test Runner"])

@app.get("/")
def root():
    return {"message": "Welcome to Kor-NeedleInHaystack Web API"}
