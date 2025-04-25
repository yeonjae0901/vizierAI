<template>
  <div class="rule-editor">
    <h2>룰 에디터</h2>
    <p class="description">자연어 설명을 입력하면 AI가 룰을 생성합니다.</p>
    
    <div class="card">
      <form @submit.prevent="generateRule">
        <div class="form-group">
          <label for="description">룰 설명:</label>
          <textarea 
            id="description"
            v-model="ruleDescription"
            rows="5"
            placeholder="예시: 주문 금액이 100,000원 이상이면 5% 할인을 적용하고, 1,000,000원 이상이면 10% 할인을 적용한다"
            required
          ></textarea>
        </div>
        
        <div class="form-group">
          <label for="additional-context">추가 컨텍스트 (선택사항):</label>
          <textarea 
            id="additional-context"
            v-model="additionalContext"
            rows="3"
            placeholder="룰에 대한 추가 정보를 입력하세요 (선택사항)"
          ></textarea>
        </div>
        
        <div class="form-actions">
          <button type="submit" class="btn btn-primary" :disabled="isLoading">
            {{ isLoading ? '생성 중...' : '룰 생성하기' }}
          </button>
        </div>
      </form>
    </div>
    
    <div v-if="error" class="error-message card">
      <h3>오류 발생</h3>
      <p>{{ error }}</p>
    </div>
    
    <div v-if="generatedRule" class="generated-rule card">
      <div class="rule-header">
        <h3>생성된 룰</h3>
        <div class="button-group">
          <button class="btn btn-secondary" @click="validateRule">유효성 검사</button>
          <button class="btn btn-primary" @click="checkRule">룰 체크</button>
        </div>
      </div>
      
      <div class="explanation">
        <h4>AI 설명:</h4>
        <p>{{ generatedExplanation }}</p>
      </div>
      
      <div class="rule-json">
        <h4>룰 JSON:</h4>
        <pre><code>{{ JSON.stringify(generatedRule, null, 2) }}</code></pre>
      </div>
    </div>
    
    <div v-if="ruleReport" class="rule-report card">
      <h3>룰 오류 검토 보고서</h3>
      <div v-if="isLoadingReport" class="loading-indicator">
        보고서 생성 중...
      </div>
      <div v-else class="report-content">
        <div v-html="renderedReport"></div>
        
        <div class="report-actions">
          <button class="btn btn-outline" @click="copyReportToClipboard">
            보고서 복사
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, computed } from 'vue'
import apiService from '../services/apiService'
import type { Rule, RuleGenerationResponse } from '../types/rule'
// @ts-ignore
import * as marked from 'marked'

export default defineComponent({
  name: 'RuleEditor',
  setup() {
    const ruleDescription = ref('')
    const additionalContext = ref('')
    const isLoading = ref(false)
    const error = ref<string | null>(null)
    const generatedRule = ref<Rule | null>(null)
    const generatedExplanation = ref('')
    
    const ruleReport = ref<string | null>(null)
    const isLoadingReport = ref(false)
    
    const renderedReport = computed(() => {
      if (!ruleReport.value) return ''
      
      try {
        return marked(ruleReport.value)
      } catch (err) {
        console.error('마크다운 변환 오류:', err)
        return ruleReport.value
      }
    })
    
    const generateRule = async () => {
      if (!ruleDescription.value.trim()) {
        error.value = '룰 설명을 입력해주세요.'
        return
      }
      
      error.value = null
      isLoading.value = true
      
      try {
        const response = await apiService.generateRule({
          description: ruleDescription.value,
          additional_context: additionalContext.value || undefined
        })
        
        generatedRule.value = response.rule
        generatedExplanation.value = response.explanation
      } catch (err: any) {
        error.value = err.message || '룰 생성 중 오류가 발생했습니다.'
        generatedRule.value = null
      } finally {
        isLoading.value = false
      }
    }
    
    const validateRule = async () => {
      if (!generatedRule.value) return
      
      try {
        alert('유효성 검사 페이지로 이동하세요.')
      } catch (err: any) {
        error.value = err.message || '오류가 발생했습니다.'
      }
    }
    
    const checkRule = async () => {
      if (!generatedRule.value) return
      
      isLoadingReport.value = true
      ruleReport.value = null
      error.value = null
      
      try {
        const response = await apiService.generateRuleReport({
          rule_json: generatedRule.value
        })
        
        ruleReport.value = response.report
      } catch (err: any) {
        error.value = err.message || '리포트 생성 중 오류가 발생했습니다.'
      } finally {
        isLoadingReport.value = false
      }
    }
    
    const copyReportToClipboard = () => {
      if (!ruleReport.value) return
      
      navigator.clipboard.writeText(ruleReport.value)
        .then(() => {
          alert('보고서가 클립보드에 복사되었습니다.')
        })
        .catch(err => {
          console.error('클립보드 복사 오류:', err)
          alert('보고서 복사에 실패했습니다.')
        })
    }
    
    return {
      ruleDescription,
      additionalContext,
      isLoading,
      error,
      generatedRule,
      generatedExplanation,
      generateRule,
      validateRule,
      ruleReport,
      isLoadingReport,
      renderedReport,
      checkRule,
      copyReportToClipboard
    }
  }
})
</script>

<style scoped>
.rule-editor {
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

.generated-rule {
  margin-top: 2rem;
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.explanation {
  margin-bottom: 1.5rem;
}

.rule-json {
  background-color: #f8fafc;
  border-radius: 0.375rem;
  padding: 1rem;
  overflow: auto;
}

pre {
  margin: 0;
  white-space: pre-wrap;
}

code {
  font-family: 'Fira Code', monospace;
  font-size: 0.875rem;
}

.rule-report {
  margin-top: 2rem;
  background-color: #f8fafc;
}

.report-content {
  padding: 1rem;
}

.loading-indicator {
  padding: 2rem;
  text-align: center;
  color: var(--secondary-color);
}

.report-actions {
  margin-top: 1.5rem;
  display: flex;
  justify-content: flex-end;
}

.button-group {
  display: flex;
  gap: 0.5rem;
}

:deep(h1) {
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

:deep(h2) {
  font-size: 1.25rem;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

:deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 1rem 0;
}

:deep(th), :deep(td) {
  border: 1px solid #ddd;
  padding: 0.5rem;
  text-align: left;
}

:deep(th) {
  background-color: #f1f5f9;
}

:deep(pre) {
  background-color: #f1f1f1;
  padding: 0.75rem;
  border-radius: 0.25rem;
  overflow-x: auto;
}

:deep(code) {
  font-family: 'Fira Code', monospace;
  font-size: 0.875rem;
}
</style> 