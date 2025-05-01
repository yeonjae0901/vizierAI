# vizierAI 프로젝트 구조

이 문서는 vizierAI 프로젝트의 전체 구조에 대한 설명입니다.

## 디렉토리 구조

```
vizierAI/
├── .git/                  # Git 저장소 정보
├── .gitignore             # Git 제외 파일 목록
├── README.md              # 메인 README 파일
├── activate_env.sh        # 가상환경 활성화 스크립트
├── docs/                  # 문서 디렉토리
│   ├── project_structure.md  # 프로젝트 구조 설명
│   ├── setup_guide.md     # 설정 가이드
│   └── rule-ai-system/    # 룰 AI 시스템 문서
│       ├── technical-architecture.md  # 기술 아키텍처 문서
│       └── user-manual.md  # 사용자 매뉴얼
├── requirements.txt       # 공통 Python 패키지 목록
├── rule-ai-system/        # rule-ai-system 프로젝트
│   ├── .env               # 환경변수 (Git에서 제외됨)
│   ├── .env.example       # 환경변수 예제 파일
│   ├── README.md          # 프로젝트 README
│   ├── backend/           # 백엔드 코드
│   │   ├── Dockerfile     # 백엔드 Docker 설정
│   │   ├── app/           # 백엔드 애플리케이션 코드
│   │   │   ├── api/       # API 엔드포인트
│   │   │   │   ├── __init__.py  # API 라우터 설정
│   │   │   │   ├── rule_validator.py  # 레거시 룰 검증 API
│   │   │   │   ├── rule_report.py  # 리포트 생성 API
│   │   │   │   └── v1/      # 버전화된 API
│   │   │   │       └── rule_validator.py  # v1 룰 검증 API
│   │   │   ├── models/    # 데이터 모델
│   │   │   │   ├── rule.py  # 룰 모델
│   │   │   │   ├── validation_result.py  # 검증 결과 모델 
│   │   │   │   ├── rule_json_validation_request.py  # JSON 검증 요청 모델
│   │   │   │   └── report.py  # 리포트 모델
│   │   │   ├── services/  # 비즈니스 로직 서비스
│   │   │   │   ├── rule_analyzer.py  # 룰 분석 서비스
│   │   │   │   ├── rule_report_service.py  # 리포트 생성 서비스
│   │   │   │   ├── llm_service.py  # LLM API 연동
│   │   │   │   ├── rule_parser.py  # 룰 파싱 유틸리티
│   │   │   │   ├── fixed_report_service.py  # 고정 리포트 서비스
│   │   │   │   └── test_report.py  # 리포트 테스트 유틸리티
│   │   │   ├── config.py  # 환경 설정
│   │   │   └── main.py    # 애플리케이션 진입점
│   │   └── requirements.txt  # 백엔드 전용 의존성
│   ├── docker-compose.yml # Docker 구성 파일
│   ├── etc/               # 기타 설정 파일
│   └── frontend/          # 프론트엔드 코드
│       ├── Dockerfile     # 프론트엔드 Docker 설정
│       ├── env.d.ts       # TypeScript 환경 선언
│       ├── nginx.conf     # Nginx 설정
│       ├── package.json   # NPM 패키지 정보
│       ├── src/           # 소스 코드
│       │   ├── assets/    # 정적 자원
│       │   ├── services/  # API 서비스
│       │   ├── types/     # 타입 정의
│       │   ├── views/     # 화면 컴포넌트
│       │   ├── App.vue    # 메인 앱 컴포넌트
│       │   └── main.ts    # 앱 진입점
│       ├── tsconfig.json  # TypeScript 설정
│       └── vite.config.ts # Vite 설정
└── venv/                  # Python 가상환경 (Git에서 제외됨)
```

## 주요 컴포넌트

### 공통 환경

- `activate_env.sh`: 모든 하위 프로젝트가 공유하는 가상환경을 활성화하는 스크립트
- `requirements.txt`: 모든 하위 프로젝트에서 사용하는 공통 Python 패키지 목록
- `venv/`: Python 가상환경 디렉토리 (Git에서 제외됨)

### rule-ai-system 프로젝트

rule-ai-system은 AI 기반 규칙 시스템을 구현한 프로젝트입니다.

#### 백엔드

- `backend/app/`: FastAPI 백엔드 애플리케이션
  - `api/`: API 엔드포인트 정의
    - `rule_validator.py`: 룰 유효성 검사(v1보다 이전 버전)
    - `rule_report.py`: 리포트 생성
    - `v1/rule_validator.py`: 버전화된 룰 유효성 검사
  - `models/`: 데이터 모델 정의 (rule.py, validation_result.py, report.py)
  - `services/`: 비즈니스 로직 구현 (llm_service.py, rule_analyzer.py, rule_report_service.py)
- `backend/Dockerfile`: 백엔드 서비스 도커 이미지 설정

#### 프론트엔드

- `frontend/src/`: Vue.js 기반 프론트엔드 애플리케이션
  - `views/`: 화면 컴포넌트 (ValidationReport.vue)
  - `services/`: API 호출 서비스 (apiService.ts)
  - `types/`: 타입 정의 (rule.ts)
- `frontend/Dockerfile`: 프론트엔드 서비스 도커 이미지 설정

## 주요 기능

### 룰 검증 기능
- 기존 룰의 논리적 오류 검증
- 이슈 목록 및 심각도 표시
- 개선 제안 제공
- 룰 구조 정보 및 이슈 요약 제공

### 리포트 생성 기능
- 룰에 대한 상세 분석 리포트 생성
- 마크다운 형식의 리포트 제공
- 조건 분석 및 개선 제안 포함

## 환경 설정

각 프로젝트는 환경 변수 파일 (.env)을 통해 설정됩니다. 보안을 위해 .env 파일은 Git에 커밋되지 않으며, 개발자는 .env.example 파일을 참고하여 자신의 .env 파일을 생성해야 합니다.

## 배포

프로젝트는 Docker 및 docker-compose를 사용하여 배포할 수 있습니다. 자세한 배포 방법은 각 프로젝트의 README.md를 참조하세요. 