import json
import os
from typing import Dict, Any, List, Optional
from openai import OpenAI
from app.config import settings

class LLMService:
    """Service for interacting with LLM"""
    
    def __init__(self):
        """Initialize LLM service with API key from settings"""
        api_key = os.environ.get("OPENAI_API_KEY") or settings.OPENAI_API_KEY
        print(f"LLM 서비스 초기화 - API 키 존재: {bool(api_key)}, 길이: {len(api_key if api_key else '')}")
        # 키가 있을 경우에만 클라이언트 초기화
        self.client = OpenAI(api_key=api_key) if api_key else None
        self.model = os.environ.get("LLM_MODEL") or settings.LLM_MODEL
        print(f"사용 모델: {self.model}")
    
    async def call_llm(self, prompt: str, system_message: str = None) -> str:
        """
        Call LLM with prompt and optional system message
        
        Args:
            prompt: User prompt to send to LLM
            system_message: Optional system message for context
            
        Returns:
            LLM response as string
        """
        api_key = os.environ.get("OPENAI_API_KEY") or settings.OPENAI_API_KEY
        if not api_key or not self.client:
            print("API 키가 없어 기본 오류 응답 사용")
            return "API 키가 설정되어 있지 않습니다. 환경변수 또는 설정 파일에 API 키를 설정하세요."
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            print(f"OpenAI API 호출 중... 모델: {self.model}")
            # API 호출
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=2000
            )
            result = response.choices[0].message.content
            print(f"OpenAI 응답 성공: {result[:50]}...")
            return result
        except Exception as e:
            print(f"LLM API 오류 상세: {str(e)}")
            return f"API 호출 중 오류가 발생했습니다: {str(e)}"
    
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
            print(f"JSON 파싱 오류: {str(e)}, 응답: {response}")
            # JSON 파싱 오류 시 기본 에러 응답 생성
            return {
                "error": "JSON 파싱 오류",
                "message": f"LLM 응답을 JSON으로 파싱할 수 없습니다: {str(e)}",
                "response": response[:200] + "..." if len(response) > 200 else response
            } 