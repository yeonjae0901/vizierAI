# 🧠 Rule AI System 기술 아키텍처 문서

## 📋 개요

이 문서는 Rule AI System의 전체 아키텍처, 데이터 흐름, 소스 코드 구조 및 주요 함수에 대한 상세 설명을 제공합니다.

**문서 작성일**: 2024-05-20  
**최종 업데이트**: 2024-05-20  
**작성자**: 기술 문서 작성팀

## 🏗️ 시스템 아키텍처

### 전체 구조

```
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│                 │         │                 │         │                 │
│    Frontend     │ ◄─────► │    Backend      │ ◄─────► │    OpenAI API   │
│    (Vue.js)     │   HTTP  │    (FastAPI)    │   HTTP  │    (GPT Model)  │
│                 │         │                 │         │                 │
└─────────────────┘         └─────────────────┘         └─────────────────┘
```

### 백엔드 구조

```
├── app/
│   ├── api/                   # API 엔드포인트 정의
│   │   ├── __init__.py       # API 라우터 설정
│   │   ├── rule_generator.py # 룰 생성 API
│   │   ├── rule_validator.py # 룰 검증 API
│   │   └── rule_report.py    # 리포트 생성 API
│   │
│   ├── models/               # 데이터 모델 정의
│   │   ├── __init__.py
│   │   ├── rule.py           # 룰 관련 데이터 모델
│   │   ├── validation_result.py # 검증 결과 모델
│   │   └── report.py         # 리포트 관련 모델
│   │
│   ├── services/             # 비즈니스 로직 서비스
│   │   ├── __init__.py
│   │   ├── llm_service.py    # LLM API 통신 서비스
│   │   ├── rule_generator.py # 룰 생성 서비스
│   │   ├── rule_analyzer.py  # 룰 검증 서비스
│   │   ├── rule_parser.py    # 룰 파싱 서비스
│   │   └── rule_report_service.py # 리포트 생성 서비스
│   │
│   ├── config.py             # 환경 설정
│   └── main.py               # 애플리케이션 진입점
```

### 프론트엔드 구조

```
├── src/
│   ├── assets/              # 정적 파일 (이미지, 스타일)
│   ├── services/            # API 서비스
│   │   └── apiService.ts    # 백엔드 API 통신
│   │
│   ├── types/               # 타입 정의
│   │   └── rule.ts          # 룰 관련 인터페이스
│   │
│   ├── views/               # 화면 컴포넌트
│   │   ├── RuleEditor.vue   # 룰 생성 화면
│   │   └── ValidationReport.vue # 룰 검증 화면
│   │
│   ├── App.vue              # 메인 앱 컴포넌트
│   └── main.ts              # 앱 진입점
```

## 🌊 데이터 흐름

### 1. 룰 생성 흐름 (Rule Generation Flow)

```
┌─────────────┐     ┌───────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 사용자 입력  │────►│ RuleEditor.vue │────►│ apiService.ts   │────►│ rule_generator.py│
│ (자연어 설명) │     │ (프론트엔드)   │     │ (generateRule)  │     │ (API 엔드포인트) │
└─────────────┘     └───────────────┘     └─────────────────┘     └────────┬────────┘
                                                                           │
                                                                           ▼
┌─────────────┐     ┌───────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 화면에 표시  │◄────│ RuleEditor.vue │◄────│ apiService.ts   │◄────│ RuleGeneratorSvc│
│ (JSON 룰)   │     │ (프론트엔드)   │     │ (응답 처리)     │     │ (룰 생성 처리)  │
└─────────────┘     └───────────────┘     └─────────────────┘     └────────┬────────┘
                                                                           │
                                                                           ▼
                                                                  ┌─────────────────┐
                                                                  │   LLMService    │
                                                                  │ (OpenAI API 호출)│
                                                                  └─────────────────┘
```

1. 사용자가 RuleEditor에 자연어 설명과 추가 컨텍스트 입력
2. 프론트엔드의 apiService가 백엔드 API 호출
3. 백엔드 API(rule_generator.py)가 요청을 받아 RuleGeneratorService 호출
4. RuleGeneratorService가 프롬프트 생성 후 LLMService 통해 OpenAI API 호출
5. OpenAI가 생성한 룰을 파싱하고 검증
6. 검증된 룰과 설명을 응답으로 반환
7. 프론트엔드에서 결과 표시

### 2. 룰 검증 흐름 (Rule Validation Flow)

