import uuid
from typing import Optional, Dict, Any
from app.models.rule import Rule, RuleGenerationResponse
from app.services.llm_service import LLMService

class RuleGeneratorService:
    """Service for generating rules from natural language descriptions"""
    
    def __init__(self):
        """Initialize rule generator service"""
        self.llm_service = LLMService()
    
    async def generate_rule(self, description: str, additional_context: Optional[str] = None) -> RuleGenerationResponse:
        """
        Generate a rule from natural language description
        
        Args:
            description: Natural language description of the rule
            additional_context: Optional additional context for the rule
            
        Returns:
            RuleGenerationResponse with generated rule and explanation
        """
        # Prepare the prompt for LLM
        prompt = self._prepare_prompt(description, additional_context)
        
        # System message for rule generation
        system_message = """
        You are an expert system that converts natural language descriptions into JSON rule definitions.
        Your task is to analyze the user's description and create a structured rule with conditions and actions.
        Always respond with valid JSON containing a 'rule' object and an 'explanation' field.
        The rule should follow the structure defined in the Rule model with name, description, conditions, and actions.
        """
        
        # Generate rule using LLM
        response_data = await self.llm_service.generate_json(prompt, system_message)
        
        # Ensure the rule has an ID
        if "rule" in response_data and response_data["rule"]:
            if not response_data["rule"].get("id"):
                response_data["rule"]["id"] = str(uuid.uuid4())
        
        # Create response object
        try:
            rule = Rule(**response_data.get("rule", {}))
            explanation = response_data.get("explanation", "No explanation provided")
            
            return RuleGenerationResponse(
                rule=rule,
                explanation=explanation
            )
        except Exception as e:
            raise ValueError(f"Failed to create rule from LLM response: {str(e)}")
    
    def _prepare_prompt(self, description: str, additional_context: Optional[str] = None) -> str:
        """
        Prepare the prompt for LLM
        
        Args:
            description: Natural language description of the rule
            additional_context: Optional additional context for the rule
            
        Returns:
            Formatted prompt for LLM
        """
        prompt = f"""
        Generate a rule based on the following description:
        
        {description}
        """
        
        if additional_context:
            prompt += f"""
            
            Additional context:
            {additional_context}
            """
        
        prompt += """
        
        Respond with a JSON object containing:
        1. A 'rule' field with the following structure:
           - name: Name of the rule
           - description: Description of the rule (same as input)
           - conditions: Array of condition objects, each with 'field', 'operator', and 'value'
           - actions: Array of action objects, each with 'action_type' and 'parameters'
           - priority: Number indicating priority (default 1)
           - enabled: Boolean indicating if rule is enabled (default true)
        2. An 'explanation' field with your reasoning about how you created the rule
        
        Ensure all JSON is valid and follows the required structure.
        """
        
        return prompt 