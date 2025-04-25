from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from app.models.rule import Rule

class ValidationIssue(BaseModel):
    """Validation issue model"""
    severity: str = Field(..., description="Issue severity (error, warning, info)")
    message: str = Field(..., description="Issue description")
    location: Optional[str] = Field(None, description="Location of the issue in the rule")
    suggestion: Optional[str] = Field(None, description="Suggestion to fix the issue")

class ValidationResult(BaseModel):
    """Validation result model"""
    valid: bool = Field(..., description="Whether the rule is valid or not")
    issues: List[ValidationIssue] = Field(default_factory=list, description="List of validation issues")
    summary: str = Field(..., description="Summary of validation results in natural language")
    
class RuleValidationRequest(BaseModel):
    """Request model for rule validation"""
    rule: Rule = Field(..., description="Rule to validate")

class RuleJsonValidationRequest(BaseModel):
    """Request model for rule validation using the original JSON format"""
    rule_json: Dict[str, Any] = Field(..., description="Rule JSON to validate")

class RuleValidationResponse(BaseModel):
    """Response model for rule validation"""
    validation_result: ValidationResult = Field(..., description="Validation result")
    rule_summary: str = Field(..., description="Natural language summary of the rule") 