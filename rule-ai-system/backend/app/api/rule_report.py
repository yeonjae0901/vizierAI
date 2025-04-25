from fastapi import APIRouter, HTTPException
from app.models.report import RuleReportRequest, RuleReportResponse
from app.services.rule_report_service import RuleReportService

router = APIRouter()

@router.post("/report", response_model=RuleReportResponse)
async def generate_rule_report(request: RuleReportRequest):
    """
    룰 JSON에 대한 상세 분석 리포트 생성
    
    - **rule_json**: 분석할 룰 JSON 객체
    - **include_markdown**: 마크다운 형식으로 반환할지 여부
    
    Returns:
        마크다운/HTML 형식의 리포트와 룰 메타데이터
    """
    try:
        report_service = RuleReportService()
        result = await report_service.generate_report(request.rule_json)
        
        return RuleReportResponse(
            report=result["report"],
            rule_id=result["rule_id"],
            rule_name=result["rule_name"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"리포트 생성 중 오류 발생: {str(e)}"
        ) 