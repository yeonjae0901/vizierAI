from typing import Dict, Any, Optional
from app.services.llm_service import LLMService
import json

class RuleReportService:
    """Service for generating rule analysis reports"""
    
    def __init__(self):
        """Initialize rule report service with LLM service"""
        self.llm_service = LLMService()
    
    async def generate_report(self, rule_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive report for the given rule
        
        Args:
            rule_json: Rule in JSON format
            
        Returns:
            Dictionary with report content and rule metadata
        """
        # 룰 메타데이터 추출
        rule_id = rule_json.get("ruleId", rule_json.get("id", "Unknown"))
        rule_name = rule_json.get("name", "Unnamed Rule")
        
        # LLM 프롬프트 생성
        prompt = self._create_report_prompt(rule_json)
        
        try:
            # LLM에 리포트 생성 요청
            report_content = await self.llm_service.call_llm(prompt, self._get_system_message())
            print(f"LLM 리포트 생성 성공: {report_content[:100]}...")
            
            return {
                "report": report_content,
                "rule_id": rule_id,
                "rule_name": rule_name
            }
        except Exception as e:
            print(f"리포트 생성 오류: {str(e)}")
            return {
                "report": self._generate_fallback_report(rule_json),
                "rule_id": rule_id,
                "rule_name": rule_name
            }
    
    def _create_report_prompt(self, rule_json: Dict[str, Any]) -> str:
        """
        Create prompt for LLM to generate rule analysis report
        
        Args:
            rule_json: Rule in JSON format
            
        Returns:
            Prompt string for LLM
        """
        # JSON을 보기 좋게 포맷팅
        rule_str = json.dumps(rule_json, indent=2, ensure_ascii=False)
        rule_id = rule_json.get("ruleId", rule_json.get("id", "Unknown"))
        rule_name = rule_json.get("name", "Unnamed Rule")
        
        # 개선된 리포트 형식 프롬프트
        prompt = f"""
다음 JSON 형식의 비즈니스 룰을 분석하고, 상세한 오류 분석 리포트를 생성해주세요.

# 분석할 룰 JSON:
```json
{rule_str}
```

# 분석 요청사항:
다음 분석 포인트를 중점적으로 검토하고, 마크다운 형식으로 상세한 리포트를 생성해주세요:
1. 조건 구조 분석 - 조건 간 논리적 관계와 계층 구조 파악
2. 중복 또는 불필요한 조건 식별
3. 자기 모순적인 조건 탐지 (같은 필드에 대한 논리적으로 충돌하는 조건)
4. 구조 복잡도 평가
5. 룰 로직 개선을 위한 제안사항

# 리포트 형식:
다음 구조로 마크다운 형식의 리포트를 생성해주세요. 각 섹션에 룰 분석 결과에 맞는 실제 내용을 채워주세요:

```markdown
# ✅ 룰 오류 검토 보고서: {rule_id} - {rule_name}

## 📌 기본 정보
- **룰 ID**: [실제 ID]
- **룰명**: [실제 이름]
- **설명**: [룰 설명]
- **우선순위**: [우선순위]

## 🧠 조건 구조 요약
- 최상단 조건: [실제 조건 연산자]
- 주요 필드: [실제 사용된 필드들]
- 조건 구조: [실제 조건 계층 구조 요약]

## 🧪 오류 검토 항목
- **형식 오류**: [있음/없음] (발견된 형식 오류 상세 설명)
- **논리 오류**: [있음/없음] (조건 겹침, 누락 가능성 등 상세 설명)
- **구조 복잡도**: [높음/중간/낮음] (구조의 복잡성 평가와 근거)
- **모순 조건**: [있음/없음] (논리적 모순이 있는 조건 상세 설명)

## 📝 요약 제안 사항
| 항목 | 점검 결과 | 제안 |
|------|------------|------|
| 조건 겹침 | ⚠️ 있음 / ✅ 없음 | [구체적인 제안 내용] |
| 누락 조건 | ⚠️ 있음 / ✅ 없음 | [구체적인 제안 내용] |
| 조건 모순 | ⚠️ 있음 / ✅ 없음 | [구체적인 제안 내용] |
| 구조 단순화 | ⚠️ 필요함 / ✅ 불필요 | [구체적인 제안 내용] |

[룰의 의도와 로직을 설명하는 자연어 요약과 주요 분석 결과 1-2문단]
```

중요: 자리표시자([실제 ID], [실제 이름] 등)를 분석한 룰의 실제 값으로 모두 대체해주세요. "✅"와 "⚠️" 이모지는 각 항목의 상태에 따라 적절히 선택해주세요.
"""
        return prompt
    
    def _get_system_message(self) -> str:
        """
        Get system message for LLM context
        
        Returns:
            System message string
        """
        return """당신은 비즈니스 규칙 시스템 전문가로서, 규칙 JSON을 분석하고 문제점을 찾아내는 데이터 분석가입니다.
당신의 역할은 규칙의 논리적 일관성, 중복, 모순, 복잡성을 철저히 분석하고 구체적인 개선 제안을 제공하는 것입니다.
전문적이고 명확한 언어로 보고서를 작성하되, 기술적 분석과 비즈니스 관점 모두를 고려해야 합니다.
발견한 모든 문제점에 대해 구체적인 위치와 이유를 설명하고, 실제적인 개선 방안을 제시해주세요."""
    
    def _generate_fallback_report(self, rule_json: Dict[str, Any]) -> str:
        """
        Generate a simple fallback report when LLM call fails
        
        Args:
            rule_json: Rule in JSON format
            
        Returns:
            Simple fallback report in markdown format
        """
        rule_id = rule_json.get("ruleId", rule_json.get("id", "Unknown"))
        rule_name = rule_json.get("name", "Unnamed Rule")
        
        return f"""# ✅ 룰 오류 검토 보고서: {rule_id} - {rule_name}

## 📌 기본 정보
- **룰 ID**: {rule_id}
- **룰명**: {rule_name}

## 🔍 분석 오류
죄송합니다. 현재 룰 분석 서비스에 일시적인 문제가 발생했습니다. 나중에 다시 시도해주세요.

## 📝 원본 룰 정보
```json
{json.dumps(rule_json, indent=2, ensure_ascii=False)}
```
""" 