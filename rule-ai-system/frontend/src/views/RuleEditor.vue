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
        <button class="btn btn-secondary" @click="validateRule">유효성 검사</button>
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
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'
import apiService from '../services/apiService'
import type { Rule, RuleGenerationResponse } from '../types/rule'

export default defineComponent({
  name: 'RuleEditor',
  setup() {
    const ruleDescription = ref('')
    const additionalContext = ref('')
    const isLoading = ref(false)
    const error = ref<string | null>(null)
    const generatedRule = ref<Rule | null>(null)
    const generatedExplanation = ref('')
    
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
        // 룰 유효성 검사 화면으로 전환하는 로직
        // 실제 구현에서는 상태 관리 라이브러리나 이벤트 버스를 통해 구현할 수 있음
        alert('유효성 검사 페이지로 이동하세요.')
      } catch (err: any) {
        error.value = err.message || '오류가 발생했습니다.'
      }
    }
    
    return {
      ruleDescription,
      additionalContext,
      isLoading,
      error,
      generatedRule,
      generatedExplanation,
      generateRule,
      validateRule
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
</style> 