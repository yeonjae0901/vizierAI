from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import rule_generator, rule_validator

app = FastAPI(
    title="Rule AI System API",
    description="API for generating and validating rules using LLM",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 프로덕션에서는 특정 도메인으로 제한하세요
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 등록
app.include_router(rule_generator.router, prefix="/api/v1/rules", tags=["rules"])
app.include_router(rule_validator.router, prefix="/api/v1/rules", tags=["rules"])

@app.get("/")
async def root():
    return {"message": "Rule AI System API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 