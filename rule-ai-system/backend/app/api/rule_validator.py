from fastapi import APIRouter, Depends, HTTPException
from app.models.validation_result import RuleValidationRequest, RuleValidationResponse, RuleJsonValidationRequest
from app.models.rule import Rule, RuleCondition, RuleAction
from app.services.rule_analyzer import RuleAnalyzerService
from typing import List, Dict, Any

router = APIRouter()

@router.post("/validate", response_model=RuleValidationResponse)
async def validate_rule(request: RuleValidationRequest):
    """
    Validate a rule and check for logical issues
    
    - **rule**: The rule to validate
    """
    try:
        rule_analyzer = RuleAnalyzerService()
        result = await rule_analyzer.validate_rule(request.rule)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validating rule: {str(e)}"
        )

@router.post("/validate-json", response_model=RuleValidationResponse)
async def validate_rule_json(request: RuleJsonValidationRequest):
    """
    Validate a rule using the original JSON format and check for logical issues
    
    - **rule_json**: The rule JSON to validate
    """
    try:
        # 원본 JSON 형식에서 Rule 객체로 변환
        rule_json = request.rule_json
        rule = convert_json_to_rule(rule_json)
        
        rule_analyzer = RuleAnalyzerService()
        result = await rule_analyzer.validate_rule(rule)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validating rule: {str(e)}"
        )

def convert_json_to_rule(rule_json: Dict[str, Any]) -> Rule:
    """원본 JSON 형식을 Rule 모델로 변환"""
    
    # 기본값 설정
    rule_id = rule_json.get("ruleId") or rule_json.get("id")
    rule_name = rule_json.get("name", "Unnamed Rule")
    rule_description = rule_json.get("description", "")
    rule_priority = rule_json.get("priority", 1)
    rule_enabled = rule_json.get("enabled", True)
    
    # 조건 변환
    conditions = extract_conditions(rule_json.get("conditions", {}))
    
    # 액션 변환
    actions = []
    if "message" in rule_json:
        message = rule_json["message"]
        if isinstance(message, list) and len(message) > 0:
            message = message[0]
        
        actions.append(RuleAction(
            action_type="display_message",
            parameters={"message": message}
        ))
    
    # 명시적인 액션이 있으면 추가
    if "actions" in rule_json and isinstance(rule_json["actions"], list):
        for action in rule_json["actions"]:
            if isinstance(action, dict) and "action_type" in action:
                actions.append(RuleAction(
                    action_type=action["action_type"],
                    parameters=action.get("parameters", {})
                ))
    
    # 액션이 하나도 없으면 기본 액션 추가
    if not actions:
        actions.append(RuleAction(
            action_type="no_action",
            parameters={}
        ))
    
    return Rule(
        id=rule_id,
        name=rule_name,
        description=rule_description,
        conditions=conditions,
        actions=actions,
        priority=rule_priority,
        enabled=rule_enabled
    )

def extract_conditions(conditions_data: Dict[str, Any]) -> List[RuleCondition]:
    """중첩된 조건 구조에서 조건 목록 추출"""
    result = []
    
    # 단순 조건인 경우
    if isinstance(conditions_data, dict) and "field" in conditions_data and "operator" in conditions_data:
        # 연산자 변환 (>, < 등의 기호를 gt, lt 등으로 변환)
        operator = map_operator(conditions_data.get("operator", "eq"))
        
        result.append(RuleCondition(
            field=conditions_data["field"],
            operator=operator,
            value=conditions_data.get("value")
        ))
        return result
    
    # conditions 키가 있는 경우 (중첩 구조)
    if isinstance(conditions_data, dict) and "conditions" in conditions_data and isinstance(conditions_data["conditions"], list):
        for condition in conditions_data["conditions"]:
            # 중첩 조건인 경우 재귀 호출
            if isinstance(condition, dict) and "conditions" in condition:
                result.extend(extract_conditions(condition))
            # 단순 조건인 경우
            elif isinstance(condition, dict) and "field" in condition and "operator" in condition:
                # 연산자 변환
                operator = map_operator(condition.get("operator", "eq"))
                
                result.append(RuleCondition(
                    field=condition["field"],
                    operator=operator,
                    value=condition.get("value")
                ))
    
    return result

def map_operator(operator: str) -> str:
    """연산자 기호를 FastAPI 모델에서 사용하는 문자열로 변환"""
    operator_map = {
        "==": "eq",
        "!=": "neq",
        ">": "gt",
        ">=": "gte",
        "<": "lt",
        "<=": "lte",
        "in": "in",
        "not in": "not_in",
        "contains": "contains"
    }
    
    return operator_map.get(operator, operator) 