from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class RuleCondition(BaseModel):
    """Rule condition model"""
    field: str = Field(..., description="Field name to apply condition")
    operator: str = Field(..., description="Condition operator (eq, gt, lt, etc)")
    value: Any = Field(..., description="Value to compare")

class RuleAction(BaseModel):
    """Rule action model"""
    action_type: str = Field(..., description="Type of action to perform")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Action parameters")

class Rule(BaseModel):
    """Rule model with conditions and actions"""
    id: Optional[str] = Field(None, description="Rule unique identifier")
    name: str = Field(..., description="Rule name")
    description: str = Field(..., description="Rule description in natural language")
    conditions: List[RuleCondition] = Field(..., description="List of conditions")
    actions: List[RuleAction] = Field(..., description="List of actions to perform if conditions are met")
    priority: int = Field(default=1, description="Rule execution priority (lower means higher priority)")
    enabled: bool = Field(default=True, description="Whether the rule is enabled or not")

class RuleGenerationRequest(BaseModel):
    """Request model for rule generation"""
    description: str = Field(..., description="Natural language description of the rule to generate")
    additional_context: Optional[str] = Field(None, description="Additional context for rule generation")

class RuleGenerationResponse(BaseModel):
    """Response model for rule generation"""
    rule: Rule = Field(..., description="Generated rule")
    explanation: str = Field(..., description="Explanation of how the rule was generated") 