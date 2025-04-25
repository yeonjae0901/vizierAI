from typing import List, Dict, Any
from app.models.rule import Rule
from app.models.validation_result import ValidationResult, ValidationIssue, RuleValidationResponse
from app.utils.logical_validator import LogicalValidator
from app.services.llm_service import LLMService

class RuleAnalyzerService:
    """Service for analyzing and validating rules"""
    
    def __init__(self):
        """Initialize rule analyzer service"""
        self.logical_validator = LogicalValidator()
        self.llm_service = LLMService()
    
    async def validate_rule(self, rule: Rule) -> RuleValidationResponse:
        """
        Validate a rule and generate a summary
        
        Args:
            rule: The rule to validate
            
        Returns:
            RuleValidationResponse with validation results and rule summary
        """
        # Perform logical validation
        validation_issues = self.logical_validator.validate(rule)
        
        # Determine if the rule is valid based on issues
        is_valid = not any(issue.severity == "error" for issue in validation_issues)
        
        # Generate summary if there are issues or create a basic one if not
        if validation_issues:
            summary = self._generate_issues_summary(validation_issues)
        else:
            summary = "The rule appears to be valid with no logical issues detected."
        
        # Create validation result
        validation_result = ValidationResult(
            valid=is_valid,
            issues=validation_issues,
            summary=summary
        )
        
        # Generate rule summary using LLM
        rule_summary = await self._generate_rule_summary(rule)
        
        return RuleValidationResponse(
            validation_result=validation_result,
            rule_summary=rule_summary
        )
    
    def _generate_issues_summary(self, issues: List[ValidationIssue]) -> str:
        """
        Generate a summary of validation issues
        
        Args:
            issues: List of validation issues
            
        Returns:
            Summary of issues in natural language
        """
        error_count = sum(1 for issue in issues if issue.severity == "error")
        warning_count = sum(1 for issue in issues if issue.severity == "warning")
        info_count = sum(1 for issue in issues if issue.severity == "info")
        
        summary = f"Rule validation found {error_count} errors, {warning_count} warnings, and {info_count} info messages."
        
        if error_count > 0:
            summary += " The rule is invalid and needs correction."
        elif warning_count > 0:
            summary += " The rule may require improvements but is technically valid."
        else:
            summary += " The rule appears to be well-formed."
            
        return summary
    
    async def _generate_rule_summary(self, rule: Rule) -> str:
        """
        Generate a natural language summary of the rule using LLM
        
        Args:
            rule: The rule to summarize
            
        Returns:
            Natural language summary of the rule
        """
        # Create a prompt for the LLM
        prompt = f"""
        Summarize the following rule in natural language:
        
        Rule name: {rule.name}
        Rule description: {rule.description}
        Conditions: {rule.conditions}
        Actions: {rule.actions}
        Priority: {rule.priority}
        Enabled: {rule.enabled}
        
        Provide a clear, concise summary of what this rule does, when it applies, and what actions it takes.
        """
        
        system_message = "You are an expert in rule systems. Your task is to explain rules in clear, natural language."
        
        try:
            response = await self.llm_service.call_llm(prompt, system_message)
            return response
        except Exception:
            # Fallback to basic summary if LLM call fails
            return f"This rule ({rule.name}) {rule.description} with {len(rule.conditions)} conditions and {len(rule.actions)} actions. Priority: {rule.priority}." 