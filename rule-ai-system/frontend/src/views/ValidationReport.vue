<template>
  <div class="validation-report">
    <h2>룰 검증 및 리포트</h2>
    <p class="description">기존 룰의 논리적 오류를 검증하고 상세 리포트를 생성합니다.</p>
    
    <div class="card">
      <form @submit.prevent="generateReport">
        <div class="form-group">
          <label for="rule-json">룰 JSON:</label>
          <textarea
            id="rule-json"
            v-model="ruleJson"
            rows="10"
            placeholder="검증할 룰의 JSON을 입력하세요"
            required
          ></textarea>
          <div v-if="jsonError" class="error">{{ jsonError }}</div>
        </div>
        
        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="isLoading">
            {{ isLoading ? '처리 중...' : '룰 리포트 생성하기' }}
          </button>
        </div>
      </form>
    </div>
    
    <div v-if="error" class="error-message card">
      <h3>오류 발생</h3>
      <p>{{ error }}</p>
    </div>
    
    <div v-if="validationResult" class="validation-result card">
      <div class="result-header" :class="{ 'valid': validationResult.valid, 'invalid': !validationResult.valid }">
        <h3>{{ validationResult.valid ? '룰이 유효합니다' : '룰에 문제가 있습니다' }}</h3>
        <div class="result-badge" :class="{ 'valid': validationResult.valid, 'invalid': !validationResult.valid }">
          {{ validationResult.valid ? '유효' : '오류' }}
        </div>
      </div>
      
      <div class="summary">
        <h4>요약:</h4>
        <p>{{ validationResult.summary }}</p>
      </div>
      
      <div v-if="ruleSummary" class="rule-summary">
        <h4>룰 설명:</h4>
        <p>{{ ruleSummary }}</p>
      </div>
      
      <div v-if="validationResult.issues && validationResult.issues.length > 0" class="issues">
        <h4>발견된 문제:</h4>
        <ul class="issue-list">
          <li v-for="(issue, index) in validationResult.issues" :key="index" class="issue-item" :class="issue.severity">
            <div class="issue-header">
              <span class="issue-badge" :class="issue.severity">{{ issue.severity }}</span>
              <span class="issue-message">{{ issue.message }}</span>
            </div>
            <div v-if="issue.location" class="issue-location">
              위치: {{ issue.location }}
            </div>
            <div v-if="issue.suggestion" class="issue-suggestion">
              제안: {{ issue.suggestion }}
            </div>
          </li>
        </ul>
      </div>
    </div>
    
    <div v-if="reportResult" class="report-result card">
      <div class="result-header">
        <h3>상세 리포트</h3>
        <div v-if="reportResult.rule_name" class="rule-name">{{ reportResult.rule_name }}</div>
      </div>
      
      <div class="report-content" v-html="formattedReport"></div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'
import apiService from '../services/apiService'
import type { Rule, ValidationResult } from '../types/rule'
import { marked } from 'marked'

