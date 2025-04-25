<template>
  <div class="app">
    <header class="header">
      <div class="container">
        <h1>Rule AI System</h1>
        <nav>
          <button 
            class="btn" 
            :class="{ 'btn-primary': activeView === 'editor', 'btn-secondary': activeView !== 'editor' }"
            @click="activeView = 'editor'"
          >
            Rule Editor
          </button>
          <button 
            class="btn ml-2" 
            :class="{ 'btn-primary': activeView === 'validation', 'btn-secondary': activeView !== 'validation' }"
            @click="activeView = 'validation'"
          >
            Rule Validation
          </button>
        </nav>
      </div>
    </header>
    
    <main class="container">
      <div v-if="activeView === 'editor'">
        <RuleEditor />
      </div>
      <div v-else-if="activeView === 'validation'">
        <ValidationReport />
      </div>
    </main>
  </div>
</template>

<script lang="ts">
import { defineComponent, ref } from 'vue'
import RuleEditor from './views/RuleEditor.vue'
import ValidationReport from './views/ValidationReport.vue'

export default defineComponent({
  name: 'App',
  components: {
    RuleEditor,
    ValidationReport
  },
  setup() {
    const activeView = ref<'editor' | 'validation'>('editor')
    
    return {
      activeView
    }
  }
})
</script>

<style>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background-color: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  padding: 1rem 0;
  margin-bottom: 2rem;
}

.header .container {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header h1 {
  font-size: 1.5rem;
  margin: 0;
}

.header nav {
  display: flex;
}

.ml-2 {
  margin-left: 0.5rem;
}

main {
  flex: 1;
  padding-bottom: 2rem;
}
</style> 