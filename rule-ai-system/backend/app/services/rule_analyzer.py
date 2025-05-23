from typing import Dict, List, Any, Optional
from app.models.validation_result import ValidationResult, ConditionIssue, StructureInfo
from app.models.rule import Rule, RuleCondition

class RuleAnalyzer:
    """룰 분석 서비스"""
    
    def __init__(self):
        self.issues: List[ConditionIssue] = []
        self.field_types: Dict[str, str] = {}
        self.condition_map: Dict[str, List[Dict[str, Any]]] = {}
        # 글로벌 조건 인덱스 추적을 위한 변수
        self.global_condition_index = 0
        self.condition_index_map = {}  # 조건 객체 ID와 인덱스 매핑
        
        # 필드별 타입 스키마 정의 (실제 비즈니스 필드에 맞게 확장)
        self.field_schema = {
            # 숫자 타입 필드들
            "MBL_ACT_MEM_PCNT": {"type": "number", "description": "무선 회선 수", "allowed_operators": ["==", "!=", ">", "<", ">=", "<=", "in"]},
            "IOT_MEM_PCNT": {"type": "number", "description": "IoT 회선 수", "allowed_operators": ["==", "!=", ">", "<", ">=", "<=", "in"]},
            "age": {"type": "number", "description": "나이"},
            "score": {"type": "number", "description": "점수"},
            "price": {"type": "number", "description": "가격"},
            "amount": {"type": "number", "description": "금액"},
            "quantity": {"type": "number", "description": "수량"},
            
            # 문자열 타입 필드들
            "ENTR_STUS_CD": {"type": "string", "description": "가입 상태", "policy": {"sortable": False, "code_group": True}},
            "MRKT_CD": {"type": "string", "description": "마켓 코드", "policy": {"sortable": False, "code_group": False}, "allowed_operators": ["==", "!=", "in"]},
            "name": {"type": "string", "description": "이름"},
            "grade": {"type": "string", "description": "등급"},
            "category": {"type": "string", "description": "카테고리"},
            "membership": {"type": "string", "description": "멤버십"},
            "status": {"type": "string", "description": "상태"},
            
            # 배열 타입 필드들
            "tags": {"type": "array", "description": "태그 목록"},
            
            # 날짜 타입 필드들
            "date": {"type": "date", "description": "날짜"}
        }
        
        # 타입별 허용 연산자 (기본값)
        self._valid_operators = {
            "string": ["==", "!=", "contains", "starts_with", "ends_with"],
            "number": ["==", "!=", ">", "<", ">=", "<=", "in"],
            "boolean": ["==", "!="],
            "array": ["contains", "not_contains", "in", "not_in"],
            "date": ["==", "!=", ">", "<", ">=", "<="],
            "logical": ["and", "or"]  # 논리 연산자는 별도 타입으로 정의
        }
    
    async def analyze_rule(self, rule: Rule) -> ValidationResult:
        """룰을 분석하고 검증 결과를 반환"""
        try:
            print(f"룰 분석 시작: {rule.name}")
            self.issues = []
            self.global_condition_index = 0
            self.condition_index_map = {}
            contradiction_fields = set()  # 모순이 발견된 필드 추적
            
            # 전체 조건에 글로벌 인덱스 부여
            self._assign_global_indices(rule.conditions)
            
            # 기본 검증
            if not rule.conditions:
                self.issues.append(ConditionIssue(
                    field="conditions",
                    issue_type="missing_condition",
                    severity="error",
                    location="최상위 조건",
                    explanation="룰에 조건이 하나도 없습니다. 최소한 하나의 조건이 필요합니다.",
                    suggestion=self._generate_suggestion("missing_condition", "conditions")
                ))
                
            # 타입 불일치 사전 확인 - 전체 조건 순회
            try:
                # 모든 타입 불일치 이슈 수집
                type_mismatch_issues = self._precheck_type_mismatches(rule.conditions)
                
                # 타입 불일치 오류를 이슈 목록에 추가하고 계속 진행
                if type_mismatch_issues:
                    type_issues_count = len(type_mismatch_issues)
                    print(f"타입 불일치 오류가 {type_issues_count}개 발견되었지만, 다른 검사도 계속 진행합니다.")
                    self.issues.extend(type_mismatch_issues)
                
            except Exception as e:
                print(f"타입 검사 중 오류: {str(e)}")
                # 타입 검사 도중 예상치 못한 오류 발생 시 처리
                self.issues.append(ConditionIssue(
                    field=None,
                    issue_type="analysis_error",
                    severity="error",
                    location="조건 구조",
                    explanation=f"타입 검사 중 오류: {str(e)}",
                    suggestion="조건의 형식과 값을 확인하세요."
                ))
            
            # 조건 검증
            for idx, condition in enumerate(rule.conditions):
                try:
                    issues = await self._analyze_conditions(condition, index=idx+1, contradiction_fields=contradiction_fields)
                    self.issues.extend(issues)
                except Exception as e:
                    print(f"조건 {idx+1} 분석 중 오류: {str(e)}")
                    # 타입 비교 예외 특별 처리
                    if "not supported between instances of" in str(e):
                        error_parts = str(e).split("not supported between instances of")
                        if len(error_parts) > 1:
                            type_info = error_parts[1].strip()
                            self.issues.append(ConditionIssue(
                                field=getattr(condition, "field", None),
                                issue_type="type_mismatch",
                                severity="error",
                                location=f"조건 {idx+1}",
                                explanation=f"타입 불일치: {type_info} 간에 비교 연산이 불가능합니다. 타입을 일치시켜주세요.",
                                suggestion="조건에 사용된 값의 타입이 일치하는지 확인하세요. 숫자는 숫자끼리, 문자열은 문자열끼리 비교해야 합니다."
                            ))
                        else:
                            # 기타 예외는 기존 방식대로 처리
                            self.issues.append(ConditionIssue(
                                field=getattr(condition, "field", None),
                                issue_type="analysis_error",
                                severity="error",
                                location=f"조건 {idx+1}",
                                explanation=f"조건 분석 중 오류: {str(e)}",
                                suggestion="조건의 형식과 값을 확인하세요."
                            ))
                    else:
                        # 기타 예외는 기존 방식대로 처리
                        self.issues.append(ConditionIssue(
                            field=getattr(condition, "field", None),
                            issue_type="analysis_error",
                            severity="error",
                            location=f"조건 {idx+1}",
                            explanation=f"조건 분석 중 오류: {str(e)}",
                            suggestion="조건의 형식과 값을 확인하세요."
                        ))
                    continue
            
            # 모순 조건 검증 - 우선순위 높게 처리
            contradiction_issues, detected_contradiction_fields = self._check_contradictions(rule.conditions)
            self.issues.extend(contradiction_issues)
            contradiction_fields.update(detected_contradiction_fields)
            
            # 중복 조건 검증 (모순이 없는 필드에 대해서만)
            duplicate_issues = self._check_duplicate_conditions(rule.conditions, contradiction_fields)
            self.issues.extend(duplicate_issues)
            
            # 조건 누락 가능성 검사
            missing_issues = self._check_missing_conditions(rule.conditions)
            self.issues.extend(missing_issues)
            
            # 분기 불명확 검사 추가
            ambiguous_issues = self._check_ambiguous_branches(rule.conditions)
            self.issues.extend(ambiguous_issues)
            
            # 구조 복잡성 검사 - complexity_warning으로 이슈 타입 변경
            # 조건 중첩 깊이 ≥ 5, 또는 총 조건 수 ≥ 10일 경우
            depth = self._calculate_depth(rule.conditions)
            condition_count = self._count_conditions(rule.conditions)
            
            if depth >= 5 or condition_count >= 10:
                complexity_explanation = []
                if depth >= 5:
                    complexity_explanation.append(f"중첩 깊이({depth})가 5 이상입니다")
                if condition_count >= 10:
                    complexity_explanation.append(f"총 조건 수({condition_count})가 10개 이상입니다")
                
                explanation = ". ".join(complexity_explanation) + ". 룰의 복잡성이 높아질 수 있습니다."
                
                self.issues.append(ConditionIssue(
                    field=None,  # 필드를 NULL로 설정
                    issue_type="complexity_warning",
                    severity="warning",
                    location="전체 룰 구조",
                    explanation=explanation,
                    suggestion="룰 구조의 복잡성이 높습니다. 조건을 단순화하거나 여러 룰로 분리하세요."
                ))
            
            # 유효성 검사 - 오류 심각도 이슈가 있으면 유효하지 않음
            is_valid = len([i for i in self.issues if i.severity == "error"]) == 0
            
            # 7가지 이슈 타입 필터링 - 요구사항에 없는 이슈 타입은 제거
            allowed_issue_types = [
                "duplicate_condition", 
                "missing_condition", 
                "ambiguous_branch",
                "self_contradiction", 
                "invalid_operator", 
                "type_mismatch", 
                "complexity_warning"
            ]
            
            filtered_issues = [issue for issue in self.issues if issue.issue_type in allowed_issue_types]
            self.issues = filtered_issues
            
            # 이슈 타입별 건수 집계
            issue_counts = {}
            for issue in self.issues:
                if issue.issue_type not in issue_counts:
                    issue_counts[issue.issue_type] = 0
                issue_counts[issue.issue_type] += 1
            
            # 조건 구조 정보 계산
            unique_fields = self._extract_unique_fields(rule.conditions)
            
            # 룰 요약 생성
            try:
                rule_summary = self._generate_rule_summary(rule)
            except Exception as e:
                print(f"룰 요약 생성 중 오류: {str(e)}")
                rule_summary = "룰 요약을 생성할 수 없습니다."
            
            # 중복된 제안 최적화 (동일한 필드에 대해 동일한 제안이 있으면 통합)
            optimized_issues = self._optimize_issues(self.issues)
            
            # 이슈 정렬 - severity (error > warning) 우선, 그 다음 field 알파벳 순
            sorted_issues = sorted(
                optimized_issues, 
                key=lambda x: (
                    0 if x.severity == "error" else 1,  # error가 먼저 오도록
                    str(x.field) if x.field is not None else ""  # field가 None일 수 있으므로 문자열로 변환
                )
            )
            
            # 최적화 후 이슈 카운트 재계산 - 정합성 유지
            issue_counts = {}
            for issue in sorted_issues:
                if issue.issue_type not in issue_counts:
                    issue_counts[issue.issue_type] = 0
                issue_counts[issue.issue_type] += 1
            
            # 조건 관련 통계 계산
            condition_node_count = self._count_conditions(rule.conditions)
            field_condition_count = self._count_field_conditions(rule.conditions)
            
            # 총 이슈 건수
            total_issue_count = len(sorted_issues)
            
            # 요약은 정확한 수치로 생성 - 요구사항 양식에 맞춤
            summary = f"룰 '{rule.name}'에 총 {len(issue_counts)}가지 유형, {total_issue_count}건의 오류가 발견되었습니다."
            
            # 구조 정보 생성
            structure_info = StructureInfo(
                depth=depth,
                condition_count=condition_node_count,  # 이전 버전 호환성 유지
                condition_node_count=condition_node_count,
                field_condition_count=field_condition_count,
                unique_fields=unique_fields
            )
            
            # AI 코멘트 생성
            ai_comment = self._generate_ai_comment(rule, sorted_issues, structure_info)
            
            print(f"룰 분석 완료: {rule.name}, 이슈 개수: {total_issue_count}")
            
            return ValidationResult(
                is_valid=is_valid,
                summary=summary,
                issue_counts=issue_counts,
                issues=sorted_issues,
                structure=structure_info,
                rule_summary=rule_summary,
                complexity_score=self._calculate_complexity_score(rule.conditions),
                ai_comment=ai_comment
            )
        except Exception as e:
            print(f"룰 분석 중 치명적 오류: {str(e)}")
            # 분석 중 예외 발생 시 기본 결과 반환
            return ValidationResult(
                is_valid=False,
                summary=f"룰 '{rule.name}'에 총 1가지 유형, 1건의 오류가 발견되었습니다.",
                issue_counts={"missing_condition": 1},
                issues=[ConditionIssue(
                    field=None,
                    issue_type="missing_condition",
                    severity="error",
                    location="전체 룰",
                    explanation=f"룰 분석 중 오류: {str(e)}",
                    suggestion="룰의 형식과 조건을 확인하세요."
                )],
                structure=StructureInfo(
                    depth=1,
                    condition_count=len(rule.conditions),
                    condition_node_count=len(rule.conditions),
                    field_condition_count=0,
                    unique_fields=[]
                ),
                rule_summary="룰 분석 중 오류가 발생하여 요약을 생성할 수 없습니다.",
                complexity_score=0,
                ai_comment=None
            )
    
    def _infer_field_types(self, rule: Rule) -> None:
        """필드 타입 추론"""
        def process_conditions(conditions: List[RuleCondition]) -> None:
            for condition in conditions:
                # 필드가 있는 경우만 타입 추론 (논리 연산자 블록이 아닌 경우)
                if condition.field:
                    if condition.field in ["age", "score", "amount", "price", "quantity"]:
                        self.field_types[condition.field] = "number"
                    elif condition.value is not None:
                        if isinstance(condition.value, bool):
                            self.field_types[condition.field] = "boolean"
                        elif isinstance(condition.value, (int, float)):
                            self.field_types[condition.field] = "number"
                        elif isinstance(condition.value, list):
                            self.field_types[condition.field] = "array"
                        else:
                            self.field_types[condition.field] = "string"
                
                if condition.conditions:
                    process_conditions(condition.conditions)
        
        process_conditions(rule.conditions)
    
    async def _analyze_conditions(self, condition: RuleCondition, parent_field: Optional[str] = None, depth: int = 0, index: int = 0, contradiction_fields: set = None) -> List[ConditionIssue]:
        """조건 분석"""
        issues = []
        
        # contradiction_fields가 None이면 빈 세트로 초기화
        if contradiction_fields is None:
            contradiction_fields = set()

        # 연산자 검증
        location = f"조건 {self._get_condition_location(condition)}"
        if parent_field:
            location = f"{location} (필드: {parent_field})"
            
        # 논리 연산자 블록인지 확인
        is_logical_block = condition.field == "placeholder" or (condition.field is None and condition.conditions is not None)
        
        # 일반 필드 조건인 경우에만 필드 검증 수행
        if not is_logical_block and condition.field and condition.field != "placeholder":
            try:
                # 타입 검증을 먼저 수행 (중요: 연산자 검증보다 먼저)
                if not self._is_valid_type(condition.field, condition.value):
                    field_desc = ""
                    if condition.field in self.field_schema and "description" in self.field_schema[condition.field]:
                        field_desc = f" ({self.field_schema[condition.field]['description']})"
                        
                    field_type = self._get_field_type(condition.field)
                    field_type_desc = self._get_field_type_description(condition.field)
                    value_type = type(condition.value).__name__ if condition.value is not None else "None"
                    
                    issues.append(ConditionIssue(
                        field=condition.field,
                        issue_type="type_mismatch",
                        severity="error",
                        location=location,
                        explanation=f"{condition.field}{field_desc} 값 '{condition.value}'은(는) {value_type} 타입으로 지정되었지만, 이 필드는 {field_type_desc}이어야 합니다.",
                        suggestion=self._generate_suggestion("type_mismatch", condition.field, value=condition.value)
                    ))
                    # 타입이 유효하지 않으면 연산자 검증을 건너뛰고 다음 조건으로 넘어갑니다
                # 타입이 유효한 경우에만 연산자 검증
                elif not self._is_valid_operator(condition.field, condition.operator):
                    readable_operator = self._get_human_readable_operator(condition.operator)
                    field_desc = ""
                    if condition.field in self.field_schema and "description" in self.field_schema[condition.field]:
                        field_desc = f" ({self.field_schema[condition.field]['description']})"
                        
                    field_type = self._get_field_type_description(condition.field)
                    
                    # 정책 정보 추가
                    policy_info = ""
                    if condition.field in self.field_schema and "policy" in self.field_schema[condition.field]:
                        policy = self.field_schema[condition.field]["policy"]
                        if not policy.get("sortable", False) and condition.operator in [">", "<", ">=", "<="]:
                            policy_info = "이 필드는 문자열 타입이며, 정렬 비교가 허용되지 않습니다."
                        elif policy.get("code_group", False) and condition.operator in [">", "<", ">=", "<="]:
                            policy_info = "이 필드는 코드 그룹 필드로, 순서 비교가 의미가 없습니다."
                    
                    explanation = f"'{readable_operator}' 연산자는 {condition.field}{field_desc} 필드에 사용할 수 없습니다. 이 필드는 {field_type} 타입입니다."
                    if policy_info:
                        explanation += f" {policy_info}"
                    
                    issues.append(ConditionIssue(
                        field=condition.field,
                        issue_type="invalid_operator",
                        severity="error",
                        location=location,
                        explanation=explanation,
                        suggestion=self._generate_suggestion("invalid_operator", condition.field, condition.operator)
                    ))
            except Exception as e:
                print(f"필드 조건 분석 중 오류 ({location}): {str(e)}")
                issues.append(ConditionIssue(
                    field=condition.field,
                    issue_type="analysis_error",
                    severity="error",
                    location=location,
                    explanation=f"조건 분석 중 오류: {str(e)}",
                    suggestion="조건의 형식과 값을 확인하세요."
                ))
                
        # 논리 연산자 블록인 경우, 연산자의 유효성 검사
        elif is_logical_block:
            try:
                if condition.operator.lower() not in ["and", "or"]:
                    issues.append(ConditionIssue(
                        field=None,  # 필드는 None으로 설정 (논리 연산자 블록)
                        issue_type="invalid_structure",
                        severity="error",
                        location=location,
                        explanation=f"논리 연산자 블록에는 'AND' 또는 'OR' 연산자만 사용할 수 있습니다. 현재 '{condition.operator}'이(가) 사용되었습니다.",
                        suggestion="논리 연산자 블록에는 'AND' 또는 'OR'만 사용하세요."
                    ))
                    
                # 하위 조건이 없는 경우 경고
                if not condition.conditions or len(condition.conditions) == 0:
                    issues.append(ConditionIssue(
                        field=None,  # 필드는 None으로 설정 (논리 연산자 블록)
                        issue_type="invalid_structure",
                        severity="error",
                        location=location,
                        explanation=f"논리 연산자 블록에는 최소 하나 이상의 하위 조건이 필요합니다.",
                        suggestion="논리 연산자 블록에 하위 조건을 추가하세요."
                    ))
            except Exception as e:
                print(f"논리 연산자 블록 분석 중 오류 ({location}): {str(e)}")
                issues.append(ConditionIssue(
                    field=getattr(condition, "field", "unknown"),
                    issue_type="analysis_error",
                    severity="error",
                    location=location,
                    explanation=f"논리 연산자 블록 분석 중 오류: {str(e)}",
                    suggestion="논리 연산자 블록의 형식을 확인하세요."
                ))

        # 중복 조건 검증
        if condition.conditions:
            try:
                # 여기서는 중복 검증 제거 - analyze_rule에서 이미 처리함
                # duplicate_issues = self._check_duplicate_conditions(condition.conditions, contradiction_fields)
                # issues.extend(duplicate_issues)

                # 중첩 조건 분석
                for idx, nested_condition in enumerate(condition.conditions):
                    # 논리 연산자 블록인 경우 parent_field를 None으로 설정
                    nested_issues = await self._analyze_conditions(
                        nested_condition, 
                        parent_field=None if is_logical_block else condition.field, 
                        depth=depth + 1, 
                        index=idx + 1,
                        contradiction_fields=contradiction_fields
                    )
                    issues.extend(nested_issues)
            except Exception as e:
                print(f"중첩 조건 분석 중 오류 ({location}): {str(e)}")
                issues.append(ConditionIssue(
                    field=None,
                    issue_type="analysis_error",
                    severity="error",
                    location=location,
                    explanation=f"중첩 조건 분석 중 오류: {str(e)}",
                    suggestion="중첩 조건의 구조를 확인하세요."
                ))

        return issues
    
    def _is_valid_operator(self, field: str, operator: str) -> bool:
        """연산자 유효성 검사"""
        # 필드 타입 확인
        field_type = self._get_field_type(field)
        
        # 숫자 타입 필드의 경우 특별 처리 - 모든 비교 연산자 허용
        if field_type == "number" and operator in ["==", "!=", ">", "<", ">=", "<="]:
            return True
        
        # 문자열 타입 필드의 경우 연산자 제한 로직 추가
        if field_type == "string":
            # 문자열 필드에는 비교 연산자(>, <, >=, <=)를 절대 허용하지 않음
            invalid_operators_for_string = {">", ">=", "<", "<="}
            
            # 정책 설정에 관계없이 문자열 필드에 비교 연산자 사용 시 거부
            if operator in invalid_operators_for_string:
                return False
            
            # 필드별 스키마에서 허용된 연산자 목록 확인
            if field in self.field_schema and "allowed_operators" in self.field_schema[field]:
                return operator in self.field_schema[field]["allowed_operators"]
            
            # 기본 문자열 연산자 허용
            return operator in self._valid_operators["string"]
        
        # 필드별 스키마에서 허용된 연산자 목록 확인
        if field in self.field_schema and "allowed_operators" in self.field_schema[field]:
            return operator in self.field_schema[field]["allowed_operators"]
            
        # 스키마에 정의된 허용 연산자가 없으면 필드 타입에 따라 판단
        if field_type in self._valid_operators:
            return operator in self._valid_operators[field_type]
            
        # 기본값으로는 모든 필드에 ==, != 허용
        return operator in ["==", "!="]
    
    def _is_valid_type(self, field: str, value: Any) -> bool:
        """타입 일치 검사"""
        if value is None:
            return True

        field_type = self._get_field_type(field)
        
        if field_type == "number":
            # 더 엄격한 타입 체크: 오직 숫자 타입만 허용
            return isinstance(value, (int, float))
        elif field_type == "string":
            return isinstance(value, str)
        elif field_type == "boolean":
            # 문자열 "true", "false"도 허용
            if isinstance(value, str):
                return value.lower() in ["true", "false"]
            return isinstance(value, bool)
        elif field_type == "array":
            return isinstance(value, list)
        elif field_type == "date":
            # 날짜 형식의 문자열 체크
            if isinstance(value, str):
                try:
                    # 간단한 날짜 형식 체크 (더 정확한 체크는 추가 로직 필요)
                    parts = value.split("-")
                    return len(parts) == 3
                except:
                    return False
            return False
        else:  # 알 수 없는 타입은 모든 값 허용
            return True
    
    def _calculate_depth(self, conditions: List[RuleCondition], current_depth: int = 1) -> int:
        """조건 트리의 최대 깊이 계산 - 중첩 구조 정확히 반영"""
        if not conditions or len(conditions) == 0:
            return current_depth
            
        max_depth = current_depth
        for condition in conditions:
            if condition.conditions and len(condition.conditions) > 0:
                # 중첩된 조건 구조 발견 - 깊이 증가
                child_depth = self._calculate_depth(condition.conditions, current_depth + 1)
                max_depth = max(max_depth, child_depth)
                
        return max_depth
    
    def _check_duplicate_conditions(self, conditions: List[RuleCondition], contradiction_fields: set = None) -> List[ConditionIssue]:
        """중복 조건 검사"""
        if contradiction_fields is None:
            contradiction_fields = set()
        
        issues = []
        
        # 필드별로 조건을 그룹화
        self.condition_map = {}
        
        def map_conditions(condition_list, parent_path=""):
            for idx, condition in enumerate(condition_list):
                # 필드가 있는 경우만 중복 체크 
                # 논리 연산자 블록이 아닌 실제 필드 조건만 체크
                # placeholder 필드는 제외 (논리 연산자 블록을 표현하기 위해 사용)
                if condition.field and condition.field not in contradiction_fields and condition.field != "placeholder":
                    # 필드 인덱스 정보와 함께 조건 저장
                    condition_id = f"{parent_path}/{idx+1}" if parent_path else f"{idx+1}"
                    if condition.field not in self.condition_map:
                        self.condition_map[condition.field] = []
                    
                    # 조건 위치 정보 추가
                    global_index = self.condition_index_map.get(id(condition), 0)
                    condition_location = f"조건 {global_index}" if global_index else condition_id
                    
                    self.condition_map[condition.field].append({
                        "field": condition.field,
                        "operator": condition.operator,
                        "value": condition.value,
                        "index": idx + 1,
                        "parent_path": parent_path,
                        "condition_id": condition_id,
                        "location": condition_location,
                        "condition_obj": condition
                    })
                    
                # 중첩 조건이 있는 경우 재귀 처리
                if condition.conditions:
                    new_path = f"{parent_path}/{idx+1}" if parent_path else f"{idx+1}"
                    map_conditions(condition.conditions, new_path)
        
        # 조건 매핑 생성
        map_conditions(conditions)
        
        # 필드별로 중복 조건 검사
        for field, condition_list in self.condition_map.items():
            # 동일 필드에 대해 2개 이상 조건이 있는 경우만 체크
            if len(condition_list) >= 2 and field not in contradiction_fields:
                # 완전히 동일한 조건 찾기 (필드, 연산자, 값이 모두 동일)
                duplicate_groups = {}
                
                for i, condition1 in enumerate(condition_list):
                    field1 = condition1["field"]
                    op1 = condition1["operator"]
                    val1 = condition1["value"]
                    
                    # 정확한 비교를 위해 값을 문자열로 변환하지 않고 원본 타입 그대로 비교
                    # 완전히 동일한 조건 그룹핑을 위한 키 생성 (필드-연산자-값 조합)
                    # 타입까지 포함하여 정확히 비교하기 위해 타입 정보 추가
                    group_key = f"{field1}-{op1}-{val1}-{type(val1).__name__}"
                    
                    if group_key not in duplicate_groups:
                        duplicate_groups[group_key] = []
                    
                    duplicate_groups[group_key].append(condition1)
                
                # 각 그룹에서 중복 조건 확인 (완전히 동일한 조건만)
                for group_key, group_conditions in duplicate_groups.items():
                    if len(group_conditions) >= 2:
                        # 중복된 조건들의 위치 정보 수집
                        locations = []
                        for cond in group_conditions:
                            if "location" in cond and cond["location"]:
                                locations.append(cond["location"])
                            elif "condition_id" in cond:
                                locations.append(f"조건 {cond['condition_id']}")
                        
                        # 위치 정보를 쉼표로 구분하여 표준화
                        location_str = ", ".join(locations)
                        
                        # 각 중복 그룹당 1건의 이슈 생성
                        sample_condition = group_conditions[0]
                        issues.append(ConditionIssue(
                            field=field,
                            issue_type="duplicate_condition",
                            severity="warning",
                            location=location_str,  # 표준화된 위치 정보
                            explanation=f"동일한 조건이 여러 위치({location_str})에 중복 정의되어 있습니다: {field} {sample_condition['operator']} {sample_condition['value']}",
                            suggestion=self._generate_suggestion("duplicate_condition", field)
                        ))
        
        return issues
    
    def _calculate_complexity_score(self, conditions: List[RuleCondition]) -> int:
        """룰 조건 복잡도 점수 계산"""
        if not conditions:
            return 0
        
        # 깊이와 조건 수를 고려한 복잡도 점수
        depth = self._calculate_depth(conditions)
        condition_count = self._count_conditions(conditions)
        field_condition_count = self._count_field_conditions(conditions)
        unique_fields = len(self._extract_unique_fields(conditions))
        
        # 복잡도 계산 공식: 깊이 * 2 + 필드 조건 수 + 총 조건 수 * 0.5
        complexity = depth * 2 + field_condition_count + condition_count * 0.5
        
        # 필드 종류가 많을수록 더 복잡
        if unique_fields > 3:
            complexity += (unique_fields - 3) * 0.5
        
        return int(complexity)
    
    def _check_contradictions(self, conditions: List[RuleCondition]) -> tuple:
        """모순 조건 검사"""
        issues = []
        contradiction_fields = set()
        
        # 필드별로 조건을 그룹화
        field_conditions = {}
        
        def collect_field_conditions(condition_list, parent_path=""):
            for idx, condition in enumerate(condition_list):
                # 필드가 있는 경우만 모순 체크 (논리 연산자 블록이 아닌 경우)
                if condition.field:
                    # 필드 인덱스 정보와 함께 조건 저장
                    condition_id = f"{parent_path}/{idx+1}" if parent_path else f"{idx+1}"
                    if condition.field not in field_conditions:
                        field_conditions[condition.field] = []
                    
                    # 조건 위치 정보 추가
                    global_index = self.condition_index_map.get(id(condition), 0)
                    condition_location = f"조건 {global_index}" if global_index else condition_id
                    
                    field_conditions[condition.field].append({
                        "field": condition.field,
                        "operator": condition.operator,
                        "value": condition.value,
                        "index": idx + 1,
                        "parent_path": parent_path,
                        "condition_id": condition_id,
                        "location": condition_location,
                        "condition_obj": condition
                    })
                    
                # 중첩 조건이 있는 경우 재귀 처리
                if condition.conditions:
                    new_path = f"{parent_path}/{idx+1}" if parent_path else f"{idx+1}"
                    collect_field_conditions(condition.conditions, new_path)
        
        # 조건 수집
        collect_field_conditions(conditions)
        
        # 수집된 필드별로 모순 체크
        for field, field_condition_list in field_conditions.items():
            contradictions = []
            
            # 필드 내 조건이 2개 이상인 경우만 체크
            if len(field_condition_list) >= 2:
                for i, condition1 in enumerate(field_condition_list):
                    for j in range(i+1, len(field_condition_list)):
                        condition2 = field_condition_list[j]
                        is_contradiction = False
                        explanation = ""
                        
                        op1 = condition1["operator"]
                        val1 = condition1["value"]
                        op2 = condition2["operator"]
                        val2 = condition2["value"]
                        
                        # == 와 != 조건의 자기모순 케이스 먼저 확인 (우선순위 높임)
                        if (op1 == "==" and op2 == "!=" and str(val1) == str(val2)) or \
                           (op1 == "!=" and op2 == "==" and str(val1) == str(val2)):
                            is_contradiction = True
                            explanation = f"{field} 필드가 '{val1}'와 같고 같지 않아야 함"
                        elif isinstance(val1, str) and isinstance(val2, str):
                            # 문자열 동등 비교
                            if (op1 == "==" and op2 == "==" and val1 != val2):
                                is_contradiction = True
                                explanation = f"{field} 필드가 '{val1}'와 '{val2}' 두 값과 동시에 같을 수 없음"
                        elif isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                            # 숫자 범위 체크
                            if (op1 == ">" and op2 == "<=" and val1 <= val2) or \
                               (op1 == "<=" and op2 == ">" and val1 >= val2):
                                is_contradiction = True
                                explanation = f"{field} 필드가 {val1}보다 크고 {val2}보다 작거나 같을 수 없음"
                            elif (op1 == ">=" and op2 == "<" and val1 >= val2) or \
                                 (op1 == "<" and op2 == ">=" and val1 <= val2):
                                is_contradiction = True
                                explanation = f"{field} 필드가 {val1}보다 크거나 같고 {val2}보다 작을 수 없음"
                            # 같음/같지 않음 체크  
                            elif (op1 == "==" and op2 == "==" and val1 != val2):
                                is_contradiction = True
                                explanation = f"{field} 필드가 {val1}와 {val2} 두 값과 동시에 같을 수 없음"
                        elif (op1 == "==" and op2 == "=="):
                            # 서로 다른 타입의 값에 대한 == 연산자 사용 시 모순
                            is_contradiction = True
                            explanation = f"{field} 필드가 '{val1}'(타입: {type(val1).__name__})와 '{val2}'(타입: {type(val2).__name__}) 두 다른 타입의 값과 동시에 같을 수 없음"
                        
                        if is_contradiction:
                            # 조건 위치 정보 포맷
                            location1 = condition1["location"]
                            location2 = condition2["location"]
                            location_str = f"{location1}, {location2}"
                            
                            # 이미 있는 모순과 중복되지 않게 체크
                            if any(c["location1"] == location1 and c["location2"] == location2 for c in contradictions):
                                continue
                                
                            contradictions.append({
                                "location1": location1,
                                "location2": location2,
                                "explanation": explanation
                            })
                            
                            # 모순 필드 추적
                            contradiction_fields.add(field)
            
            # 발견된 모순에 대해 이슈 생성
            for contradiction in contradictions:
                issues.append(ConditionIssue(
                    field=field,
                    issue_type="self_contradiction",
                    severity="error",
                    location=f"{contradiction['location1']}, {contradiction['location2']}",
                    explanation=f"자기모순: {contradiction['explanation']}",
                    suggestion=self._generate_suggestion("self_contradiction", field)
                ))
        
        return issues, contradiction_fields
    
    def _generate_summary(self, issues: List[ConditionIssue]) -> str:
        """이슈 목록에서 요약 생성"""
        error_count = len([issue for issue in issues if issue.severity == "error"])
        warning_count = len([issue for issue in issues if issue.severity == "warning"])
        
        # 이슈 유형 카운트
        issue_types = set(issue.issue_type for issue in issues)
        issue_type_count = len(issue_types)
        
        # 총 이슈 건수
        total_issue_count = len(issues)
        
        if error_count == 0 and warning_count == 0:
            return "룰 검증이 완료되었습니다. 문제가 발견되지 않았습니다."
        
        summary_parts = []
        
        # 이슈 유형과 총 이슈 건수를 모두 표시하도록 수정
        if issue_type_count > 0 and total_issue_count > 0:
            summary_parts.append(f"총 {issue_type_count}가지 유형, {total_issue_count}건의 이슈가 발견되었습니다.")
        
        # 오류가 있는 경우
        if error_count > 0:
            error_str = f"{error_count}개의 오류"
            summary_parts.append(f"심각한 {error_str}를 수정해야 룰이 정상 작동합니다.")
        
        # 경고만 있는 경우
        if error_count == 0 and warning_count > 0:
            warning_str = f"{warning_count}개의 경고"
            summary_parts.append(f"{warning_str}가 있지만 룰은 작동 가능합니다.")
        
        return " ".join(summary_parts)
    
    def _generate_rule_summary(self, rule: Rule) -> str:
        """룰 요약 생성"""
        def format_condition(condition: RuleCondition, indent: int = 0) -> str:
            # 논리 연산자 블록인지 확인
            is_logical_block = condition.field == "placeholder" or (condition.field is None and condition.conditions is not None)
            
            if condition.conditions:
                nested_conditions = [format_condition(c, indent + 1) for c in condition.conditions]
                if condition.operator.lower() == "and":
                    return f"{'  ' * indent}모든 조건이 만족해야 합니다:\n" + "\n".join(nested_conditions)
                else:
                    return f"{'  ' * indent}다음 조건 중 하나가 만족해야 합니다:\n" + "\n".join(nested_conditions)
            else:
                # 실제 필드 조건인 경우에만 필드 정보 표시
                if not is_logical_block and condition.field and condition.field != "placeholder":
                    field_desc = self._get_field_type_description(condition.field)
                    operator_desc = self._get_human_readable_operator(condition.operator)
                    return f"{'  ' * indent}{field_desc} '{condition.field}'이(가) '{condition.value}'와(과) {operator_desc}"
                else:
                    return f"{'  ' * indent}조건 구조 오류: 필드 정보가 없습니다."

        if not rule.conditions:
            return "이 룰에는 조건이 없습니다."
            
        conditions_summary = [format_condition(condition) for condition in rule.conditions]
        return "이 룰은 다음과 같은 조건을 가집니다:\n" + "\n".join(conditions_summary)
    
    def _get_human_readable_operator(self, operator: str) -> str:
        """연산자를 사람이 이해하기 쉬운 표현으로 변환"""
        operator_map = {
            "eq": "같다(==)",
            "==": "같다(==)",
            "neq": "같지 않다(!=)",
            "!=": "같지 않다(!=)",
            "gt": "보다 크다(>)",
            ">": "보다 크다(>)",
            "gte": "보다 크거나 같다(>=)",
            ">=": "보다 크거나 같다(>=)",
            "lt": "보다 작다(<)",
            "<": "보다 작다(<)",
            "lte": "보다 작거나 같다(<=)",
            "<=": "보다 작거나 같다(<=)",
            "in": "목록에 포함됨(in)",
            "not_in": "목록에 포함되지 않음(not_in)",
            "contains": "포함한다(contains)",
            "starts_with": "로 시작한다(starts_with)",
            "ends_with": "로 끝난다(ends_with)",
            "and": "그리고(and)",
            "or": "또는(or)"
        }
        return operator_map.get(operator, operator)
    
    def _generate_suggestion(self, issue_type: str, field: str, operator: str = None, value: Any = None) -> str:
        """이슈 타입별 제안 내용 생성 - 템플릿화된 제안"""
        if issue_type == "invalid_operator":
            # 필드 타입 기반 메시지
            field_type = self._get_field_type(field)
            field_desc = self._get_field_type_description(field)
            
            # 필드별 허용 연산자 확인
            allowed_operators = []
            if field in self.field_schema and "allowed_operators" in self.field_schema[field]:
                allowed_operators = self.field_schema[field]["allowed_operators"]
            else:
                # 기본 타입별 허용 연산자
                if field_type in self._valid_operators:
                    allowed_operators = self._valid_operators[field_type]
            
            # 필드 스키마에 설명이 있으면 추가
            field_description = ""
            if field in self.field_schema and "description" in self.field_schema[field]:
                field_description = f" ({self.field_schema[field]['description']})"
            
            # 타입별 템플릿화된 제안 메시지
            type_templates = {
                "string": f"'{field}'{field_description} 필드는 문자열 데이터에 적합한 '같다(==)', '같지 않다(!=)', '포함한다(contains)' 등의 연산자를 사용하세요.",
                "number": f"'{field}'{field_description} 필드는 숫자 데이터에 적합한 '같다(==)', '보다 크다(>)', '보다 작다(<)' 등의 연산자를 사용하세요.",
                "boolean": f"'{field}'{field_description} 필드는 불리언(참/거짓) 데이터에 적합한 '같다(==)', '같지 않다(!=)' 연산자만 사용하세요.",
                "date": f"'{field}'{field_description} 필드는 날짜 데이터에 적합한 '같다(==)', '보다 이전(<=)', '보다 이후(>=)' 등의 연산자를 사용하세요.",
                "array": f"'{field}'{field_description} 필드는 배열 데이터에 적합한 '포함함(contains)', '포함하지 않음(not_contains)' 등의 연산자를 사용하세요.",
                "logical": "논리 연산자 블록에는 'AND' 또는 'OR' 연산자만 사용하세요."
            }
            
            # 타입에 맞는 템플릿 반환
            if field_type in type_templates:
                return type_templates[field_type]
            else:
                # 일반적인 제안
                return f"'{field}' 필드에 적절한 연산자를 사용하세요."
        
        elif issue_type == "type_mismatch":
            field_type = self._get_field_type(field)
            field_type_desc = self._get_field_type_description(field)
            value_type = type(value).__name__ if value is not None else "None"
            
            # 필드 스키마에 설명이 있으면 추가
            field_description = ""
            if field in self.field_schema and "description" in self.field_schema[field]:
                field_description = f" ({self.field_schema[field]['description']})"
            
            # 숫자로 변환 가능한 문자열의 경우 구체적 제안
            if field_type == "number" and isinstance(value, str):
                try:
                    num_value = float(value)
                    return f"'{field}'{field_description} 필드는 숫자여야 합니다. 문자열 '{value}' 대신 숫자 {value}를 입력하세요."
                except:
                    pass
            
            # 타입별 예시 값
            example_values = {
                "number": "1, 2, 3, 10.5",
                "string": "'홍길동', '서울시'",
                "boolean": "true 또는 false",
                "array": "[1, 2, 3] 또는 ['a', 'b', 'c']",
                "date": "'2023-01-01'"
            }
            
            example = example_values.get(field_type, f"{field_type_desc} 타입 값")
            return f"'{field}'{field_description} 필드는 {field_type_desc} 타입이어야 합니다. 예: {example}"
        
        elif issue_type == "duplicate_condition":
            # 필드 스키마에 설명이 있으면 추가
            field_description = ""
            if field in self.field_schema and "description" in self.field_schema[field]:
                field_description = f" ({self.field_schema[field]['description']})"
                
            return f"'{field}'{field_description} 필드에 중복된 조건이 있습니다. 하나의 조건으로 통합하세요."
        
        elif issue_type == "self_contradiction":
            return f"'{field}' 필드에 모순되는 조건이 있습니다. 충돌하는 조건을 검토하고 수정하세요."
        
        elif issue_type == "complexity_warning":
            return "룰 구조의 복잡성이 높습니다. 조건을 단순화하거나 여러 룰로 분리하세요."
        
        elif issue_type == "missing_condition":
            if field == "conditions":
                return "룰에는 최소한 하나의 조건이 필요합니다. 구체적인 필드와 조건을 추가하세요."
            else:
                # 필드 스키마에 설명이 있으면 추가
                field_description = ""
                if field in self.field_schema and "description" in self.field_schema[field]:
                    field_description = f" ({self.field_schema[field]['description']})"
                return f"'{field}'{field_description} 필드에 대해 값이 0 또는 기본값인 경우의 처리를 규칙에 명시적으로 추가하는 것이 좋습니다."
        
        elif issue_type == "ambiguous_branch":
            # 필드 스키마에 설명이 있으면 추가
            field_description = ""
            if field in self.field_schema and "description" in self.field_schema[field]:
                field_description = f" ({self.field_schema[field]['description']})"
                
            return f"'{field}'{field_description} 필드에 대한 분기 처리가 불명확합니다. 모든 가능한 입력값에 대해 명확한 처리 경로를 정의하고, 중복 적용되는 조건이 없도록 하세요."
        
        else:
            return "이슈를 해결하기 위한 적절한 조치를 취하세요."
    
    def _get_field_type_description(self, field: str) -> str:
        """필드 타입에 대한 설명 반환 - 스키마 기반으로 수정"""
        # 스키마에서 타입 정보 가져오기
        if field in self.field_schema:
            field_type = self.field_schema[field]["type"]
        else:
            field_type = self._get_field_type(field)
            
        # 타입별 사람이 이해하기 쉬운 설명
        type_descriptions = {
            "string": "문자열",
            "number": "숫자",
            "boolean": "참/거짓",
            "date": "날짜",
            "array": "배열",
            "logical": "논리 연산자"
        }
        return type_descriptions.get(field_type, "알 수 없는 타입")
    
    def _get_condition_location(self, condition: RuleCondition) -> str:
        """조건의 위치 정보 문자열 반환"""
        global_index = self.condition_index_map.get(id(condition), 0)
        if global_index:
            return f"조건 {global_index}"
        return "알 수 없는 위치"
    
    def _get_conditions_location(self, conditions: List[RuleCondition]) -> str:
        """여러 조건의 위치 정보 문자열 반환"""
        if not conditions:
            return ""
            
        indices = []
        for condition in conditions:
            global_index = self.condition_index_map.get(id(condition), 0)
            if global_index:
                indices.append(str(global_index))
        
        if len(indices) > 2:
            # 3개 이상이면 처음과 끝만 표시
            return f"조건 {indices[0]}~{indices[-1]}"
        else:
            # 2개 이하면 단순 나열
            return "조건 " + ", ".join(indices)

    def _check_ambiguous_branches(self, conditions: List[RuleCondition]) -> List[ConditionIssue]:
        """분기 불명확 검사 - 입력값이 어느 조건에도 해당되지 않거나, 여러 조건 분기에 동시에 포함되는 경우를 감지"""
        issues = []
        
        # 필드별 조건 정보 수집
        field_conditions = {}
        
        def collect_condition_info(condition_list, parent_path="", parent_operator=None):
            for idx, condition in enumerate(condition_list):
                # 필드가 있고 논리 연산자가 아닌 경우만 처리
                if condition.field and condition.field != "placeholder":
                    if condition.field not in field_conditions:
                        field_conditions[condition.field] = []
                    
                    # 조건 인덱스와 위치 기록
                    condition_id = f"{parent_path}/{idx+1}" if parent_path else f"{idx+1}"
                    global_index = self.condition_index_map.get(id(condition), 0)
                    condition_location = f"조건 {global_index}" if global_index else condition_id
                    
                    # 상위 논리 연산자 정보와 함께 조건 정보 저장
                    field_conditions[condition.field].append({
                        "field": condition.field,
                        "operator": condition.operator,
                        "value": condition.value,
                        "location": condition_location,
                        "parent_operator": parent_operator  # 상위 논리 연산자 (AND/OR)
                    })
                
                # 중첩 조건이 있는 경우 재귀 처리
                if condition.conditions:
                    # 현재 조건의 논리 연산자 판단
                    current_operator = None
                    if condition.operator and condition.operator.upper() in ["AND", "OR"]:
                        current_operator = condition.operator.upper()
                    
                    # 부모 연산자가 없고 자식이 있는 경우, 기본값 AND 설정 (묵시적 AND)
                    if not current_operator and not parent_operator:
                        current_operator = "AND"
                    
                    # 재귀 호출 시 현재 연산자 전달
                    new_path = f"{parent_path}/{idx+1}" if parent_path else f"{idx+1}"
                    collect_condition_info(condition.conditions, new_path, current_operator or parent_operator)
        
        # 필드별 조건 정보 수집
        collect_condition_info(conditions)
        
        # 각 필드별로 분기 불명확 검사
        for field, conditions_list in field_conditions.items():
            # 동일 필드에 대한 조건이 2개 이상인 경우만 검사
            if len(conditions_list) < 2:
                continue
            
            # 필드 타입 확인
            field_type = self._get_field_type(field)
            
            # 타입별 검사 방법 선택
            if field_type == "number":
                ambiguous_issue = self._check_number_field_ambiguity(field, conditions_list)
                if ambiguous_issue:
                    issues.append(ambiguous_issue)
            elif field_type == "string":
                ambiguous_issue = self._check_string_field_ambiguity(field, conditions_list)
                if ambiguous_issue:
                    issues.append(ambiguous_issue)
        
        # 중첩 조건에 대해서도 검사
        for condition in conditions:
            if condition.conditions:
                nested_issues = self._check_ambiguous_branches(condition.conditions)
                issues.extend(nested_issues)
        
        return issues
    
    def _check_number_field_ambiguity(self, field: str, conditions: List[Dict[str, Any]]) -> Optional[ConditionIssue]:
        """숫자 필드에 대한 분기 불명확 검사"""
        # 1. 동일 상위 OR 블록 내에서 값 영역이 겹치는 조건 검사
        or_groups = {}
        
        # OR 그룹별로 조건 분류
        for condition in conditions:
            parent_op = condition.get("parent_operator")
            if parent_op == "OR":
                group_key = str(id(parent_op))  # 부모 연산자 객체의 ID
                if group_key not in or_groups:
                    or_groups[group_key] = []
                or_groups[group_key].append(condition)
        
        # 각 OR 그룹 내에서 값 영역 겹침 확인
        overlapping_conditions = []
        for group_key, group_conditions in or_groups.items():
            if len(group_conditions) < 2:
                continue
                
            # 범위 조건 추출
            ranges = []
            for condition in group_conditions:
                op = condition["operator"]
                value = condition["value"]
                
                if not isinstance(value, (int, float)):
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        continue
                
                if op == "==":
                    ranges.append({"min": value, "max": value, "condition": condition})
                elif op == ">":
                    ranges.append({"min": value + 0.000001, "max": float("inf"), "condition": condition})
                elif op == ">=":
                    ranges.append({"min": value, "max": float("inf"), "condition": condition})
                elif op == "<":
                    ranges.append({"min": float("-inf"), "max": value - 0.000001, "condition": condition})
                elif op == "<=":
                    ranges.append({"min": float("-inf"), "max": value, "condition": condition})
            
            # 범위 겹침 확인
            for i in range(len(ranges)):
                for j in range(i+1, len(ranges)):
                    range1 = ranges[i]
                    range2 = ranges[j]
                    
                    # 겹치는 부분이 있는지 확인
                    if max(range1["min"], range2["min"]) <= min(range1["max"], range2["max"]):
                        overlapping_conditions.append((range1["condition"], range2["condition"]))
        
        # 겹치는 조건이 있으면 이슈 생성
        if overlapping_conditions:
            locations = []
            for cond1, cond2 in overlapping_conditions:
                locations.append(f"{cond1['location']}, {cond2['location']}")
            
            location_str = "; ".join(locations)
            field_desc = ""
            if field in self.field_schema and "description" in self.field_schema[field]:
                field_desc = f" ({self.field_schema[field]['description']})"
            
            return ConditionIssue(
                field=field,
                issue_type="ambiguous_branch",
                severity="warning",
                location=location_str,
                explanation=f"{field}{field_desc} 필드에 대한 조건이 여러 분기에 동시에 적용될 수 있습니다. 값 범위가 겹치는 조건이 있습니다.",
                suggestion="조건 분기를 명확하게 정의하세요. 범위가 겹치지 않도록 조건을 수정하세요."
            )
        
        # 2. 어느 조건에도 해당되지 않는 사각지대 검출
        all_values = set()
        for condition in conditions:
            op = condition["operator"]
            value = condition["value"]
            
            if op == "==" and isinstance(value, (int, float)):
                all_values.add(value)
        
        # 0을 포함한 주요 값이 누락되었는지 확인
        key_values = [0, 1]  # 주요 확인 값
        missing_values = []
        
        for key_value in key_values:
            if key_value not in all_values and all(not self._value_matches_condition(key_value, condition) for condition in conditions):
                missing_values.append(key_value)
        
        if missing_values:
            field_desc = ""
            if field in self.field_schema and "description" in self.field_schema[field]:
                field_desc = f" ({self.field_schema[field]['description']})"
            
            values_str = ", ".join([str(v) for v in missing_values])
            return ConditionIssue(
                field=field,
                issue_type="ambiguous_branch",
                severity="warning",
                location=f"필드 '{field}' 조건",
                explanation=f"{field}{field_desc} 필드가 {values_str} 값일 때는 어느 조건에도 해당되지 않아 분기 처리가 불명확합니다.",
                suggestion=f"{field} 필드의 모든 가능한 값에 대한 처리를 정의하세요."
            )
        
        return None
    
    def _check_string_field_ambiguity(self, field: str, conditions: List[Dict[str, Any]]) -> Optional[ConditionIssue]:
        """문자열 필드에 대한 분기 불명확 검사"""
        # 문자열 필드는 주로 == 연산자로 검사하므로, 동일 값에 대한 중복 조건 검사
        string_values = {}
        
        for condition in conditions:
            op = condition["operator"]
            value = condition["value"]
            
            if op == "==" and isinstance(value, str):
                if value not in string_values:
                    string_values[value] = []
                string_values[value].append(condition)
        
        # 동일 값에 대해 여러 조건이 있는 경우
        ambiguous_values = {}
        for value, value_conditions in string_values.items():
            if len(value_conditions) > 1:
                # 서로 다른 상위 연산자(AND/OR) 아래에 있는 경우만 애매함으로 판단
                parent_ops = set(cond.get("parent_operator") for cond in value_conditions)
                if len(parent_ops) > 1 or "OR" in parent_ops:
                    ambiguous_values[value] = value_conditions
        
        if ambiguous_values:
            locations = []
            for value, value_conditions in ambiguous_values.items():
                cond_locations = [cond["location"] for cond in value_conditions]
                locations.append(f"값 '{value}': {', '.join(cond_locations)}")
            
            location_str = "; ".join(locations)
            field_desc = ""
            if field in self.field_schema and "description" in self.field_schema[field]:
                field_desc = f" ({self.field_schema[field]['description']})"
            
            return ConditionIssue(
                field=field,
                issue_type="ambiguous_branch",
                severity="warning",
                location=location_str,
                explanation=f"{field}{field_desc} 필드에 대한 동일 값이 여러 조건 분기에 중복 정의되어 있어 처리 경로가 불명확합니다.",
                suggestion="동일 값에 대한 처리를 한 곳으로 통합하여 논리적 일관성을 유지하세요."
            )
            
        # 주요 값('', null 등)이 어느 조건에도 해당되지 않는지 확인
        key_values = ["", None]  # 주요 확인 값
        missing_values = []
        
        for key_value in key_values:
            if all(not self._value_matches_condition(key_value, condition) for condition in conditions):
                missing_values.append(key_value if key_value != "" else "빈 문자열")
        
        if missing_values:
            field_desc = ""
            if field in self.field_schema and "description" in self.field_schema[field]:
                field_desc = f" ({self.field_schema[field]['description']})"
            
            values_str = ", ".join([str(v) for v in missing_values])
            return ConditionIssue(
                field=field,
                issue_type="ambiguous_branch",
                severity="warning",
                location=f"필드 '{field}' 조건",
                explanation=f"{field}{field_desc} 필드가 {values_str}일 때는 어느 조건에도 해당되지 않아 분기 처리가 불명확합니다.",
                suggestion=f"{field} 필드의 모든 가능한 값(특히 기본값과 특수 케이스)에 대한 처리를 정의하세요."
            )
        
        return None
    
    def _value_matches_condition(self, value: Any, condition: Dict[str, Any]) -> bool:
        """주어진 값이 조건에 매칭되는지 확인"""
        op = condition["operator"]
        condition_value = condition["value"]
        
        # 타입 호환성 확인 - 비교 연산자는 동일한 타입 간에만 비교 가능
        if op in [">", ">=", "<", "<="]:
            # 숫자 비교 시 타입 호환성 검사
            if isinstance(value, (int, float)) and isinstance(condition_value, (int, float)):
                pass  # 두 값이 모두 숫자면 계속 진행
            elif isinstance(value, str) and isinstance(condition_value, str):
                pass  # 두 값이 모두 문자열이면 계속 진행
            else:
                # 타입이 호환되지 않으면 False 반환 (비교 불가)
                return False
                
        if op == "==":
            return value == condition_value
        elif op == "!=":
            return value != condition_value
        elif op == ">":
            return value > condition_value
        elif op == ">=":
            return value >= condition_value
        elif op == "<":
            return value < condition_value
        elif op == "<=":
            return value <= condition_value
        elif op == "in" and isinstance(condition_value, list):
            return value in condition_value
        elif op == "contains" and isinstance(condition_value, str) and isinstance(value, str):
            return condition_value in value
        elif op == "starts_with" and isinstance(condition_value, str) and isinstance(value, str):
            return value.startswith(condition_value)
        elif op == "ends_with" and isinstance(condition_value, str) and isinstance(value, str):
            return value.endswith(condition_value)
        
        return False

    def _optimize_issues(self, issues: List[ConditionIssue]) -> List[ConditionIssue]:
        """이슈 중복 제거 및 우선순위 고려하여 최적화"""
        # 필드별로 이슈 그룹화
        field_issues: Dict[str, List[ConditionIssue]] = {}
        
        for issue in issues:
            field_key = str(issue.field) if issue.field is not None else "null"
            if field_key not in field_issues:
                field_issues[field_key] = []
            field_issues[field_key].append(issue)
            
        # 최적화된 이슈 목록
        optimized = []
        
        for field_key, field_issue_list in field_issues.items():
            # 같은 타입의 이슈 합치기
            issue_by_type: Dict[str, List[ConditionIssue]] = {}
            
            # 모순 이슈 존재 여부 확인
            has_contradiction = any(issue.issue_type == "self_contradiction" for issue in field_issue_list)
            
            for issue in field_issue_list:
                # 같은 필드에 모순과 중복이 함께 있는 경우, 중복은 제외
                if has_contradiction and issue.issue_type == "duplicate_condition":
                    continue
                
                if issue.issue_type not in issue_by_type:
                    issue_by_type[issue.issue_type] = []
                issue_by_type[issue.issue_type].append(issue)
            
            # 각 타입별로 중요도를 고려하여 이슈 추가
            # 우선순위: self_contradiction(모순) > 기타 error > warning
            issue_type_priority = {
                "self_contradiction": 0,  # 가장 높은 우선순위
                "invalid_operator": 1,
                "type_mismatch": 2,
                "ambiguous_branch": 3,
                "missing_condition": 4,
                "complexity_warning": 5,
                "duplicate_condition": 6  # 가장 낮은 우선순위
            }
            
            # 우선순위에 따라 이슈 타입 정렬
            sorted_issue_types = sorted(
                issue_by_type.keys(),
                key=lambda x: issue_type_priority.get(x, 999)  # 정의되지 않은 타입은 낮은 우선순위
            )
            
            for issue_type in sorted_issue_types:
                type_issues = issue_by_type[issue_type]
                
                if len(type_issues) == 1:
                    # 단일 이슈는 그대로 추가
                    optimized.append(type_issues[0])
                else:
                    # 여러 개의 같은 타입 이슈는 합쳐서 추가
                    locations = []
                    explanations = []
                    
                    for issue in type_issues:
                        if issue.location and issue.location not in locations:
                            locations.append(issue.location)
                        if issue.explanation and issue.explanation not in explanations:
                            explanations.append(issue.explanation)
                    
                    # 첫 번째 이슈를 기반으로 통합 이슈 생성
                    combined_issue = type_issues[0].model_copy()
                    
                    # 위치 정보는 모두 결합 - 이슈 개수는 하나지만 위치는 모두 표시
                    if locations:
                        combined_issue.location = ", ".join(locations)
                    
                    if len(explanations) > 1:
                        # 문장을 마침표나 줄바꿈으로 분리 (';' → '. ')
                        combined_issue.explanation = ". ".join([e.rstrip(";,. ") for e in explanations])
                    
                    optimized.append(combined_issue)
        
        # 최종 정렬: 심각도(error > warning)와 이슈 타입 우선순위로
        return sorted(
            optimized,
            key=lambda x: (
                0 if x.severity == "error" else 1,  # error가 먼저
                issue_type_priority.get(x.issue_type, 999)  # 이슈 타입 우선순위
            )
        )

    def _assign_global_indices(self, conditions: List[RuleCondition], parent_operator: str = None) -> None:
        """모든 조건에 글로벌 인덱스 할당"""
        for condition in conditions:
            # 인덱스 할당
            self.global_condition_index += 1
            self.condition_index_map[id(condition)] = self.global_condition_index
            
            # 부모 연산자 정보 저장 (location 표시에 활용)
            if parent_operator:
                setattr(condition, 'parent_operator', parent_operator)
            
            # 현재 조건의 연산자 추출
            current_operator = None
            if hasattr(condition, 'operator'):
                current_operator = condition.operator
            
            # 중첩 조건이 있는 경우 재귀 처리
            if condition.conditions:
                # 논리 연산자는 대문자로 표준화
                if current_operator and current_operator.upper() in ["AND", "OR"]:
                    self._assign_global_indices(condition.conditions, current_operator.upper())
                else:
                    self._assign_global_indices(condition.conditions, parent_operator)

    def _get_field_type(self, field: str) -> str:
        """필드 타입 반환 - 스키마 기반"""
        # 스키마에 정의된 필드 타입 반환
        if field in self.field_schema:
            return self.field_schema[field]["type"]
            
        # 기본 타입 추론 (이전 코드 유지, 백업 메커니즘)
        field_types = {
            "age": "number",
            "score": "number",
            "price": "number",
            "name": "string",
            "grade": "string",
            "category": "string",
            "membership": "string",
            "status": "string",
            "tags": "array",
            "date": "date"
        }
        return field_types.get(field, "string")  # 기본값은 문자열

    def _count_conditions(self, conditions: List[RuleCondition]) -> int:
        """전체 조건 노드 수 계산 - 논리 연산자 노드 포함"""
        if not conditions:
            return 0
            
        count = len(conditions)
        for condition in conditions:
            if condition.conditions:
                count += self._count_conditions(condition.conditions)
                
        return count

    def _count_field_conditions(self, conditions: List[RuleCondition]) -> int:
        """실제 필드를 가진 비교 조건 수만 계산 (논리 연산자 노드 제외)"""
        if not conditions:
            return 0
            
        count = 0
        for condition in conditions:
            # field가 있고 논리 연산자가 아닌 경우만 카운트
            if condition.field and condition.field.upper() not in ["AND", "OR", "GROUP"] and condition.field != "placeholder":
                count += 1
            
            # 중첩 조건도 계산
            if condition.conditions:
                count += self._count_field_conditions(condition.conditions)
                
        return count
    
    def _extract_unique_fields(self, conditions: List[RuleCondition]) -> List[str]:
        """고유 필드 추출 - 유효한 필드만 포함"""
        unique_fields = set()
        
        def extract_fields(conditions_list):
            for condition in conditions_list:
                # 실제 필드만 추가 (논리 연산자 블록 제외)
                if condition.field and condition.field.upper() not in ["AND", "OR", "GROUP"] and condition.field != "placeholder":
                    unique_fields.add(condition.field)
                if condition.conditions:
                    extract_fields(condition.conditions)
                    
        extract_fields(conditions)
        return list(unique_fields)

    def _check_missing_conditions(self, conditions: List[RuleCondition]) -> List[ConditionIssue]:
        """조건 누락 가능성 탐지"""
        issues = []
        field_conditions = {}
        
        # 필드별로 조건 그룹화
        for condition in conditions:
            # 논리 연산자 블록 제외, 실제 필드 조건만 검사
            if condition.field and condition.field != "placeholder":
                if condition.field not in field_conditions:
                    field_conditions[condition.field] = []
                
                field_conditions[condition.field].append({
                    "operator": condition.operator,
                    "value": condition.value
                })
        
        # 각 필드별로 누락된 조건 검사
        for field, conditions_list in field_conditions.items():
            # 현재는 숫자 타입 필드에 대한 범위 누락만 검사
            if field in self.field_schema and self.field_schema[field]["type"] == "number":
                missing_ranges = self._check_number_field_missing_ranges(field, conditions_list)
                issues.extend(missing_ranges)
        
        # 중첩 조건에 대해서도 검사
        for condition in conditions:
            if condition.conditions:
                nested_issues = self._check_missing_conditions(condition.conditions)
                issues.extend(nested_issues)
                
        return issues
    
    def _check_number_field_missing_ranges(self, field: str, conditions: List[Dict[str, Any]]) -> List[ConditionIssue]:
        """숫자 필드에 대한 범위 누락 검사"""
        issues = []
        
        # 숫자 필드에 대한 조건들을 분석
        min_values = []  # >= 또는 > 연산자의 값들
        max_values = []  # <= 또는 < 연산자의 값들
        exact_values = set()  # == 연산자의 값들
        not_exact_values = set()  # != 연산자의 값들
        
        # 연산자별로 값 분류
        for condition in conditions:
            try:
                value = float(condition["value"]) if isinstance(condition["value"], str) else condition["value"]
                
                if condition["operator"] == ">=":
                    min_values.append({"value": value, "inclusive": True})
                elif condition["operator"] == ">":
                    min_values.append({"value": value, "inclusive": False})
                elif condition["operator"] == "<=":
                    max_values.append({"value": value, "inclusive": True})
                elif condition["operator"] == "<":
                    max_values.append({"value": value, "inclusive": False})
                elif condition["operator"] == "==":
                    exact_values.add(value)
                elif condition["operator"] == "!=":
                    not_exact_values.add(value)
            except (ValueError, TypeError):
                # 숫자 변환 실패 시 건너뜀
                continue
        
        # 특별한 경우: 최소값은 있는데 0보다 크고, 0에 대한 조건은 없는 경우
        if min_values and not max_values and not any(v["value"] == 0 for v in min_values) and not 0 in exact_values:
            min_value = min(v["value"] for v in min_values)
            
            if min_value > 0:
                field_desc = ""
                if field in self.field_schema and "description" in self.field_schema[field]:
                    field_desc = f" ({self.field_schema[field]['description']})"
                
                issues.append(ConditionIssue(
                    field=field,
                    issue_type="missing_condition",
                    severity="warning",
                    location=f"필드 '{field}' 조건",
                    explanation=f"{field}{field_desc} = 0인 경우는 어떤 조건에도 해당되지 않으므로 누락된 조건 가능성이 있습니다.",
                    suggestion=f"'{field}' 필드에 대해 값이 0인 경우의 처리를 규칙에 명시적으로 추가하는 것이 좋습니다."
                ))
        
        # 최소값과 최대값 사이에 특정 값에 대한 조건이 누락된 경우 (현재는 복잡한 검사는 구현하지 않음)
        # 이 부분은 필요에 따라 추가 조건 검사 가능
        
        return issues
    
    def _generate_ai_comment(self, rule: Rule, issues: List[ConditionIssue], structure: StructureInfo) -> Optional[str]:
        """
        정해진 이슈 타입 외에 AI가 자유롭게 판단한 조언을 생성
        - 설계 팁, 의문 제기, 개선 제안, 단순화 제안 등을 포함
        - 이슈가 없거나 조언할 내용이 없으면 None 반환
        """
        if not issues and structure.depth <= 2 and structure.condition_node_count <= 5:
            return None  # 이슈가 없고 구조가 단순하면 조언 생략
            
        comments = []
        
        # 1. 구조적 복잡성 분석
        if structure.depth >= 4 or structure.condition_node_count >= 8:
            comments.append("조건이 중첩된 구조는 유지보수에 취약할 수 있으므로 간결하게 리팩토링을 고려하세요.")
        
        # 2. 필드별 조건 수 분석
        field_condition_counts = {}
        logical_operators = {"and": 0, "or": 0}
        missing_default_fields = []
        special_fields = set(["ENTR_STUS_CD", "MRKT_CD", "MBL_ACT_MEM_PCNT", "IOT_MEM_PCNT"])
        
        def analyze_fields(conditions):
            nonlocal missing_default_fields
            
            for condition in conditions:
                # 필드 조건 카운트
                if condition.field and condition.field != "placeholder":
                    if condition.field not in field_condition_counts:
                        field_condition_counts[condition.field] = 0
                    field_condition_counts[condition.field] += 1
                    
                    # 기본값 처리 누락 가능성 체크
                    if condition.field in special_fields and condition.field not in missing_default_fields:
                        # 특정 필드들에 대한 조건이 제한적인 경우
                        if condition.field == "ENTR_STUS_CD" and condition.operator == "==" and condition.value == "정지":
                            missing_default_fields.append(condition.field)  # 일단 추가
                
                # 특정 값을 가진 조건이 있으면 missing_default_fields에서 제거
                if condition.field == "ENTR_STUS_CD" and condition.operator == "==" and condition.value == "정상":
                    if "ENTR_STUS_CD" in missing_default_fields:
                        missing_default_fields.remove("ENTR_STUS_CD")
                
                # 논리 연산자 카운트
                if condition.operator and condition.operator.lower() in ["and", "or"]:
                    logical_operators[condition.operator.lower()] += 1
                    
                # 중첩 조건 재귀 분석
                if condition.conditions:
                    analyze_fields(condition.conditions)
        
        analyze_fields(rule.conditions)
        
        # 3. 특정 패턴 분석
        # 3.1. OR 연산자가 많은 경우
        if logical_operators["or"] > 2 and logical_operators["or"] > logical_operators["and"] * 2:
            comments.append("OR 연산자 사용이 많습니다. 일부 조건은 의미적으로 중복되거나 합쳐질 수 있는지 검토해보세요.")
            
        # 3.2. 특정 필드에 조건이 집중된 경우
        for field, count in field_condition_counts.items():
            if count >= 3:
                field_desc = ""
                if field in self.field_schema and "description" in self.field_schema[field]:
                    field_desc = f"({self.field_schema[field]['description']})"
                comments.append(f"{field} {field_desc} 필드에 대한 조건이 {count}개로 많습니다. 조건을 범위로 단순화할 수 있는지 검토하세요.")
                break  # 가장 많은 조건을 가진 필드 하나만 언급
        
        # 3.3. 누락된 기본 상태 체크
        if missing_default_fields:
            field = missing_default_fields[0]  # 첫 번째 필드만 언급
            if field == "ENTR_STUS_CD":
                comments.append(f"{field}는 '정지' 상태만 정의되어 있는데, '정상' 상태도 함께 고려하는 것이 좋습니다.")
        
        # 4. 최종 코멘트 조합 (1~2개 선택)
        if not comments:
            return None  # 조언할 내용이 없음
            
        # 가장 관련성 높은 코멘트 1-2개만 선택
        selected_comments = comments[:min(2, len(comments))]
        
        return " ".join(selected_comments)

    def _precheck_type_mismatches(self, conditions: List[RuleCondition]) -> List[ConditionIssue]:
        """타입 불일치를 검사하여 이슈 목록 반환 (이전: 예외 발생)"""
        issues = []
        
        for i, condition in enumerate(conditions):
            try:
                # 필드 타입 확인
                if condition.field:
                    field_type = self._get_field_type(condition.field)
                    location = f"조건 {self.condition_index_map.get(id(condition), i+1)}"
                    
                    # 숫자 타입 필드에 문자열 값을 사용하는 경우 - 더 엄격한 체크
                    if field_type == "number" and not isinstance(condition.value, (int, float)):
                        # 이전: raise TypeError
                        # 현재: 이슈 추가
                        field_desc = ""
                        if condition.field in self.field_schema and "description" in self.field_schema[condition.field]:
                            field_desc = f" ({self.field_schema[condition.field]['description']})"
                        
                        issues.append(ConditionIssue(
                            field=condition.field,
                            issue_type="type_mismatch",
                            severity="error",
                            location=location,
                            explanation=f"타입 불일치: 숫자(int) 타입 필드 '{condition.field}'{field_desc}에 {type(condition.value).__name__} 타입 값이 사용되었습니다.",
                            suggestion=f"조건에 사용된 값의 타입이 일치하는지 확인하세요. '{condition.field}' 필드는 숫자 타입이므로 숫자 값을 사용해야 합니다."
                        ))
                    
                    # 문자열 타입 필드에 숫자 값을 사용하는 경우
                    if field_type == "string" and isinstance(condition.value, (int, float)):
                        # 이전: raise TypeError
                        # 현재: 이슈 추가
                        field_desc = ""
                        if condition.field in self.field_schema and "description" in self.field_schema[condition.field]:
                            field_desc = f" ({self.field_schema[condition.field]['description']})"
                        
                        issues.append(ConditionIssue(
                            field=condition.field,
                            issue_type="type_mismatch",
                            severity="error",
                            location=location,
                            explanation=f"타입 불일치: 문자열(str) 타입 필드 '{condition.field}'{field_desc}에 숫자({type(condition.value).__name__}) 값 {condition.value}이 사용되었습니다.",
                            suggestion=f"조건에 사용된 값의 타입이 일치하는지 확인하세요. '{condition.field}' 필드는 문자열 타입이므로 문자열 값을 사용해야 합니다."
                        ))
                    
                    # 비교 연산자에 대한 추가 검사
                    if condition.operator in [">", ">=", "<", "<="]:
                        # 비교 연산자에 대한 타입 체크
                        if field_type == "string":
                            # 이전: raise TypeError
                            # 현재: 이슈 추가
                            field_desc = ""
                            if condition.field in self.field_schema and "description" in self.field_schema[condition.field]:
                                field_desc = f" ({self.field_schema[condition.field]['description']})"
                            
                            issues.append(ConditionIssue(
                                field=condition.field,
                                issue_type="invalid_operator",
                                severity="error",
                                location=location,
                                explanation=f"비교 연산자 '{condition.operator}'는 문자열 타입 필드 '{condition.field}'{field_desc}에 사용할 수 없습니다.",
                                suggestion=f"문자열 필드에는 '==', '!=', 'contains' 등의 연산자를 사용하세요. 비교 연산자(>, <, >=, <=)는 숫자 타입에만 사용 가능합니다."
                            ))
            except Exception as e:
                print(f"타입 검사 중 예외 발생 ({condition.field if hasattr(condition, 'field') else 'unknown'}): {str(e)}")
                # 예외는 무시하고 계속 진행 (다른 조건 검사를 위해)
                pass
            
            # 중첩 조건이 있는 경우 재귀적으로 검사
            if condition.conditions:
                nested_issues = self._precheck_type_mismatches(condition.conditions)
                issues.extend(nested_issues)
                
        return issues