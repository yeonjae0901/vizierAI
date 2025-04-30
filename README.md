# vizierAI 프로젝트 공통 가상환경

이 디렉토리는 vizierAI 하위의 모든 프로젝트(rule-ai-system 등)를 위한 공통 가상환경을 제공합니다.

## 문서 링크

- [프로젝트 구조](docs/project_structure.md): 프로젝트 전체 구조에 대한 설명
- [설정 가이드](docs/setup_guide.md): 프로젝트 설정 방법 안내
- [Rule AI System](docs/rule-ai-system/technical-architecture.md): 룰 AI 시스템 기술 아키텍처 문서
- [사용자 매뉴얼](docs/rule-ai-system/user-manual.md): 사용자 매뉴얼

## 최근 업데이트 내용

### 룰 검증 기능 개선 (2024-05)
- 룰 검증 화면 UI/UX 개선
- 검증 결과에 룰 구조 정보 및 이슈 요약 추가
- 이슈 표시 방식 개선 (필드별 구분, 이슈 타입 명시)
- API 호출 방식 개선 (/api/v1/rules/validate-json 직접 호출)

## 가상환경 설정

모든 하위 프로젝트는 이 디렉토리의 `venv` 가상환경을 공유하여 사용합니다.

### 가상환경 활성화

```bash
# vizierAI 디렉토리에서
source ./activate_env.sh

# 또는 직접 활성화
source ./venv/bin/activate
```

### 인터프리터 경로

IDE에서 Python 인터프리터를 설정할 때 다음 경로를 사용하세요:

```
/Users/roseline/projects/vizierAI/venv/bin/python
```

### 패키지 설치

모든 필요한 패키지는 `requirements.txt`에 정의되어 있습니다.

```bash
# 패키지 설치
pip install -r requirements.txt
```

### 프로젝트에서 가상환경 사용하기

각 하위 프로젝트에서는 상위 디렉토리의 가상환경을 사용할 수 있습니다:

```bash
# rule-ai-system 디렉토리에서 상위 가상환경 활성화
source ../venv/bin/activate
```

## 새로운 패키지 추가하기

새로운 패키지가 필요한 경우:

1. `requirements.txt`에 패키지와 버전을 추가합니다.
2. 가상환경을 활성화한 후 `pip install -r requirements.txt`를 실행합니다.

## 환경변수 설정

각 프로젝트는 `.env.example` 파일을 참고하여 자신의 `.env` 파일을 생성해야 합니다.

```bash
# .env.example 파일을 복사하여 .env 파일 생성
cp rule-ai-system/.env.example rule-ai-system/.env

# 텍스트 에디터로 .env 파일 열기
nano rule-ai-system/.env
```

> **중요**: `.env` 파일에는 API 키와 같은 민감한 정보가 포함될 수 있으므로 절대 Git에 커밋하지 마세요.

## GitHub에 푸시하기

이 프로젝트는 환경변수 파일(.env)을 제외한 파일들을 GitHub에 푸시합니다.

### GitHub에 푸시하기

```bash
# vizierAI 디렉토리로 이동
cd /Users/roseline/projects/vizierAI

# 변경사항 추가
git add .

# 커밋
git commit -m "변경사항 설명"

# 푸시
git push origin main
```

## 문제 해결

### 의존성 설치 오류

pydantic_core나 다른 패키지 설치 시 오류가 발생하는 경우:

```bash
# vizierAI 디렉토리로 반드시 이동
cd 경로/vizierAI

# requirements.txt 수정
# pydantic_core 버전 제약 제거
sed -i '' 's/pydantic_core==2.10.1//' requirements.txt
# pydantic 버전 업그레이드
sed -i '' 's/pydantic==2.4.2/pydantic>=2.5.0/' requirements.txt

# 필요시 Rust 설치 (pydantic_core 빌드에 필요)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
source "$HOME/.cargo/env"

# 가상환경 재생성
rm -rf venv
python3 -m venv venv
source venv/bin/activate

# 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt
```

### 명령 실행 위치 오류

모든 명령은 반드시 vizierAI 디렉토리 내에서 실행해야 합니다. 다음과 같은 오류가 발생하면 현재 위치를 확인하세요:

```
sed: requirements.txt: No such file or directory
bash: venv/bin/activate: No such file or directory
```

## 주의사항

- 모든 하위 프로젝트의 호환성을 위해 패키지 버전을 신중하게 관리해야 합니다.
- 특정 프로젝트에만 필요한 패키지가 있는 경우에도 `requirements.txt`에 추가해 주세요.
- 모든 명령은 반드시 vizierAI 디렉토리 내에서 실행해야 합니다.
- 민감한 정보가 포함된 `.env` 파일은 절대 Git에 커밋하지 마세요. 