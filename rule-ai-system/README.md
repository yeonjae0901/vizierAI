# Rule AI System

자연어로 룰을 생성하고 검증하는 AI 시스템입니다.

## 기술 스택

- 백엔드: FastAPI (Python)
- 프론트엔드: Vue 3 (TypeScript)
- 환경관리: Docker + docker-compose

## 주요 기능

1. **룰 생성**: 자연어 설명을 JSON 형식의 룰로 변환
2. **룰 검증**: JSON 룰의 논리적 오류를 검증하고 자연어 요약 제공

## 시작하기

### 사전 요구사항

- Docker 및 docker-compose가 설치되어 있어야 합니다.
- OpenAI API 키 (환경 변수로 설정)

### 설치 및 실행

1. 저장소 클론

```bash
git clone https://github.com/yourusername/rule-ai-system.git
cd rule-ai-system
```

2. 환경 변수 설정

```bash
cp .env.example .env
# .env 파일을 편집하여 OPENAI_API_KEY를 설정하세요
```

3. Docker Compose로 실행

```bash
docker-compose up -d
```

4. 서비스에 접근

- 프론트엔드: http://localhost:3000
- 백엔드 API: http://localhost:8000

## API 엔드포인트

- `POST /api/v1/rules/generate`: 자연어 설명을 기반으로 룰 생성
- `POST /api/v1/rules/validate`: 기존 룰의 논리적 오류 검증

## 개발

### 백엔드 개발

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 프론트엔드 개발

```bash
cd frontend
npm install
npm run dev
```

## 라이센스

MIT 