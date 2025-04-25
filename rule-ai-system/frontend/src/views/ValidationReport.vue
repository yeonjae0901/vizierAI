<template>
  <div class="validation-report">
    <h2>룰 검증</h2>
    <p class="description">기존 룰의 논리적 오류를 검증하고 자연어 설명을 생성합니다.</p>
    
    <div class="card">
      <form @submit.prevent="validateRule">
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
            {{ isLoading ? '검증 중...' : '룰 검증하기' }}
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
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'
import apiService from '../services/apiService'
import type { Rule, ValidationResult } from '../types/rule'

export default defineComponent({
  name: 'ValidationReport',
  setup() {
    const ruleJson = ref('')
    const isLoading = ref(false)
    const error = ref<string | null>(null)
    const validationResult = ref<ValidationResult | null>(null)
    const ruleSummary = ref<string | null>(null)
    
    const jsonError = computed(() => {
      if (!ruleJson.value) return null
      
      try {
        JSON.parse(ruleJson.value)
        return null
      } catch (err: any) {
        return 'JSON 형식이 올바르지 않습니다: ' + err.message
      }
    })
    
    const validateRule = async () => {
      if (jsonError.value) return
      
      error.value = null
      isLoading.value = true
      
      try {
        // JSON을 파싱하고 룰 객체로 변환
        const ruleData = JSON.parse(ruleJson.value) as Rule
        
        // API 호출
        const response = await apiService.validateRule({ rule: ruleData })
        
        validationResult.value = response.validation_result
        ruleSummary.value = response.rule_summary
      } catch (err: any) {
        error.value = err.message || '룰 검증 중 오류가 발생했습니다.'
        validationResult.value = null
        ruleSummary.value = null
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
      validateRule
    }
  }
})
</script>

<style scoped>
.validation-report {
  max-width: 800px;
  margin: 0 auto;
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

.validation-result {
  margin-top: 2rem;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-color);
}

.result-header.valid h3 {
  color: var(--success-color);
}

.result-header.invalid h3 {
  color: var(--danger-color);
}

.result-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.result-badge.valid {
  background-color: #dcfce7;
  color: var(--success-color);
}

.result-badge.invalid {
  background-color: #fee2e2;
  color: var(--danger-color);
}

.summary, .rule-summary {
  margin-bottom: 1.5rem;
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
  border-radius: 0.375rem;
}

.issue-item.error {
  background-color: #fee2e2;
}

.issue-item.warning {
  background-color: #fef3c7;
}

.issue-item.info {
  background-color: #e0f2fe;
}

.issue-header {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
}

.issue-badge {
  padding: 0.125rem 0.5rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-right: 0.5rem;
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

.issue-location, .issue-suggestion {
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.issue-suggestion {
  font-style: italic;
}
</style> 