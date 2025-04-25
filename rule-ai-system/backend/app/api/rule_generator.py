from fastapi import APIRouter, Depends, HTTPException
from app.models.rule import RuleGenerationRequest, RuleGenerationResponse
from app.services.rule_generator import RuleGeneratorService

router = APIRouter()

@router.post("/generate", response_model=RuleGenerationResponse)
async def generate_rule(request: RuleGenerationRequest):
    """
    Generate a rule from natural language description
    
    - **description**: Natural language description of the rule
    - **additional_context**: Optional additional context for the rule generation
    """
    try:
        rule_generator = RuleGeneratorService()
        result = await rule_generator.generate_rule(request.description, request.additional_context)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating rule: {str(e)}"
        ) 