```
┌─────────────┐     ┌───────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 사용자 입력  │────►│ ValidationReport.vue │──►│ apiService.ts   │────►│ rule_validator.py│
│ (JSON 룰)   │     │ (프론트엔드)       │     │ (post 메서드)    │     │ (API 엔드포인트) │
└─────────────┘     └───────────────────┘     └─────────────────┘     └────────┬────────┘
                                                                               │
                                                                               ▼
┌─────────────┐     ┌───────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│ 화면에 표시  │◄────│ ValidationReport.vue │◄───│ apiService.ts   │◄────│ RuleAnalyzerSvc │
│ (검증 결과)  │     │ (프론트엔드)       │     │ (응답 처리)     │     │ (룰 검증 처리)  │
└─────────────┘     └───────────────────┘     └─────────────────┘     └─────────────────┘
```

1. 사용자가 ValidationReport 화면에 JSON 룰 입력
2. 프론트엔드에서 JSON이 파싱되고 요청 객체 생성
   - `rule_json` 필드가 있는 경우: 원본 요청 사용
   - `rule_json` 필드가 없는 경우: 입력 JSON을 `rule_json` 필드에 래핑
3. `apiService.post()` 메서드를 통해 `/api/v1/rules/validate-json` API 직접 호출
4. 백엔드 API가 요청을 받아 RuleAnalyzerService 호출
5. RuleAnalyzerService가 룰을 분석하여 검증 결과 생성
   - 중복 조건 검출
   - 잘못된 연산자 검출
   - 타입 불일치 검출
   - 자기 모순 검출
   - 구조 복잡도 평가
6. 응답 객체 생성
   - `is_valid`: 룰의 유효성 여부
   - `summary`: 검증 결과 요약
   - `issues`: 발견된 이슈 목록
   - `issue_counts`: 이슈 유형별 개수
   - `structure`: 룰 구조 정보 (깊이, 조건 수, 사용된 필드)
7. 프론트엔드에서 응답을 처리하여 결과 표시
   - 유효성 결과와 요약 표시
   - 룰 구조 정보 표시
   - 이슈 유형별 개수 표시
   - 필드별로 구분된 이슈 목록 표시

### 3. 룰 리포트 생성 흐름 (Rule Report Flow)

```
┌─────────────┐     ┌───────────────────┐     ┌─────────────────┐     ┌────────────────┐
│ 사용자 입력  │────►│ ValidationReport.vue │──►│ apiService.ts   │────►│ rule_report.py │
│ (JSON 룰)   │     │ (프론트엔드)       │     │ (generateReport)│     │ (API 엔드포인트)│
└─────────────┘     └───────────────────┘     └─────────────────┘     └────────┬───────┘
                                                                               │
                                                                               ▼
┌─────────────┐     ┌───────────────────┐     ┌─────────────────┐     ┌────────────────┐
│ 화면에 표시  │◄────│ ValidationReport.vue │◄───│ apiService.ts   │◄────│ RuleReportSvc  │
│ (마크다운 리포트)│  │ (프론트엔드)       │     │ (응답 처리)     │     │ (리포트 생성)  │
└─────────────┘     └───────────────────┘     └─────────────────┘     └────────┬───────┘
                                                                               │
                                                                               ▼
                                                                      ┌─────────────────┐
                                                                      │   LLMService    │
                                                                      │ (OpenAI API 호출)│
                                                                      └─────────────────┘
```

1. 사용자가 ValidationReport에서 검증 결과 확인 후 리포트 생성
2. 프론트엔드의 apiService가 백엔드 API 호출
3. 백엔드 API(rule_report.py)가 요청을 받아 RuleReportService 호출
4. RuleReportService가 프롬프트 생성 후 LLMService 통해 OpenAI API 호출
5. OpenAI가 생성한 마크다운 리포트를 응답으로 반환
6. 프론트엔드에서 마크다운을 HTML로 변환하여 표시

## 📁 주요 컴포넌트 상세 설명

### 백엔드 (Backend)

#### 1. LLMService (llm_service.py)
- **역할**: OpenAI API 통신 담당
- **주요 함수**:
  - `call_llm(prompt, system_message)`: LLM 모델에 요청을 보내고 응답을 반환
  - `generate_json(prompt, system_message)`: LLM 모델에 JSON 생성 요청을 보내고 파싱된 JSON 반환
- **오류 처리**: API 키 부재, API 호출 실패, JSON 파싱 실패에 대한 예외 처리
- **설정**: OpenAI API 키와 모델을 환경 변수 또는 설정 파일에서 로드

#### 2. RuleAnalyzerService (rule_analyzer.py)
- **역할**: 룰의 논리적 일관성과 구조적 문제 검증
- **주요 함수**:
  - `validate_rule(rule)`: 룰 객체 검증 및 결과 반환
  - `analyze_rule(rule_json)`: 룰 JSON 분석
  - `flatten_conditions(conditions_node)`: 조건 트리 평탄화
  - `detect_duplicate_conditions(conditions)`: 중복 조건 감지
  - `detect_invalid_operator(conditions)`: 잘못된 연산자 감지
  - `detect_type_mismatch(conditions)`: 타입 불일치 감지
  - `detect_self_contradiction(conditions)`: 자기 모순 감지
  - `evaluate_structure_complexity(conditions_node)`: 구조 복잡도 평가
  - `count_issues_by_type(issues)`: 이슈 유형별 개수 집계
  - `extract_unique_fields(conditions)`: 조건에서 사용된 고유 필드 추출
