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
│   └── project_structure.md  # 프로젝트 구조 설명
├── requirements.txt       # 공통 Python 패키지 목록
├── rule-ai-system/        # rule-ai-system 프로젝트
│   ├── .env               # 환경변수 (Git에서 제외됨)
│   ├── .env.example       # 환경변수 예제 파일
│   ├── README.md          # 프로젝트 README
│   ├── backend/           # 백엔드 코드
│   │   ├── Dockerfile     # 백엔드 Docker 설정
│   │   ├── app/           # 백엔드 애플리케이션 코드
│   │   └── requirements.txt  # 백엔드 전용 의존성
│   ├── docker-compose.yml # Docker 구성 파일
│   ├── etc/               # 기타 설정 파일
│   └── frontend/          # 프론트엔드 코드
│       ├── Dockerfile     # 프론트엔드 Docker 설정
│       ├── env.d.ts       # TypeScript 환경 선언
│       ├── nginx.conf     # Nginx 설정
│       ├── package.json   # NPM 패키지 정보
│       ├── src/           # 소스 코드
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
- `backend/Dockerfile`: 백엔드 서비스 도커 이미지 설정

#### 프론트엔드

- `frontend/src/`: Vue.js 기반 프론트엔드 애플리케이션
- `frontend/Dockerfile`: 프론트엔드 서비스 도커 이미지 설정

## 환경 설정

각 프로젝트는 환경 변수 파일 (.env)을 통해 설정됩니다. 보안을 위해 .env 파일은 Git에 커밋되지 않으며, 개발자는 .env.example 파일을 참고하여 자신의 .env 파일을 생성해야 합니다.

## 배포

프로젝트는 Docker 및 docker-compose를 사용하여 배포할 수 있습니다. 자세한 배포 방법은 각 프로젝트의 README.md를 참조하세요. 