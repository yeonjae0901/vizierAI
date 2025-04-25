import axios from 'axios';
import type {
  Rule,
  RuleGenerationRequest,
  RuleGenerationResponse,
  RuleValidationRequest,
  RuleValidationResponse,
  RuleReportRequest,
  RuleReportResponse
} from '../types/rule';

// API 설정
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// API 오류 핸들러
const handleApiError = (error: any): never => {
  console.error('API Error:', error);
  
  let errorMessage = 'API 요청 중 오류가 발생했습니다';
  
  if (error.response) {
    // 서버에서 응답한 오류
    const serverError = error.response.data;
    errorMessage = serverError.detail || `서버 오류: ${error.response.status}`;
  } else if (error.request) {
    // 요청은 보냈지만 응답이 없는 경우
    errorMessage = '서버에서 응답이 없습니다. 네트워크를 확인해주세요.';
  }
  
  throw new Error(errorMessage);
};

// API 서비스
export default {
  // 룰 생성 API
  async generateRule(request: RuleGenerationRequest): Promise<RuleGenerationResponse> {
    try {
      const response = await apiClient.post<RuleGenerationResponse>('/api/v1/rules/generate', request);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  },
  
  // 룰 검증 API
  async validateRule(request: RuleValidationRequest): Promise<RuleValidationResponse> {
    try {
      // 원래의 Rule 형식을 사용하는 경우
      if ('rule' in request) {
        const response = await apiClient.post<RuleValidationResponse>('/api/v1/rules/validate', request);
        return response.data;
      } 
      // 원본 JSON 포맷을 사용하는 경우
      else if ('rule_json' in request) {
        const response = await apiClient.post<RuleValidationResponse>('/api/v1/rules/validate-json', request);
        return response.data;
      }
      // 호환성을 위해 request가 rule을 포함하지 않는 경우
      else {
        const response = await apiClient.post<RuleValidationResponse>('/api/v1/rules/validate-json', { rule_json: request });
        return response.data;
      }
    } catch (error) {
      return handleApiError(error);
    }
  },
  
  // 룰 리포트 생성 API
  async generateRuleReport(request: RuleReportRequest): Promise<RuleReportResponse> {
    try {
      const response = await apiClient.post<RuleReportResponse>('/api/v1/rules/report', request);
      return response.data;
    } catch (error) {
      return handleApiError(error);
    }
  }
}; 