- **검증 프로세스**:
  1. 룰 객체를 JSON 형식으로 변환
  2. 조건 트리 평탄화
  3. 각종 검증 함수 실행
  4. 이슈 유형별 개수 집계
  5. 룰 구조 정보 생성 (깊이, 조건 수, 사용된 필드)
  6. 검증 결과 및 룰 요약 생성

#### 3. RuleGeneratorService (rule_generator.py)
- **역할**: 자연어 설명에서 구조화된 룰 생성
- **주요 함수**:
  - `generate_rule(request)`: 자연어 설명에서 룰 생성
  - `_prepare_prompt(description, additional_context)`: LLM용 프롬프트 생성
- **생성 프로세스**:
  1. 자연어 설명과 추가 컨텍스트로 프롬프트 생성
  2. LLMService를 통해 룰 JSON 생성
  3. 생성된 룰 파싱 및 검증
  4. 룰 생성 설명 요청
  5. 룰과 설명 반환

#### 4. RuleReportService (rule_report_service.py)
- **역할**: 룰 분석 리포트 생성
- **주요 함수**:
  - `generate_report(rule_json)`: 룰 분석 리포트 생성
  - `_create_report_prompt(rule_json)`: 리포트 생성용 프롬프트 작성
  - `_generate_fallback_report(rule_json)`: 오류 발생 시 대체 리포트 생성
- **리포트 프로세스**:
  1. 룰 JSON과 메타데이터 추출
  2. 분석 프롬프트 생성
  3. LLMService를 통해 마크다운 리포트 생성
  4. 리포트와 룰 메타데이터 반환

### 프론트엔드 (Frontend)

#### 1. apiService (apiService.ts)
- **역할**: 백엔드 API와의 통신 담당
- **주요 함수**:
  - `validateRuleJson(ruleJson)`: 룰 검증 API 호출
  - `generateRuleReport(request)`: 리포트 생성 API 호출
  - `generateRule(request)`: 룰 생성 API 호출
  - `post(url, data)`: 일반 POST 요청 함수
- **오류 처리**: HTTP 오류 처리 및 사용자 친화적인 오류 메시지 생성
- **인터셉터**: 요청/응답 로깅을 위한 axios 인터셉터 구현

#### 2. ValidationReport 컴포넌트 (ValidationReport.vue)
- **역할**: 룰 검증 화면 제공
- **주요 기능**:
  - JSON 입력 및 파싱
  - 룰 검증 요청 처리
  - 검증 결과 시각화
  - 리포트 생성 요청 처리
  - 마크다운 리포트 렌더링
- **주요 함수**:
  - `validateRule()`: 룰 검증 요청 처리
  - `generateReport()`: 리포트 생성 요청 처리
  - `getSeverityText()`: 심각도 텍스트 변환
  - `getIssueTypeText()`: 이슈 유형 텍스트 변환
  - `renderMarkdown()`: 마크다운 HTML 변환
- **상태 관리**:
  - `validationResult`: 검증 결과 상태
  - `reportResult`: 리포트 결과 상태
  - `error`: 오류 상태
  - `isLoading`: 로딩 상태

#### 3. RuleEditor (RuleEditor.vue)
- **역할**: 자연어 설명에서 룰 생성 화면 제공
- **상태 관리**:
  - `ruleDescription`: 자연어 설명
  - `additionalContext`: 추가 컨텍스트
  - `generatedRule`: 생성된 룰
  - `generatedExplanation`: 룰 생성 설명
- **주요 함수**:
  - `generateRule()`: 룰 생성 API 호출 및 결과 처리
  - `validateRule()`: 생성된 룰 검증 페이지로 이동

## 🔄 주요 API 엔드포인트

### 1. 룰 생성 API
- **URL**: `/api/v1/rules/generate`
- **Method**: POST
- **Handler**: `rule_generator.py`의 `generate_rule()`
- **요청 형식**: `RuleGenerationRequest`
  ```json
  {
    "description": "텍스트 설명",
    "additional_context": "추가 컨텍스트"
  }
  ```
- **응답 형식**: `RuleGenerationResponse`
  ```json
  {
    "rule": { Rule 객체 },
    "explanation": "생성 설명"
  }
  ```

### 2. 룰 검증 API
- **URL**: `/api/v1/rules/validate-json`
- **Method**: POST
- **Handler**: `rule_validator.py`의 `validate_rule_json()`
- **요청 형식**: `RuleJsonValidationRequest`
  ```json
  {
    "rule_json": { 룰 JSON 객체 }
  }
  ```
