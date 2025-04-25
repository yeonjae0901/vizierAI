export interface RuleCondition {
  field: string;
  operator: string;
  value: any;
}

export interface RuleAction {
  action_type: string;
  parameters: Record<string, any>;
}

export interface Rule {
  id?: string;
  name: string;
  description: string;
  conditions: RuleCondition[];
  actions: RuleAction[];
  priority: number;
  enabled: boolean;
}

export interface RuleGenerationRequest {
  description: string;
  additional_context?: string;
}

export interface RuleGenerationResponse {
  rule: Rule;
  explanation: string;
}

export interface ValidationIssue {
  severity: 'error' | 'warning' | 'info';
  message: string;
  location?: string;
  suggestion?: string;
}

export interface ValidationResult {
  valid: boolean;
  issues: ValidationIssue[];
  summary: string;
}

// 두 가지 형태의 요청을 모두 허용하는 유니온 타입
export type RuleValidationRequest = 
  | { rule: Rule } 
  | { rule_json: Record<string, any> }
  | Record<string, any>; // 호환성을 위한 추가 타입 (rule_json으로 처리됨)

export interface RuleValidationResponse {
  validation_result: ValidationResult;
  rule_summary: string;
}

export interface RuleReportRequest {
  rule_json: Record<string, any>;
  include_markdown?: boolean;
}

export interface RuleReportResponse {
  report: string;
  rule_id?: string;
  rule_name?: string;
} 