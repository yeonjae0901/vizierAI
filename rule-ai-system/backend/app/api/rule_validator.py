from fastapi import APIRouter, Depends, HTTPException
from app.models.validation_result import RuleValidationRequest, RuleValidationResponse
from app.services.rule_analyzer import RuleAnalyzerService

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