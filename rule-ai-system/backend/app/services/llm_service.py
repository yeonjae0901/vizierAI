import json
import openai
from typing import Dict, Any, List, Optional
from app.config import settings

class LLMService:
    """Service for interacting with LLM"""
    
    def __init__(self):
        """Initialize LLM service with API key from settings"""
        openai.api_key = settings.OPENAI_API_KEY
        self.model = settings.LLM_MODEL
    
    async def call_llm(self, prompt: str, system_message: str = None) -> str:
        """
        Call LLM with prompt and optional system message
        
        Args:
            prompt: User prompt to send to LLM
            system_message: Optional system message for context
            
        Returns:
            LLM response as string
        """
        if not openai.api_key:
            # Mock mode for development without API key
            return self._mock_llm_response(prompt)
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=messages,
                temperature=0.2,  # Low temperature for more deterministic outputs
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            # Fallback to mock in case of API error
            print(f"LLM API Error: {str(e)}")
            return self._mock_llm_response(prompt)
    
    async def generate_json(self, prompt: str, system_message: str = None) -> Dict[str, Any]:
        """
        Generate JSON from prompt
        
        Args:
            prompt: User prompt describing what JSON to generate
            system_message: Optional system message for context
            
        Returns:
            Generated JSON as dict
        """
        if system_message is None:
            system_message = "You are a helpful assistant that generates valid JSON based on user requirements. Always respond with valid JSON only."
        
        response = await self.call_llm(prompt, system_message)
        
        # Extract JSON from response (handling cases where LLM might add markdown code blocks)
        json_str = response
        if "```json" in response:
            json_str = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            json_str = response.split("```")[1].split("```")[0].strip()
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}")
            
    def _mock_llm_response(self, prompt: str) -> str:
        """Mock LLM response for development without API key"""
        if "rule" in prompt.lower() and "generate" in prompt.lower():
            return json.dumps({
                "rule": {
                    "id": "mock-rule-123",
                    "name": "Mock Price Discount Rule",
                    "description": "Apply 10% discount for orders over $100",
                    "conditions": [
                        {
                            "field": "order_total",
                            "operator": "gt",
                            "value": 100
                        }
                    ],
                    "actions": [
                        {
                            "action_type": "apply_discount",
                            "parameters": {
                                "discount_percentage": 10
                            }
                        }
                    ],
                    "priority": 1,
                    "enabled": True
                },
                "explanation": "This is a mock rule generated for testing purposes."
            })
        elif "validate" in prompt.lower():
            return json.dumps({
                "validation_result": {
                    "valid": True,
                    "issues": [],
                    "summary": "The rule appears to be valid and well-formed."
                },
                "rule_summary": "This rule applies a 10% discount to orders over $100."
            })
        else:
            return "I'm a mock LLM service. Please provide an API key for real responses." 