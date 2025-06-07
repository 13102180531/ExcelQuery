<template>
  <div class="config-options-settings-view card">
    <h2>配置选项 - LLM API</h2>
    <div class="api-panels">
      <div class="api-panel">
        <h3>硅基流动API</h3>
        <div class="form-group">
          <label for="sfs-apikey">API密钥:</label>
          <input type="password" id="sfs-apikey" v-model.trim="config.siliconflow.apiKey" placeholder="您的硅基流动API密钥">
        </div>
        <div class="form-group">
          <label for="sfs-endpoint">API端点:</label>
          <input type="text" id="sfs-endpoint" v-model.trim="config.siliconflow.apiUrl" placeholder="硅基流动API的完整URL地址">
        </div>
        <div class="form-group">
          <label for="sfs-model">模型:</label>
          <select id="sfs-model" v-model="config.siliconflow.model">
            <option>Qwen/Qwen2-7B-Instruct</option>
            <option>Qwen/Qwen2-57B-A14B-Instruct</option>
            <option>deepseek-ai/DeepSeek-V2-Chat</option>
            <option>THUDM/glm-4-9b-chat</option>
            <option>01-ai/Yi-1.5-34B-Chat</option>
            <option>Qwen/Qwen3-8B</option>
          </select>
        </div>
        <div class="form-group">
          <label for="sfs-temperature">温度: {{ config.siliconflow.temperature }}</label>
          <input type="range" id="sfs-temperature" v-model.number="config.siliconflow.temperature" min="0" max="2" step="0.1">
          <span class="range-helper-text">较低的值使输出更确定 (0-2)</span>
        </div>
        <div class="form-group">
          <label for="sfs-max-tokens">最大令牌数:</label>
          <input type="number" id="sfs-max-tokens" v-model.number="config.siliconflow.maxTokens" placeholder="例如: 2048">
        </div>
      </div>

      <div class="api-panel">
        <h3>本地Ollama</h3>
        <div class="form-group">
          <label for="os-endpoint">Ollama端点:</label>
          <input type="text" id="os-endpoint" v-model.trim="config.ollama.apiUrl" placeholder="本地Ollama API的完整URL地址">
        </div>
        <div class="form-group">
          <label for="os-model">模型:</label>
          <input type="text" id="os-model" v-model.trim="config.ollama.model" placeholder="已在本地安装的Ollama模型名称">
        </div>
        <div class="form-group">
          <label for="os-temperature">温度: {{ config.ollama.temperature }}</label>
          <input type="range" id="os-temperature" v-model.number="config.ollama.temperature" min="0" max="1" step="0.1">
        </div>
          <div class="form-group">
          <label for="os-topP">Top P: {{ config.ollama.topP }}</label>
          <input type="range" id="os-topP" v-model.number="config.ollama.topP" min="0" max="1" step="0.05">
        </div>
      </div>
    </div>

    <div class="advanced-options-settings">
      <h3>当前API选择</h3>
      <div class="form-group">
        <label class="api-type-label-settings">默认API类型:</label>
        <div class="radio-group">
          <label><input type="radio" v-model="config.apiType" value="siliconflow"> 硅基流动API</label>
          <label><input type="radio" v-model="config.apiType" value="ollama"> 本地Ollama</label>
        </div>
        <span class="api-type-helper-settings">选择默认查询使用的API类型</span>
      </div>
    </div>
    <button @click="saveConfiguration" class="btn btn-primary save-config-btn">保存LLM配置</button>
    <p v-if="configStatus" :class="['status-message', configStatusType]">{{ configStatus }}</p>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';

// Re-implement config logic here, or use a global state manager (Pinia/Vuex)
const config = reactive({
  apiType: 'siliconflow',
  siliconflow: { apiKey: '', apiUrl: 'https://api.siliconflow.cn/v1/chat/completions', model: 'Qwen/Qwen2-7B-Instruct', temperature: 0.2, maxTokens: 2048 },
  ollama: { apiUrl: 'http://localhost:11434/api/chat', model: 'llama3:8b', temperature: 0.2, topP: 0.9, }
});
const configStatus = ref('');
const configStatusType = ref('');

