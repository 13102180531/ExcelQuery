<template>
  <div class="excel-query-tool-page">
    <div class="config-section">
      <div v-if="showConfig" class="config-options">
        <h2>API配置</h2>
        <div class="api-panels">
          <div class="api-panel">
            <h3>硅基流动API</h3>
            <div class="form-group">
              <label for="sf-apikey">API密钥:</label>
              <input type="password" id="sf-apikey" v-model.trim="config.siliconflow.apiKey" placeholder="您的硅基流动API密钥">
            </div>
            <div class="form-group">
              <label for="sf-endpoint">API端点:</label>
              <input type="text" id="sf-endpoint" v-model.trim="config.siliconflow.apiUrl" placeholder="硅基流动API的完整URL地址">
            </div>
            <div class="form-group">
              <label for="sf-model">模型:</label>
              <select id="sf-model" v-model="config.siliconflow.model">
                <option>Qwen/Qwen2-7B-Instruct</option>
                <option>Qwen/Qwen2-57B-A14B-Instruct</option>
                <option>deepseek-ai/DeepSeek-V2-Chat</option>
                <option>THUDM/glm-4-9b-chat</option>
                <option>01-ai/Yi-1.5-34B-Chat</option>
                <option>Qwen/Qwen3-8B</option> {/* Added from your template */}
              </select>
            </div>
            <div class="form-group">
              <label for="sf-temperature">温度: {{ config.siliconflow.temperature }}</label>
              <input type="range" id="sf-temperature" v-model.number="config.siliconflow.temperature" min="0" max="2" step="0.1">
              <span class="range-helper-text">较低的值使输出更确定 (0-2)</span>
            </div>
            <div class="form-group">
              <label for="sf-max-tokens">最大令牌数:</label>
              <input type="number" id="sf-max-tokens" v-model.number="config.siliconflow.maxTokens" placeholder="例如: 2048">
            </div>
          </div>

          <div class="api-panel">
            <h3>本地Ollama</h3>
            <div class="form-group">
              <label for="ollama-endpoint">Ollama端点:</label>
              <input type="text" id="ollama-endpoint" v-model.trim="config.ollama.apiUrl" placeholder="本地Ollama API的完整URL地址">
            </div>
            <div class="form-group">
              <label for="ollama-model">模型:</label>
              <input type="text" id="ollama-model" v-model.trim="config.ollama.model" placeholder="已在本地安装的Ollama模型名称">
            </div>
            <div class="form-group">
              <label for="ollama-temperature">温度: {{ config.ollama.temperature }}</label>
              <input type="range" id="ollama-temperature" v-model.number="config.ollama.temperature" min="0" max="1" step="0.1">
            </div>
             <div class="form-group">
              <label for="ollama-topP">Top P: {{ config.ollama.topP }}</label>
              <input type="range" id="ollama-topP" v-model.number="config.ollama.topP" min="0" max="1" step="0.05">
            </div>
          </div>
        </div>

        <div class="advanced-options">
          <h3>高级选项</h3>
          <div class="form-group">
            <label class="api-type-label">当前API类型:</label>
            <div class="radio-group">
              <label><input type="radio" v-model="config.apiType" value="siliconflow"> 硅基流动API</label>
              <label><input type="radio" v-model="config.apiType" value="ollama"> 本地Ollama</label>
            </div>
            <span class="api-type-helper">选择当前使用的API类型</span>
          </div>
        </div>
        <button @click="saveConfiguration" class="btn btn-primary save-config-btn">保存配置</button>
        <p v-if="configStatus" :class="['status-message', configStatusType]">{{ configStatus }}</p> {/* Added configStatusType binding */}
      </div>
    </div>

    <main class="main-content">
      <div class="actions-panel">
        <section class="action-step">
          <h2>1. 上传Excel文件</h2>
          <input type="file" @change="handleFileSelection" accept=".xlsx, .xls" ref="fileInputRef" multiple style="display: none;">
          <div class="file-upload-controls">
            <button @click="triggerFileInput" :disabled="isUploading" class="btn btn-outline">
              选择文件 (可多选)
            </button>
            <button @click="uploadAndProcess" :disabled="!selectedFilesForUpload.length || isUploading" class="btn btn-success">
              <span v-if="isUploading" class="loader-small"></span>
              {{ isUploading ? '上传中...' : '上传并处理文件' }}
            </button>
          </div>
          <div v-if="selectedFilesForUpload.length > 0" class="selected-files-list">
            <strong>已选择文件:</strong>
            <ul>
              <li v-for="file in selectedFilesForUpload" :key="file.name">
                {{ file.name }} ({{ (file.size / 1024).toFixed(2) }} KB)
              </li>
            </ul>
          </div>
          <p v-if="fileInfo" class="file-info">{{ fileInfo }}</p>
          <p v-if="uploadStatus.message" :class="['status-message', uploadStatus.type]">{{ uploadStatus.message }}</p>
          <div v-if="columnsInfoHtml" class="columns-display" v-html="columnsInfoHtml"></div>
        </section>

        <section class="action-step">
          <h2>2. 输入自然语言查询</h2>
          <textarea v-model.trim="naturalQuery" placeholder="例如：找出所有销售额大于1000且利润率高于20%的记录"></textarea>
          <div class="query-buttons">
            <button @click="executeQuery" :disabled="isQuerying || !isFileUploaded" class="btn btn-primary">
              <span v-if="isQuerying" class="loader-small"></span>
              {{ isQuerying ? '查询中...' : '执行查询' }}
            </button>
            <button @click="downloadResults" :disabled="isDownloading || !results.length" class="btn btn-info">
              <span v-if="isDownloading" class="loader-small"></span>
              {{ isDownloading ? '下载中...' : '下载结果' }}
            </button>
          </div>
          <p v-if="queryStatus.message" :class="['status-message', queryStatus.type]">{{ queryStatus.message }}</p>
        </section>
      </div>

      <div class="results-panel">
        <h2>查询结果</h2>
         <div v-if="parsedConditions" class="parsed-conditions-display"> {/* Your parsed conditions display */}
          <strong>LLM解析条件:</strong>
          <pre>{{ JSON.stringify(parsedConditions, null, 2) }}</pre>
        </div>
        <div v-if="!isFileUploaded && !isQuerying && !isUploading && results.length === 0" class="status-message info initial-message">
          请先上传并处理Excel文件。
        </div>
        <div v-else-if="isFileUploaded && !results.length && !isQuerying && queryAttempted === false" class="status-message info initial-message">
          文件已上传，请输入自然语言查询并执行。
        </div>
        <div v-else-if="isFileUploaded && results.length === 0 && queryAttempted === true && !isQuerying" class="status-message warning">
          没有找到匹配的记录。
        </div>

        <div v-if="results.length > 0" class="results-table-container">
          <p class="results-count">找到 {{ results.length }} 条记录。</p>
          <table class="results-table">
            <thead>
              <tr>
                <th v-for="header_col in tableHeaders" :key="header_col">{{ header_col }}</th> {/* Changed to tableHeaders */}
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, rowIndex) in results" :key="rowIndex">
                <td v-for="header_col in tableHeaders" :key="header_col + rowIndex" :title="String(row[header_col] == null ? '' : row[header_col])"> {/* Added null/undefined check */}
                  {{ formatCellContent(row[header_col]) }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'; // watch removed as not used
import axios from 'axios';

const FASTAPI_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1/excel';

const props = defineProps({
  currentUsername: {
    type: String,
    default: '用户' // More generic default
  }
});

const emit = defineEmits(['user-logout']);

// --- Config State ---
const showConfig = ref(false);
const config = reactive({
  apiType: 'siliconflow',
  siliconflow: {
    apiKey: '',
    apiUrl: 'https://api.siliconflow.cn/v1/chat/completions',
    model: 'Qwen/Qwen2-7B-Instruct',
    temperature: 0.2,
    maxTokens: 2048
  },
  ollama: {
    apiUrl: 'http://localhost:11434/api/chat',
    model: 'llama3:8b', // Example, user can change
    temperature: 0.2,
    topP: 0.9,
  }
});
const configStatus = ref('');
const configStatusType = ref(''); // To bind class for success/error

// --- File Upload State ---
const fileInputRef = ref(null);
const selectedFilesForUpload = ref([]); // Files selected by user via input
const isUploading = ref(false);
const fileInfo = ref(''); // Summary after successful upload
const uploadStatus = reactive({ message: '', type: '', timeoutId: null }); // type: 'success', 'error', 'warning', 'info'
const columnsInfoHtml = ref(''); // For displaying column names from backend
const isFileUploaded = ref(false); // Set to true after a successful upload processing

// --- Query State ---
const naturalQuery = ref('');
const isQuerying = ref(false);
const queryStatus = reactive({ message: '', type: '', timeoutId: null });
const parsedConditions = ref(null);
const results = ref([]);
const queryAttempted = ref(false); // To differentiate no results from not yet queried
const tableHeaders = computed(() => (results.value.length > 0 ? Object.keys(results.value[0]) : []));
const isDownloading = ref(false);

// --- Methods ---
const logout = () => {
  emit('user-logout');
};

const toggleConfig = () => {
  showConfig.value = !showConfig.value;
};

const saveConfiguration = () => {
  localStorage.setItem('excelQueryLLMConfig', JSON.stringify(config));
  configStatus.value = 'API配置已保存！';
  configStatusType.value = 'success'; // For styling
  setTimeout(() => { configStatus.value = ''; }, 3000);
};

onMounted(() => {
  const savedConfig = localStorage.getItem('excelQueryLLMConfig');
  if (savedConfig) {
    try {
      const parsed = JSON.parse(savedConfig);
      config.apiType = parsed.apiType || 'siliconflow';
      if (parsed.siliconflow) Object.assign(config.siliconflow, parsed.siliconflow);
      if (parsed.ollama) Object.assign(config.ollama, parsed.ollama);
    } catch (e) { console.error('Failed to parse saved LLM configuration:', e); }
  }
});

const triggerFileInput = () => {
  fileInputRef.value?.click(); // Optional chaining
};

const handleFileSelection = (event) => {
  selectedFilesForUpload.value = Array.from(event.target.files);
  if (selectedFilesForUpload.value.length === 0) {
    fileInfo.value = '';
  }
  // Reset relevant states for a new selection
  setStatusMessage(uploadStatus, '', '', 0);
  isFileUploaded.value = false;
  results.value = [];
  parsedConditions.value = null;
  setStatusMessage(queryStatus, '', '', 0);
  queryAttempted.value = false;
  columnsInfoHtml.value = '';
};

const getAuthHeaders = () => {
  const token = localStorage.getItem('authToken');
  if (token) return { Authorization: `Bearer ${token}` };
  console.error("Auth token missing.");
  emit('user-logout');
  throw new Error("用户未认证，请先登录。");
};

const setStatusMessage = (statusRef, message, type, duration = 4000) => {
  statusRef.message = message;
  statusRef.type = type; // 'success', 'error', 'warning', 'info'
  if (statusRef.timeoutId) clearTimeout(statusRef.timeoutId);
  if (duration > 0 && message) { // Only set timeout if there's a message
    statusRef.timeoutId = setTimeout(() => {
      statusRef.message = '';
      statusRef.type = '';
    }, duration);
  } else if (!message) { // If message is cleared, clear type too
    statusRef.type = '';
  }
};


const resetForNewUpload = () => {
    fileInfo.value = '';
    columnsInfoHtml.value = '';
    results.value = [];
    parsedConditions.value = null;
    queryAttempted.value = false;
    isFileUploaded.value = false; // Reset this specifically
    setStatusMessage(uploadStatus, '', '', 0);
    setStatusMessage(queryStatus, '', '', 0);
};

const uploadAndProcess = async () => {
  if (selectedFilesForUpload.value.length === 0) {
    setStatusMessage(uploadStatus, '请选择文件上传。', 'warning');
    return;
  }
  isUploading.value = true;
  resetForNewUpload(); // Reset before new upload attempt
  setStatusMessage(uploadStatus, '正在上传和处理文件...', 'info', 0);

  const formData = new FormData();
  for (const file of selectedFilesForUpload.value) {
    formData.append('files', file);
  }

  try {
    const headers = getAuthHeaders(); // Throws and emits logout if no token
    const response = await axios.post(`${FASTAPI_BASE_URL}/upload`, formData, { headers });

    if (response.data.success) {
      isFileUploaded.value = true;
      const message = `文件处理成功！共 ${response.data.total_records} 条记录。已上传文件: ${response.data.files.join(', ')}`;
      setStatusMessage(uploadStatus, message, 'success', 0); // Keep success message
      fileInfo.value = `当前数据包含 ${response.data.total_records} 条记录。`;

      if (response.data.columns && response.data.columns.length > 0) {
        let html = '<strong>可用列名 (已规范化):</strong><ul>';
        response.data.columns.forEach(col => { html += `<li>${col}</li>`; });
        html += '</ul>';
        columnsInfoHtml.value = html;
      }
    } else {
      // Handle cases where backend might return success: false with a message
      setStatusMessage(uploadStatus, response.data.message || '文件处理失败，未知原因。', 'error', 0);
      isFileUploaded.value = false;
    }
  } catch (error) {
    console.error("Upload error:", error);
    isFileUploaded.value = false;
    if (error.message !== "用户未认证，请先登录。") { // Avoid double message if getAuthHeaders handled it
        if (error.response && error.response.data && error.response.data.detail) {
            setStatusMessage(uploadStatus, `文件上传错误: ${error.response.data.detail}`, 'error', 0);
        } else {
            setStatusMessage(uploadStatus, `文件上传请求失败: ${error.message || '请检查网络或服务器状态。'}`, 'error', 0);
        }
    }
  } finally {
    isUploading.value = false;
    // Do not clear selectedFilesForUpload here, user might want to retry without re-selecting
    // if (fileInputRef.value) fileInputRef.value.value = ''; // This would clear it
  }
};

const executeQuery = async () => {
  if (!naturalQuery.value.trim()) {
    setStatusMessage(queryStatus, '请输入自然语言查询语句。', 'warning'); return;
  }
  if (!isFileUploaded.value) {
    setStatusMessage(queryStatus, '请先成功上传并处理Excel文件。', 'warning'); return;
  }
  isQuerying.value = true;
  setStatusMessage(queryStatus, '正在查询，请稍候...', 'info', 0);
  results.value = [];
  parsedConditions.value = null;
  queryAttempted.value = true;


  const llmConfigPayload = {
    apiType: config.apiType,
    [config.apiType]: { ...config[config.apiType] }
  };

  try {
    const headers = getAuthHeaders();
    const response = await axios.post(`${FASTAPI_BASE_URL}/query`, {
        query: naturalQuery.value,
        config: llmConfigPayload
    }, { headers });

    parsedConditions.value = response.data.parsed_conditions;
    results.value = response.data.results;

    if (results.value.length === 0) {
      setStatusMessage(queryStatus, '没有找到匹配的记录。', 'warning', 0);
    } else {
      setStatusMessage(queryStatus, `查询成功，找到 ${results.value.length} 条记录。 (源文件: ${response.data.source_files.join(', ')})`, 'success');
    }
  } catch (error) {
    console.error("Query error:", error);
    parsedConditions.value = { query: naturalQuery.value, error: error.message }; // Show error in parsed conditions
    results.value = []; // Ensure results are cleared on error
    if (error.message !== "用户未认证，请先登录。") {
        if (error.response && error.response.data && error.response.data.detail) {
            setStatusMessage(queryStatus, `查询请求失败: ${error.response.data.detail}`, 'error', 0);
        } else {
            setStatusMessage(queryStatus, `查询请求失败: ${error.message || '请检查网络或服务器状态。'}`, 'error', 0);
        }
    }
  } finally {
    isQuerying.value = false;
  }
};

const downloadResults = async () => {
  if (!results.value.length && !naturalQuery.value.trim()) {
     setStatusMessage(queryStatus, '没有可下载的结果或查询条件。', 'warning'); return;
  }
  isDownloading.value = true;
  setStatusMessage(queryStatus, '正在准备下载...', 'info', 0);

  const llmConfigPayload = {
    apiType: config.apiType,
    [config.apiType]: { ...config[config.apiType] }
  };

  const payload = {
    query: results.value.length && parsedConditions.value ? undefined : naturalQuery.value.trim(), // Send query only if no prior successful query that yielded results
    parsed_conditions: parsedConditions.value, // Send current parsed conditions if available
    config: llmConfigPayload
  };
   if (!payload.query && !payload.parsed_conditions) {
    setStatusMessage(queryStatus, '没有有效的查询条件用于下载。', 'warning');
    isDownloading.value = false;
    return;
  }


  try {
    const headers = getAuthHeaders();
    const response = await axios.post(`${FASTAPI_BASE_URL}/download`, payload, {
        headers,
        responseType: 'blob'
    });

    const blob = await response.data; // Axios already gives blob if responseType is 'blob'
    const contentDisposition = response.headers['content-disposition'];
    let filename = "query_results.xlsx";
    if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename\*?=['"]?(?:UTF-\d['"]*)?([^;\r\n"']*)['"]?;?/i);
        if (filenameMatch && filenameMatch[1]) filename = decodeURIComponent(filenameMatch[1]);
    }

    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
    setStatusMessage(queryStatus, '结果文件已开始下载。', 'success');
  } catch (error) {
    console.error("Download error:", error);
     if (error.message !== "用户未认证，请先登录。") {
        if (error.response && error.response.data) {
            try {
                // Axios error.response.data for blob might already be the blob if error, or an object if JSON
                let errorDetail = '下载失败，无法解析错误。';
                if (error.response.data instanceof Blob && error.response.headers['content-type'] === 'application/json') {
                    const errorText = await error.response.data.text();
                    const errorJson = JSON.parse(errorText);
                    errorDetail = errorJson.detail || '无法生成文件';
                } else if (error.response.data.detail) { // If already parsed as JSON by Axios
                    errorDetail = error.response.data.detail;
                }
                setStatusMessage(queryStatus, `下载请求失败: ${errorDetail}`, 'error', 0);
            } catch (parseError) {
                setStatusMessage(queryStatus, '下载请求失败: 无法解析服务器错误。', 'error', 0);
            }
        } else {
            setStatusMessage(queryStatus, `下载请求失败: ${error.message || '请检查网络或服务器状态。'}`, 'error', 0);
        }
    }
  } finally {
    isDownloading.value = false;
  }
};

const formatCellContent = (content) => {
  if (content === null || content === undefined) return '';
  const strContent = String(content);
  return strContent.length > 100 ? strContent.substring(0, 100) + '...' : strContent;
};

</script>

<style scoped>
/* Root container ensuring it tries to take full page provided by App.vue */
.excel-query-tool-page {
  display: flex;
  flex-direction: column;
  height: 100%; /* Fill parent's height */
  width: 100%;  /* Fill parent's width */
  overflow: hidden; /* This main container does not scroll */
  background-color: #f4f7f6;
  color: #333;
  box-sizing: border-box;
}

/* Your provided header styles */
.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 25px; /* Consistent padding */
  background-color: #2c3e50; /* Darker, professional header */
  color: white;
  flex-shrink: 0; /* Header should not shrink */
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  /* position: sticky; top: 0; z-index: 1000; -- Optional for sticky header */
}
.app-header h1 {
  margin: 0;
  font-size: 1.6em; /* Slightly larger */
  font-weight: 500;
}
.user-info {
  display: flex;
  align-items: center;
  font-size: 0.95em;
}
.user-info span {
  margin-right: 15px;
  color: #ecf0f1; /* Lighter color for username */
}
.btn-link {
  background: none;
  border: 1px solid #7f8c8d; /* Subtle border */
  color: #ecf0f1;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 4px;
  text-decoration: none;
  font-size: 0.9em;
  transition: background-color 0.2s, color 0.2s;
}
.btn-link:hover {
  background-color: #e74c3c; /* Red hover for logout */
  border-color: #e74c3c;
  color: white;
}

