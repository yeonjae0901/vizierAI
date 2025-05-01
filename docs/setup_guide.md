# vizierAI 프로젝트 설정 가이드

이 문서는 vizierAI 프로젝트와 그 하위 프로젝트를 설정하는 방법을 설명합니다.

## 요구사항

- Python 3.9 이상
- pip
- Git
- Node.js 18.0 이상 및 npm
- Docker 및 docker-compose (선택사항)

## 공통 가상환경 설정

1. 저장소 클론
```bash
git clone https://github.com/yeonjae0901/vizierAI.git
cd vizierAI
```

2. 가상환경 생성 및 활성화
```bash
python3 -m venv venv
source ./activate_env.sh
# 또는 직접 활성화
# source venv/bin/activate
```

3. 의존성 설치
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## 프로젝트별 설정

### rule-ai-system 프로젝트

1. 환경변수 설정
```bash
cd rule-ai-system
cp .env.example .env
```

2. .env 파일 편집
```bash
# 텍스트 에디터로 .env 파일 열고 필요한 값 설정
# 특히 OPENAI_API_KEY는 반드시 설정해야 합니다
nano .env
```

내용 예시:
```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxx
LOG_LEVEL=INFO
ENVIRONMENT=development
```

3. 백엔드 실행
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. 프론트엔드 실행
```bash
cd frontend
npm install  # 패키지 설치
npm run dev  # 개발 서버 실행
```

5. 웹 브라우저에서 접속
- 백엔드: http://localhost:8000/api/docs
- 프론트엔드: http://localhost:5173

## Docker를 이용한 실행

1. 환경변수 설정
```bash
cd rule-ai-system
cp .env.example .env
# .env 파일을 편집하여 필요한 환경변수 설정
```

2. Docker Compose 사용
```bash
cd rule-ai-system
docker-compose up -d  # 백그라운드에서 실행
```

3. 로그 확인
```bash
docker-compose logs -f  # 실시간 로그 확인
```

4. 서비스 접속
- 백엔드: http://localhost:8000/api/docs
- 프론트엔드: http://localhost:80

5. 중지
```bash
docker-compose down
```

## 개발 및 배포 가이드

### 개발 모드
```bash
# 백엔드 개발 모드 (자동 재시작)
cd rule-ai-system/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 프론트엔드 개발 모드 (핫 리로드)
cd rule-ai-system/frontend
npm run dev
```

### 프로덕션 빌드
```bash
# 프론트엔드 빌드
cd rule-ai-system/frontend
npm run build

# 백엔드 프로덕션 실행
cd rule-ai-system/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API 엔드포인트 테스트

### 룰 검증 API 테스트
```bash
# v1 API
curl -X POST http://localhost:8000/api/v1/rules/validate-json \
  -H "Content-Type: application/json" \
  -d '{"rule_json": {"ruleId": "R123", "name": "테스트 룰", "conditions": {"operator": "and", "conditions": [{"field": "SVC_CNT", "operator": ">=", "value": 3}]}}}'

# 레거시 API
curl -X POST http://localhost:8000/api/rules/validate-json \
  -H "Content-Type: application/json" \
  -d '{"rule_json": {"ruleId": "R123", "name": "테스트 룰", "conditions": {"operator": "and", "conditions": [{"field": "SVC_CNT", "operator": ">=", "value": 3}]}}}'
```

### 리포트 생성 API 테스트
```bash
curl -X POST http://localhost:8000/api/v1/rules/report \
  -H "Content-Type: application/json" \
  -d '{"rule_json": {"ruleId": "R123", "name": "테스트 룰", "conditions": {"operator": "and", "conditions": [{"field": "SVC_CNT", "operator": ">=", "value": 3}]}}, "include_markdown": true}'
```

## 문제 해결

### 의존성 설치 오류

pydantic_core 빌드 오류 발생 시:
```bash
# Rust 설치
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# 다시 설치 시도
pip install -r requirements.txt
```

### 환경변수 관련 오류

환경변수가 로드되지 않는 경우:
1. .env 파일이 올바른 위치에 있는지 확인
2. .env 파일의 형식이 올바른지 확인
3. python-dotenv 패키지가 설치되어 있는지 확인

### API 키 오류

OpenAI API 키 관련 오류:
1. 유효한 API 키인지 확인
2. 요금제 한도가 충분한지 확인
3. 네트워크 연결 상태 확인

### 프론트엔드 빌드 오류

TypeScript 또는 Vue 관련 오류:
1. Node.js 버전이 최소 요구사항을 충족하는지 확인
2. npm 패키지가 최신 상태인지 확인: `npm update`
3. 의존성 캐시를 삭제하고 다시 설치: `rm -rf node_modules && npm install`

### API 응답 오류

API 응답 오류가 발생하는 경우:
1. 서버 로그 확인: 백엔드 콘솔 출력 또는 `/var/log/rule-validator/app.log`
2. 요청 형식이 올바른지 확인: API 문서 참조
3. 서버 재시작 시도: `Ctrl+C`로 서버 중지 후 다시 실행 