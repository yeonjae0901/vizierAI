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

export interface RuleValidationRequest {
  rule: Rule;
}

export interface RuleValidationResponse {
  validation_result: ValidationResult;
  rule_summary: string;
} 