/* Config section directly under header, not part of main scrollable content */
.config-section {
  padding: 15px 25px;
  background-color: #ffffff; /* White background for config */
  border-bottom: 1px solid #e0e0e0;
  flex-shrink: 0; /* Config section should not shrink */
  /* overflow-y: auto; -- If config itself needs to scroll, but generally it's of fixed height */
  /* max-height: 40vh; -- Example if you want to limit config height and make it scrollable */
}
.toggle-config-btn {
  margin-bottom: 10px;
}
.config-options {
  margin-top: 5px;
  padding: 15px;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #fdfdfd;
}
.api-panels { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; margin-bottom: 20px; }
.api-panel { padding: 15px; border: 1px solid #e0e0e0; border-radius: 6px; background-color: #fff; }
.advanced-options { margin-top: 15px; }
.form-group { margin-bottom: 12px; }
.form-group label:not(.radio-group label) { display: block; margin-bottom: 6px; font-weight: 600; font-size: .9em; color: #555; }
.form-group .range-helper-text { font-size: .8em; color: #777; display: block; margin-top: 4px; }
.form-group .api-type-label { font-weight: 600; font-size: .9em; color: #555; margin-bottom: 8px; }
.radio-group { display: flex; gap: 15px; align-items: center; }
.radio-group label { font-weight: normal; font-size: .9em; display: flex; align-items: center; cursor: pointer; }
.radio-group input[type=radio] { margin-right: 6px; transform: scale(.9); }
.api-type-helper { font-size: .8em; color: #777; display: block; margin-top: 6px; }
.form-group input[type=text], .form-group input[type=password], .form-group input[type=number], .form-group select {
  width: 100%; padding: 9px 12px; border: 1px solid #ccc; border-radius: 4px;
  box-sizing: border-box; font-size: .95em; background-color: #fff;
}
.form-group input[type=range] { width: 100%; margin-top: 5px; }
.save-config-btn { margin-top: 10px; }

/* Main content area that holds action panels and results, this part scrolls */
.main-content {
  display: flex; /* For side-by-side panels */
  flex-grow: 1; /* Takes remaining vertical space */
  padding: 20px 25px 25px 25px; /* Padding around the panels */
  gap: 25px; /* Space between action and results panels */
  overflow: hidden; /* Main content itself does not scroll, its children do */
  width: 100%;
  box-sizing: border-box;
}

.actions-panel, .results-panel {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 3px 10px rgba(0,0,0,0.07);
  padding: 20px;
  display: flex;
  flex-direction: column;
  overflow-y: auto; /* These panels scroll independently */
}
.actions-panel {
  flex: 0 0 400px; /* Fixed width for actions panel, adjust as needed */
  gap: 25px; /* Space between action-steps */
}
.results-panel {
  flex-grow: 1; /* Results panel takes remaining horizontal space */
}

.action-step h2, .results-panel h2 {
  margin-top: 0; margin-bottom: 15px; font-size: 1.3em; color: #2c3e50;
  border-bottom: 2px solid #3498db; padding-bottom: 10px; font-weight: 500;
}

.file-upload-controls { display: flex; gap: 10px; margin-bottom: 10px; }
.file-upload-controls .btn { flex-grow: 1; }

.selected-files-list { margin-top: 10px; font-size: 0.9em; }
.selected-files-list ul { list-style-type: none; padding-left: 0; margin: 0; }
.selected-files-list li { background-color: #f9f9f9; border: 1px solid #eee; padding: 5px 8px; margin-bottom: 3px; border-radius: 3px; font-size: 0.85em; }


.action-step textarea {
  width: 100%; min-height: 120px; padding: 10px; border: 1px solid #ccc;
  border-radius: 4px; box-sizing: border-box; font-family: inherit;
  font-size: .95em; margin-bottom: 10px; resize: vertical;
}
.query-buttons { display: flex; gap: 10px; margin-top: 5px; }
.query-buttons .btn { flex: 1; } /* Buttons share space equally */

/* General Button Styles (from your provided CSS) */
.btn {
  padding: 9px 16px; border: none; border-radius: 5px; cursor: pointer;
  font-size: .95em; transition: background-color .2s ease, box-shadow .2s ease, transform .1s ease;
  font-weight: 500; text-align: center;
}
.btn:hover:not(:disabled) { box-shadow: 0 2px 5px rgba(0,0,0,0.1); transform: translateY(-1px); }
.btn:active:not(:disabled) { transform: translateY(0); box-shadow: inset 0 1px 3px rgba(0,0,0,0.1); }
.btn:disabled { opacity: .6; cursor: not-allowed; }
.btn-primary { background-color: #3498db; color: #fff; }
.btn-primary:hover:not(:disabled) { background-color: #2980b9; }
.btn-secondary { background-color: #7f8c8d; color: #fff; }
.btn-secondary:hover:not(:disabled) { background-color: #6c7a7b; }
.btn-success { background-color: #2ecc71; color: #fff; }
.btn-success:hover:not(:disabled) { background-color: #27ae60; }
.btn-info { background-color: #1abc9c; color: #fff; }
.btn-info:hover:not(:disabled) { background-color: #16a085; }
.btn-outline { background-color: #fff; color: #3498db; border: 1px solid #3498db; }
.btn-outline:hover:not(:disabled) { background-color: #f0f8ff; }


.file-info { font-size: .85em; color: #555; margin-top: 8px; word-break: break-all; padding: 8px; background-color: #e9ecef; border-radius: 4px; }

/* Status Message Styles (from your provided CSS) */
.status-message { margin-top: 10px; padding: 10px 12px; border-radius: 4px; font-size: .9em; border: 1px solid transparent; }
.status-message.initial-message { text-align: center; padding: 15px; color: #555; background-color: #f9f9f9; border-color: #eee;}
.status-message.success { background-color: #e6ffed; border-color: #b7ebc3; color: #257942; }
.status-message.error { background-color: #ffebeb; border-color: #f5c0c0; color: #c0392b; }
.status-message.warning { background-color: #fff9e6; border-color: #ffecb3; color: #8a6d3b; }
.status-message.info { background-color: #e7f3fe; border-color: #b3d7f9; color: #31708f; }

/* Parsed Conditions & Results Table Styles (from your provided CSS) */
.parsed-conditions-display { /* Your class for parsed conditions */
  background-color: #2d2d2d; color: #f0f0f0; padding: 12px 15px;
  border-radius: 5px; margin-bottom: 15px; max-height: 180px;
  overflow-y: auto; font-size: .85em;
}
.parsed-conditions-display strong { color: #87ceeb; display: block; margin-bottom: 5px; }
.parsed-conditions-display pre { white-space: pre-wrap; word-wrap: break-word; font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace; margin: 0; }

.results-table-container {
  /* flex-grow: 1; -- Removed, results-panel handles growth */
  overflow: auto; /* Allows table to scroll horizontally and vertically if needed */
  border: 1px solid #ddd;
  border-radius: 5px;
  position: relative; /* For sticky header */
  max-height: 500px; /* Example max height, adjust as needed */
}
.results-count { padding: 8px 12px 5px; font-weight: 600; color: #444; font-size: .9em; }
.results-table { width: 100%; border-collapse: collapse; font-size: .88em; }
.results-table th, .results-table td {
  border: 1px solid #e0e0e0; padding: 9px 12px; text-align: left; vertical-align: top;
}
.results-table th {
  background-color: #ecf0f1; color: #34495e; position: sticky; top: 0; z-index: 10; font-weight: 600;
}
.results-table td {
  max-width: 280px; /* Limit column width */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: normal; /* Allow wrapping within the max-width */
}
.results-table td[title]:hover { cursor: help; } /* Show full content on hover via title */


.columns-display ul { list-style-type: none; padding-left: 0; margin-top: 5px; display: flex; flex-wrap: wrap; gap: 6px; }
.columns-display li { background-color: #dee2e6; padding: 4px 8px; border-radius: 10px; font-size: 0.85em; color: #343a40; }


.loader-small {
  width: 16px; height: 16px; border: 2.5px solid rgba(255,255,255,0.3);
  border-top-color: #fff; /* For loaders on dark buttons */
  border-radius: 50%; animation: spin 0.7s linear infinite;
}
/* If used on light buttons, adjust border-top-color */
.btn-outline .loader-small, .btn-light .loader-small {
  border-top-color: #3498db; /* Or primary button color */
}

@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

/* Responsive Adjustments from your CSS */
@media (max-width: 900px) {
  .app-header h1 { font-size: 1.4em; }
  .main-content { flex-direction: column; overflow-y: auto; padding: 15px; gap: 15px; }
  .actions-panel { flex: 0 0 auto; order: 1; } /* Actions panel takes its content height */
  .results-panel { min-height: 300px; order: 2; } /* Results panel also takes content height or min-height */
  .api-panels { grid-template-columns: 1fr; } /* Stack API panels */
}
@media (max-width: 600px) {
  .app-header { padding: 10px 15px; }
  .app-header h1 { font-size: 1.2em; }
  .user-info span { display: none; } /* Hide username on very small screens */
  .config-section { padding: 10px 15px; }
  .config-options { padding: 10px; }
  .actions-panel, .results-panel { padding: 15px; }
  .action-step h2, .results-panel h2 { font-size: 1.2em; padding-bottom: 8px; margin-bottom: 12px; }
  .file-upload-controls, .query-buttons { flex-direction: column; }
  .btn { font-size: .9em; padding: 8px 12px; width: 100%; box-sizing: border-box; } /* Full width buttons on small screens */
  .action-step textarea { min-height: 100px; }
}
</style>