export default defineComponent({
  name: 'ValidationReport',
  setup() {
    const ruleJson = ref('')
    const isLoading = ref(false)
    const error = ref<string | null>(null)
    const validationResult = ref<ValidationResult | null>(null)
    const ruleSummary = ref<string | null>(null)
    const reportResult = ref<{ report: string, rule_id?: string, rule_name?: string } | null>(null)
    const formattedReport = ref<string>('')
    
    const jsonError = computed(() => {
      if (!ruleJson.value) return null
      
      try {
        JSON.parse(ruleJson.value)
        return null
      } catch (err: any) {
        return 'JSON 형식이 올바르지 않습니다: ' + err.message
      }
    })
    
    // 이모지 문자열을 실제 이모지로 변환하는 함수
    const parseEmojis = (text: string): string => {
      // 이모지 및 특수 기호 매핑
      const emojiMap: Record<string, string> = {
        ':white_check_mark:': '✅',
        ':x:': '❌',
        ':warning:': '⚠️',
        ':information_source:': 'ℹ️',
        ':bulb:': '💡',
        ':mag:': '🔍',
        ':chart_with_upwards_trend:': '📈',
        ':page_facing_up:': '📄',
        ':pushpin:': '📌',
        ':memo:': '📝',
        '#': '# ',
        '##': '## ',
        '###': '### ',
        '####': '#### ',
        '🔸': '• ',
        '✅': '✅ ',
        '❌': '❌ ',
        '⚠️': '⚠️ ',
        '💡': '💡 ',
        '📌': '📌 ',
        '📝': '📝 '
      }
      
      // 텍스트 내의 이모지 코드를 실제 이모지로 변환
      Object.entries(emojiMap).forEach(([code, emoji]) => {
        const regex = new RegExp(code.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g')
        text = text.replace(regex, emoji)
      })
      
      return text
    }
    
    // 마크다운 텍스트를 HTML로 변환하는 함수
    const renderMarkdown = (text: string): string => {
      // 이모지 파싱
      const textWithEmojis = parseEmojis(text)
      
      // 마크다운을 HTML로 변환
      return marked.parse(textWithEmojis)
    }
    
    const generateReport = async () => {
      if (jsonError.value) return
      
      error.value = null
      isLoading.value = true
      reportResult.value = null
      validationResult.value = null
      ruleSummary.value = null
      formattedReport.value = ''
      
      try {
        // JSON을 파싱
        const ruleData = JSON.parse(ruleJson.value)
        
        // 먼저 룰 검증 수행
        const validationResponse = await apiService.validateRule({ rule_json: ruleData })
        validationResult.value = validationResponse.validation_result
        ruleSummary.value = validationResponse.rule_summary
        
        // 그 다음 상세 리포트 생성
        const reportResponse = await apiService.generateRuleReport({ 
          rule_json: ruleData,
          include_markdown: true
        })
        
        reportResult.value = {
          report: reportResponse.report,
          rule_id: reportResponse.rule_id,
          rule_name: reportResponse.rule_name
        }
        
        // 마크다운 렌더링
        if (reportResponse.report) {
          formattedReport.value = renderMarkdown(reportResponse.report)
        }
      } catch (err: any) {
        error.value = err.message || '처리 중 오류가 발생했습니다.'
      } finally {
        isLoading.value = false
      }
    }
    
    return {
      ruleJson,
      isLoading,
      error,
      jsonError,
      validationResult,
      ruleSummary,
      reportResult,
      formattedReport,
      generateReport
    }
  }
})
</script>

<style scoped>
.validation-report {
  max-width: 800px;
  margin: 0 auto;
  padding-bottom: 3rem;
}

.description {
  margin-bottom: 1.5rem;
  color: var(--secondary-color);
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-actions {
  margin-top: 1.5rem;
}

.error-message {
  background-color: #fef2f2;
  border-left: 4px solid var(--danger-color);
  padding: 1rem;
  margin-top: 1.5rem;
}

.error-message h3 {
  color: var(--danger-color);
  margin-bottom: 0.5rem;
}

.card {
  background: #fff;
  border-radius: 0.8rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  padding: 1.5rem;
  margin-bottom: 2rem;
  transition: all 0.3s ease;
}

.validation-result, .report-result {
  margin-top: 2rem;
  overflow: hidden;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.result-header.valid h3 {
  color: var(--success-color);
}

.result-header.invalid h3 {
  color: var(--danger-color);
}

.result-badge {
  padding: 0.3rem 0.8rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.result-badge.valid {
  background-color: #dcfce7;
  color: #166534;
}

.result-badge.invalid {
  background-color: #fee2e2;
  color: #b91c1c;
}

.summary, .rule-summary {
  margin-bottom: 1.5rem;
  line-height: 1.6;
  padding: 1rem;
  background-color: #f9fafb;
  border-radius: 0.5rem;
}

.summary h4, .rule-summary h4 {
  margin-bottom: 0.5rem;
  font-size: 1.1rem;
  color: #1f2937;
}

.issues {
  margin-top: 1.5rem;
}

.issue-list {
  list-style-type: none;
  padding: 0;
}

.issue-item {
  padding: 1rem;
  margin-bottom: 1rem;
  border-radius: 0.6rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.05);
}

.issue-item.error {
  background-color: #fee2e2;
  border-left: 4px solid #b91c1c;
}

.issue-item.warning {
  background-color: #fef3c7;
  border-left: 4px solid #d97706;
}

.issue-item.info {
  background-color: #e0f2fe;
  border-left: 4px solid #0284c7;
}

.issue-header {
  display: flex;
  align-items: center;
  margin-bottom: 0.75rem;
}

.issue-badge {
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-right: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.issue-badge.error {
  background-color: #b91c1c;
  color: white;
}

.issue-badge.warning {
  background-color: #d97706;
  color: white;
}

.issue-badge.info {
  background-color: #0284c7;
  color: white;
}

.issue-message {
  font-weight: 500;
}

.issue-location, .issue-suggestion {
  font-size: 0.875rem;
  margin-top: 0.5rem;
  background-color: rgba(255, 255, 255, 0.5);
  padding: 0.5rem;
  border-radius: 0.4rem;
}

.issue-suggestion {
  font-style: italic;
}

/* 리포트 스타일 개선 */
.report-result {
  position: relative;
  overflow: visible;
}

.report-result::before {
  content: '';
  position: absolute;
  top: -1.5rem;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, #4f46e5, #6366f1, #818cf8);
  border-radius: 3px;
}

.report-result .result-header {
  background-color: #f8fafc;
  margin: -1.5rem -1.5rem 1.5rem -1.5rem;
  padding: 1.5rem;
  border-bottom: 1px solid #e2e8f0;
  border-radius: 0.8rem 0.8rem 0 0;
}

.report-result .result-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #334155;
}

.rule-name {
  font-size: 0.95rem;
  color: #64748b;
  font-weight: 500;
  background-color: #f1f5f9;
  padding: 0.3rem 0.6rem;
  border-radius: 0.4rem;
}

.report-content {
  line-height: 1.7;
  font-size: 0.95rem;
  color: #334155;
  padding: 0.5rem 0;
}

.report-content :deep(h1) {
  font-size: 1.5rem;
  font-weight: 700;
  margin-top: 2rem;
  margin-bottom: 1rem;
  color: #1e293b;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 0.5rem;
}

.report-content :deep(h2) {
  font-size: 1.3rem;
  font-weight: 600;
  margin-top: 1.8rem;
  margin-bottom: 0.9rem;
  color: #334155;
}

.report-content :deep(h3) {
  font-size: 1.1rem;
  font-weight: 600;
  margin-top: 1.6rem;
  margin-bottom: 0.8rem;
  color: #475569;
}

.report-content :deep(p) {
  margin-bottom: 1.2rem;
  line-height: 1.7;
}

.report-content :deep(strong) {
  font-weight: 600;
  color: #1e293b;
}

.report-content :deep(em) {
  font-style: italic;
  color: #475569;
}

.report-content :deep(ul), 
.report-content :deep(ol) {
  margin-left: 1.5rem;
  margin-bottom: 1.2rem;
  margin-top: 0.5rem;
}

.report-content :deep(li) {
  margin-bottom: 0.5rem;
}

.report-content :deep(a) {
  color: #3b82f6;
  text-decoration: underline;
  text-underline-offset: 2px;
  transition: all 0.2s;
}

.report-content :deep(a:hover) {
  color: #2563eb;
}

.report-content :deep(code) {
  background-color: #f1f5f9;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.9rem;
  color: #0f172a;
  border: 1px solid #e2e8f0;
}

.report-content :deep(pre) {
  background-color: #f8fafc;
  padding: 1.2rem;
  border-radius: 0.6rem;
  overflow-x: auto;
  margin: 1.5rem 0;
  border: 1px solid #e2e8f0;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.report-content :deep(pre code) {
  background-color: transparent;
  padding: 0;
  border: none;
  font-size: 0.9rem;
  line-height: 1.6;
  color: #334155;
}

.report-content :deep(blockquote) {
  margin: 1.5rem 0;
  padding: 0.8rem 1.2rem;
  border-left: 4px solid #818cf8;
  background-color: #f8fafc;
  color: #475569;
  font-style: italic;
  border-radius: 0 0.4rem 0.4rem 0;
}

.report-content :deep(blockquote p) {
  margin-bottom: 0;
}

.report-content :deep(hr) {
  margin: 2rem 0;
  border: 0;
  height: 1px;
  background: #e2e8f0;
}

.report-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5rem 0;
  font-size: 0.9rem;
}

.report-content :deep(th) {
  background-color: #f1f5f9;
  padding: 0.75rem 1rem;
  text-align: left;
  font-weight: 600;
  color: #334155;
  border: 1px solid #e2e8f0;
}

.report-content :deep(td) {
  padding: 0.75rem 1rem;
  border: 1px solid #e2e8f0;
  vertical-align: top;
}

.report-content :deep(tr:nth-child(even)) {
  background-color: #f8fafc;
}

.btn-primary {
  background-color: #4f46e5;
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.btn-primary:hover {
  background-color: #4338ca;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.15);
}

.btn-primary:disabled {
  background-color: #a5b4fc;
  cursor: not-allowed;
}

textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 0.5rem;
  font-size: 0.95rem;
  line-height: 1.5;
  transition: border-color 0.2s, box-shadow 0.2s;
  resize: vertical;
}

textarea:focus {
  outline: none;
  border-color: #818cf8;
  box-shadow: 0 0 0 3px rgba(129, 140, 248, 0.2);
}

.error {
  color: #dc2626;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}
</style> 