- **응답 형식**: `RuleValidationResponse`
  ```json
  {
    "validation_result": {
      "is_valid": true/false,
      "issues": [ { ValidationIssue 객체들 } ],
      "summary": "요약 메시지"
    },
    "rule_summary": "룰 설명"
  }
  ```

### 3. 룰 리포트 API
- **URL**: `/api/v1/rules/report`
- **Method**: POST
- **Handler**: `rule_report.py`의 `generate_rule_report()`
- **요청 형식**: `RuleReportRequest`
  ```json
  {
    "rule_json": { 룰 JSON 객체 },
    "include_markdown": true
  }
  ```
- **응답 형식**: `RuleReportResponse`
  ```json
  {
    "report": "마크다운 리포트",
    "rule_id": "룰 ID",
    "rule_name": "룰 이름"
  }
  ```

## 🛠️ 데이터 모델

### 백엔드 모델 (Pydantic)

#### 1. Rule 모델 (rule.py)
```python
class RuleCondition(BaseModel):
    field: str
    operator: str
    value: Any

class RuleAction(BaseModel):
    action_type: str
    parameters: Dict[str, Any]

class Rule(BaseModel):
    id: Optional[str]
    name: str
    description: str
    conditions: List[RuleCondition]
    actions: List[RuleAction]
    priority: int
    enabled: bool
```

#### 2. ValidationResult 모델 (validation_result.py)
```python
class ValidationIssue(BaseModel):
    message: str
    severity: str
    field: Optional[str]

class ValidationResult(BaseModel):
    is_valid: bool
    issues: List[ValidationIssue]
    summary: str
    duplicate_issues: List[str]
    invalid_operator_issues: List[str]
    type_mismatch_issues: List[str]
    contradiction_issues: List[str]
    structure_complexity: int
```

### 프론트엔드 모델 (TypeScript)

#### 1. Rule 인터페이스 (rule.ts)
```typescript
interface RuleCondition {
  field: string;
  operator: string;
  value: any;
}

interface RuleAction {
  action_type: string;
  parameters: Record<string, any>;
}

interface Rule {
  id?: string;
  name: string;
  description: string;
  conditions: RuleCondition[];
  actions: RuleAction[];
  priority: number;
  enabled: boolean;
}
```

#### 2. ValidationResult 인터페이스 (rule.ts)
```typescript
interface ValidationIssue {
  severity: 'error' | 'warning' | 'info';
  message: string;
  location?: string;
  suggestion?: string;
}

interface ValidationResult {
  is_valid: boolean;
  issues: ValidationIssue[];
  summary: string;
}
```

## 🔎 최적화 및 오류 처리

### 백엔드 최적화
1. **비동기 처리**: FastAPI의 비동기 처리를 활용하여 OpenAI API 호출 시 성능 최적화
2. **오류 처리**: LLM 호출, JSON 파싱, 검증 단계에서 오류 처리 및 상세 메시지 제공
3. **환경 변수**: API 키 및 설정을 환경 변수로 관리하여 보안 강화

### 프론트엔드 최적화
1. **응답 캐싱**: 동일 요청에 대한 불필요한 서버 호출 최소화
2. **국제화**: 영문 메시지를 한국어로 변환하는 함수 제공
3. **마크다운 렌더링**: 마크다운 텍스트를 HTML로 변환하여 가독성 향상
4. **JSON 검증**: 사용자 입력 JSON의 유효성 검증 및 중첩 구조 처리

## 📊 성능 고려사항

### 응답 시간
- LLM API 호출은 평균 2-5초의 지연 시간 발생
- OpenAI 서버 부하에 따라 지연 시간 변화 가능
- 타임아웃 설정으로 장시간 요청 방지

### 메모리 사용량
- 대용량 JSON 처리 시 메모리 오버헤드 발생 가능
- 복잡한 조건 트리 분석 시 재귀 호출 제한 고려

### API 요청 제한
- OpenAI API 요청 제한(rate limit) 고려
- 중요 요청 실패 시 재시도 로직 구현

## 📝 결론

Rule AI System은 자연어 설명에서 비즈니스 룰을 생성하고, 룰의 논리적 일관성을 검증하며, 상세 분석 리포트를 생성하는 AI 기반 시스템입니다. 백엔드(FastAPI, Python)와 프론트엔드(Vue.js, TypeScript)로 구성되어 있으며, OpenAI API를 활용하여 자연어 처리 기능을 제공합니다.

주요 기능:
1. 자연어 설명에서 구조화된 룰 생성
2. 룰의 논리적 일관성 검증
3. 룰에 대한 상세 분석 리포트 생성

이 시스템은 복잡한 비즈니스 규칙을 쉽게 생성하고 검증할 수 있게 하여 사용자의 업무 효율성을 높이고, 규칙 기반 시스템의 안정성을 향상시킵니다. 