const loadConfiguration = () => {
  const saved = localStorage.getItem('excelQueryLLMConfig'); // Use the same key
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      config.apiType = parsed.apiType || 'siliconflow';
      if (parsed.siliconflow) Object.assign(config.siliconflow, parsed.siliconflow);
      if (parsed.ollama) Object.assign(config.ollama, parsed.ollama);
    } catch (e) { console.error('Failed to parse saved LLM configuration:', e); }
  }
};

const saveConfiguration = () => {
  localStorage.setItem('excelQueryLLMConfig', JSON.stringify(config));
  configStatus.value = 'LLM配置已保存！';
  configStatusType.value = 'success';
  setTimeout(() => { configStatus.value = ''; }, 3000);
};

onMounted(() => {
  loadConfiguration();
});
</script>

<style scoped>
.config-options-settings-view {
  /* Styles from your original .config-options but as a main view */
  padding: 20px;
  background-color: #fff;
  border-radius: 8px;
}
.config-options-settings-view h2 {
    font-size: 1.6em;
    color: #34495e;
    margin-bottom: 25px;
    padding-bottom: 10px;
    border-bottom: 1px solid #eee;
}
.config-options-settings-view h3 {
    margin-top: 20px;
    margin-bottom: 15px;
    font-size: 1.2em;
    color: #2c3e50;
    border-bottom: 1px solid #f0f0f0;
    padding-bottom: 8px;
}
.api-panels { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 25px; margin-bottom: 25px; }
.api-panel { padding: 20px; border: 1px solid #e0e0e0; border-radius: 6px; background-color: #fdfdfd; }

.advanced-options-settings { margin-top: 20px; }
.form-group { margin-bottom: 18px; }
.form-group label:not(.radio-group label) { display: block; margin-bottom: 8px; font-weight: 500; font-size: 0.9em; color: #555; }
.form-group .range-helper-text { font-size: .8em; color: #777; display: block; margin-top: 5px; }
.api-type-label-settings { font-weight: 500; font-size: 0.9em; color: #555; margin-bottom: 10px; display: block; }
.radio-group { display: flex; gap: 20px; align-items: center; }
.radio-group label { font-weight: normal; font-size: 0.9em; display: flex; align-items: center; cursor: pointer; }
.radio-group input[type=radio] { margin-right: 8px; transform: scale(1); }
.api-type-helper-settings { font-size: .8em; color: #777; display: block; margin-top: 8px; }
.form-group input[type=text], .form-group input[type=password], .form-group input[type=number], .form-group select {
  width: 100%; padding: 10px 12px; border: 1px solid #ccc; border-radius: 4px;
  box-sizing: border-box; font-size: .95em; background-color: #fff;
}
.form-group input[type=range] { width: 100%; margin-top: 5px; }
.save-config-btn {
    background-color: #28a745; color: white; padding: 10px 20px; border: none;
    border-radius: 4px; cursor: pointer; font-size: 1em; font-weight: 500;
}
.save-config-btn:hover { background-color: #218838; }
.status-message { margin-top: 15px; padding: 10px; border-radius: 4px; font-size: 0.9em; }
.status-message.success { background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
.status-message.error { background-color: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
.btn { /* General button styling if needed elsewhere */
  padding: 9px 16px; border: none; border-radius: 5px; cursor: pointer;
  font-size: .95em; transition: background-color .2s ease, box-shadow .2s ease, transform .1s ease;
  font-weight: 500; text-align: center;
}
.btn-primary { background-color: #3498db; color: #fff; }
.btn-primary:hover:not(:disabled) { background-color: #2980b9; }

</style>