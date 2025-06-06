<template>
  <div class="excel-query-tool-page">
    <header class="app-header">
      <h1>通用Excel智能查询工具</h1>
      <div class="user-info">
        <span>欢迎, {{ props.currentUsername }}</span>
        <button @click="logout" class="btn-link">退出登录</button>
      </div>
    </header>

    <div class="config-section">
      <button @click="toggleConfig" class="btn btn-secondary toggle-config-btn">
        {{ showConfig ? '隐藏配置选项' : '显示配置选项' }}
      </button>

      <div v-if="showConfig" class="config-options">
        <h2>API配置</h2>
        <div class="api-panels">
          <div class="api-panel">
            <h3>硅基流动API</h3>
            <div class="form-group">
              <label for="sf-apikey">API密钥:</label>
              <input type="password" id="sf-apikey" v-model="config.siliconflow.apiKey" placeholder="您的硅基流动API密钥">
            </div>
            <div class="form-group">
              <label for="sf-endpoint">API端点:</label>
              <input type="text" id="sf-endpoint" v-model="config.siliconflow.apiUrl" placeholder="硅基流动API的完整URL地址">
            </div>
            <div class="form-group">
              <label for="sf-model">模型:</label>
              <select id="sf-model" v-model="config.siliconflow.model">
                <option>Qwen/Qwen2-7B-Instruct</option>
                <option>Qwen/Qwen2-57B-A14B-Instruct</option>
                <option>deepseek-ai/DeepSeek-V2-Chat</option>
                <option>THUDM/glm-4-9b-chat</option>
                <option>01-ai/Yi-1.5-34B-Chat</option>
                <!-- Add the model used in backend's DEFAULT_LLM_CONFIG -->
                <option>Qwen/Qwen3-8B</option>
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
              <input type="text" id="ollama-endpoint" v-model="config.ollama.apiUrl" placeholder="本地Ollama API的完整URL地址">
            </div>
            <div class="form-group">
              <label for="ollama-model">模型:</label>
              <input type="text" id="ollama-model" v-model="config.ollama.model" placeholder="已在本地安装的Ollama模型名称">
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
        <p v-if="configStatus" class="status-message success">{{ configStatus }}</p>
      </div>
    </div>

    <main class="main-content">
      <div class="actions-panel">
        <section class="action-step">
          <h2>1. 上传Excel文件</h2>
          <!-- Modified file input to allow multiple files -->
          <input type="file" @change="handleFileSelection" accept=".xlsx, .xls, .csv" ref="fileInputRef" multiple style="display: none;">
          <div class="file-upload-controls">
            <button @click="triggerFileInput" :disabled="isUploading" class="btn btn-outline">
              选择文件 (可多选)
            </button>
            <button @click="uploadAndProcess" :disabled="!selectedFilesForUpload.length || isUploading" class="btn btn-success">
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
          <p v-if="fileInfo" class="file-info">{{ fileInfo }}</p> <!-- This can show summary after upload -->
          <p v-if="uploadStatus.message" :class="['status-message', uploadStatus.type]">{{ uploadStatus.message }}</p>
        </section>

        <section class="action-step">
          <h2>2. 输入自然语言查询</h2>
          <textarea v-model="naturalQuery" placeholder="例如：找出所有销售额大于1000且利润率高于20%的记录"></textarea>
          <div class="query-buttons">
            <button @click="executeQuery" :disabled="isQuerying || !isFileUploaded" class="btn btn-primary">
              {{ isQuerying ? '查询中...' : '执行查询' }}
            </button>
            <button @click="downloadResults" :disabled="isDownloading || !results.length" class="btn btn-info">
              {{ isDownloading ? '下载中...' : '下载结果' }}
            </button>
          </div>
          <p v-if="queryStatus.message" :class="['status-message', queryStatus.type]">{{ queryStatus.message }}</p>
        </section>
      </div>

      <div class="results-panel">
        <h2>查询结果</h2>
        <div v-if="!isFileUploaded && !isQuerying && !isUploading" class="status-message info initial-message">
          请先上传并处理Excel文件。
        </div>
        <div v-else-if="isFileUploaded && !results.length && !isQuerying && (!queryStatus.message || !queryStatus.message.includes('没有找到匹配的记录'))" class="status-message info initial-message">
          文件已上传，请输入自然语言查询并执行。
        </div>
        <div v-else-if="queryStatus.message.includes('没有找到匹配的记录') && !isQuerying" class="status-message warning">
          没有找到匹配的记录。
        </div>

        <div v-if="results.length > 0" class="results-table-container">
          <p class="results-count">找到 {{ results.length }} 条记录。</p>
          <table class="results-table">
            <thead>
              <tr>
                <th v-for="header_col in headers" :key="header_col">{{ header_col }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, rowIndex) in results" :key="rowIndex">
                <td v-for="header_col in headers" :key="header_col" :title="String(row[header_col])">
                  {{ String(row[header_col]).length > 100 ? String(row[header_col]).substring(0, 100) + '...' : row[header_col] }}
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
import { ref, reactive, computed, watch, onMounted } from 'vue';

const props = defineProps({
  currentUsername: {
    type: String,
    default: '测试用户'
  }
});

const emit = defineEmits(['user-logout']);

const showConfig = ref(false);
const config = reactive({ // This structure matches ExcelQueryRequest.config
  apiType: 'siliconflow', // Default API type
  siliconflow: {
    apiKey: '',
    apiUrl: 'https://api.siliconflow.cn/v1/chat/completions',
    model: 'Qwen/Qwen2-7B-Instruct',
    temperature: 0.2, // Default from backend
    maxTokens: 2048  // Default from backend
  },
  ollama: {
    apiUrl: 'http://localhost:11434/api/chat',
    model: 'llama3:8b', // Default from backend
    temperature: 0.2,
    topP: 0.9,
  }
});
const configStatus = ref('');

const fileInputRef = ref(null); // Ref for the <input type="file">
const selectedFilesForUpload = ref([]); // To hold selected files from input
const isUploading = ref(false);
const fileInfo = ref(''); // To show summary after upload
const uploadStatus = reactive({ message: '', type: '' });
const isFileUploaded = ref(false); // True if at least one file from a batch was successfully processed

const naturalQuery = ref('');
const isQuerying = ref(false);
const queryStatus = reactive({ message: '', type: '' });
const parsedConditions = ref(null);
const results = ref([]);
const headers = computed(() => (results.value.length > 0 ? Object.keys(results.value[0]) : []));
const isDownloading = ref(false);

const logout = () => { emit('user-logout'); };
const toggleConfig = () => { showConfig.value = !showConfig.value; };

const saveConfiguration = () => {
  localStorage.setItem('excelQueryLLMConfig', JSON.stringify(config));
  configStatus.value = 'API配置已保存！';
  setTimeout(() => configStatus.value = '', 3000);
};

onMounted(() => {
  const savedConfig = localStorage.getItem('excelQueryLLMConfig');
  if (savedConfig) {
    try {
      const parsed = JSON.parse(savedConfig);
      // Merge carefully, ensuring all keys exist
      config.apiType = parsed.apiType || 'siliconflow';
      if (parsed.siliconflow) Object.assign(config.siliconflow, parsed.siliconflow);
      if (parsed.ollama) Object.assign(config.ollama, parsed.ollama);
    } catch (e) { console.error('Failed to parse saved LLM configuration:', e); }
  }
});

const triggerFileInput = () => {
  fileInputRef.value.click();
};

const handleFileSelection = (event) => {
  selectedFilesForUpload.value = Array.from(event.target.files);
  if (selectedFilesForUpload.value.length === 0) {
    fileInfo.value = ''; // Clear if no files selected
  }
  // Reset status messages for new selection
  uploadStatus.message = '';
  uploadStatus.type = '';
  isFileUploaded.value = false;
  results.value = [];
  parsedConditions.value = null;
  queryStatus.message = '';
};

const uploadAndProcess = async () => {
  if (selectedFilesForUpload.value.length === 0) {
    uploadStatus.message = '请选择文件上传。';
    uploadStatus.type = 'warning';
    return;
  }
  isUploading.value = true;
  isFileUploaded.value = false; // Reset for this upload attempt
  uploadStatus.message = '正在上传和处理文件...';
  uploadStatus.type = 'info';
  results.value = []; // Clear previous results on new upload
  parsedConditions.value = null;
  queryStatus.message = ''; queryStatus.type = '';

  const formData = new FormData();
  for (const file of selectedFilesForUpload.value) {
    formData.append('files', file);
  }

  try {
    const authToken = localStorage.getItem('authToken');
    if (!authToken) {
        throw new Error("用户未认证，请先登录。");
    }

    const response = await fetch('/api/v1/excel/upload', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${authToken}`
        // 'Content-Type': 'multipart/form-data' is set by browser for FormData
      },
      body: formData
    });

    const responseData = await response.json();

    if (!response.ok) {
      throw new Error(responseData.detail || `服务器错误: ${response.status}`);
    }

    // --- CORRECTED RESPONSE HANDLING ---
    if (responseData.success && responseData.details && responseData.details.length > 0) {
      isFileUploaded.value = true; // At least one file was processed by backend
      const successfulFilenames = responseData.details.map(item => item.filename);
      let message = `成功处理文件: ${successfulFilenames.join(', ')}.`;
      uploadStatus.type = 'success';

      if (responseData.errors && responseData.errors.length > 0) {
        message += ` 但发生以下错误: ${responseData.errors.join('; ')}`;
        uploadStatus.type = 'warning'; // Indicate partial success / issues
      }
      uploadStatus.message = message;
      fileInfo.value = `最近处理: ${successfulFilenames.join(', ')}`; // Update summary

    } else if (responseData.errors && responseData.errors.length > 0) {
      uploadStatus.message = `上传失败: ${responseData.errors.join('; ')}`;
      uploadStatus.type = 'error';
      isFileUploaded.value = false;
    } else if (!responseData.success && responseData.message) { // Backend indicates failure with a message
      uploadStatus.message = responseData.message;
      uploadStatus.type = 'error';
      isFileUploaded.value = false;
    }
     else {
      uploadStatus.message = '上传处理完成，但服务器未返回明确成功状态或文件详情。';
      uploadStatus.type = 'warning';
      isFileUploaded.value = false;
    }
    // --- END OF CORRECTED RESPONSE HANDLING ---

  } catch (error) {
    console.error("Upload error:", error);
    uploadStatus.message = `文件上传请求失败: ${error.message}`;
    uploadStatus.type = 'error';
    isFileUploaded.value = false;
  } finally {
    isUploading.value = false;
    // Clear the selected files from the input ref after an attempt
    if (fileInputRef.value) {
      fileInputRef.value.value = ''; // Resets the file input
    }
    selectedFilesForUpload.value = []; // Clear the reactive array
  }
};


const executeQuery = async () => {
  if (!naturalQuery.value.trim()) {
    queryStatus.message = '请输入自然语言查询语句。'; queryStatus.type = 'warning'; return;
  }
  if (!isFileUploaded.value) {
    queryStatus.message = '请先成功上传Excel文件。'; queryStatus.type = 'warning'; return;
  }
  isQuerying.value = true;
  queryStatus.message = '正在查询，请稍候...'; queryStatus.type = 'info';
  results.value = []; parsedConditions.value = null;

  const authToken = localStorage.getItem('authToken');
    if (!authToken) {
        queryStatus.message = "用户未认证，请先登录。"; queryStatus.type = 'error'; isQuerying.value = false; return;
    }

  // Prepare LLM config to send based on current selection
  const llmConfigPayload = {
    apiType: config.apiType,
    [config.apiType]: { ...config[config.apiType] } // Send only the config for the selected API type
  };


  try {
    const response = await fetch('/api/v1/excel/query', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({ query: naturalQuery.value, config: llmConfigPayload })
    });
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || `查询失败: ${response.status}`);
    }

    parsedConditions.value = data.parsed_conditions;
    results.value = data.results;
    if (results.value.length === 0) {
        queryStatus.message = '没有找到匹配的记录。'; queryStatus.type = 'warning';
    } else {
        queryStatus.message = `查询成功，找到 ${results.value.length} 条记录。 (源文件: ${data.source_files.join(', ')})`;
        queryStatus.type = 'success';
    }
  } catch (error) {
    console.error("Query error:", error);
    queryStatus.message = `查询请求失败: ${error.message}`; queryStatus.type = 'error';
    parsedConditions.value = { query: naturalQuery.value, error: error.message };
  } finally {
    isQuerying.value = false;
  }
};

const downloadResults = async () => {
  if (!results.value.length && !naturalQuery.value.trim()) {
     queryStatus.message = '没有可下载的结果或查询条件。'; queryStatus.type = 'warning'; return;
  }
  isDownloading.value = true;
  queryStatus.message = '正在准备下载...'; queryStatus.type = 'info';

  const authToken = localStorage.getItem('authToken');
  if (!authToken) {
    queryStatus.message = "用户未认证，请先登录。"; queryStatus.type = 'error'; isDownloading.value = false; return;
  }

  const llmConfigPayload = {
    apiType: config.apiType,
    [config.apiType]: { ...config[config.apiType] }
  };

  // If results are already available, use the parsed_conditions from the last query.
  // If no results but query exists, backend will re-parse.
  const payload = {
    query: results.value.length ? undefined : naturalQuery.value.trim(), // Send query only if no results yet
    parsed_conditions: results.value.length && parsedConditions.value ? parsedConditions.value : undefined,
    config: llmConfigPayload
  };

  try {
    const response = await fetch('/api/v1/excel/download', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(payload)
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "下载准备失败，无法解析错误信息。" }));
        throw new Error(errorData.detail || `下载失败: ${response.status}`);
    }

    const blob = await response.blob();
    const contentDisposition = response.headers.get('content-disposition');
    let filename = "query_results.xlsx"; // Default filename
    if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?(.+)"?/i);
        if (filenameMatch && filenameMatch.length === 2)
            filename = filenameMatch[1];
    }

    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(link.href);
    queryStatus.message = '结果文件已开始下载。'; queryStatus.type = 'success';
  } catch (error) {
    console.error("Download error:", error);
    queryStatus.message = `下载请求失败: ${error.message}`; queryStatus.type = 'error';
  } finally {
    isDownloading.value = false;
    setTimeout(() => { if (queryStatus.message.includes('下载')) { queryStatus.message = ''; queryStatus.type = ''; }}, 4000);
  }
};

</script>

<style scoped>
/* Copied styles from your full component response */
.excel-query-tool-page{display:flex;flex-direction:column;height:100%;width:100%;box-sizing:border-box;background-color:#f4f7f6;color:#333;overflow:hidden}
.app-header{display:flex;justify-content:space-between;align-items:center;padding:12px 25px;background-color:#2c3e50;color:white;flex-shrink:0;box-shadow:0 2px 4px rgba(0,0,0,0.1)}
.app-header h1{margin:0;font-size:1.6em;font-weight:500}
.user-info{display:flex;align-items:center;font-size:.95em}
.user-info span{margin-right:15px}
.btn-link{background:none;border:1px solid #7f8c8d;color:#ecf0f1;cursor:pointer;padding:6px 12px;border-radius:4px;text-decoration:none;font-size:.9em;transition:background-color .2s,color .2s}
.btn-link:hover{background-color:#ecf0f1;color:#2c3e50}
.config-section{padding:15px 25px;background-color:#fff;border-bottom:1px solid #e0e0e0;flex-shrink:0}
.toggle-config-btn{margin-bottom:10px}
.config-options{margin-top:5px;padding:15px;border:1px solid #ddd;border-radius:8px;background-color:#fdfdfd}
.config-options h2,.config-options h3{margin-top:0;color:#34495e}
.config-options h2{font-size:1.3em;margin-bottom:15px}
.config-options h3{margin-bottom:12px;font-size:1.1em;border-bottom:1px solid #eee;padding-bottom:8px;color:#2c3e50}
.api-panels{display:grid;grid-template-columns:repeat(auto-fit,minmax(350px,1fr));gap:20px;margin-bottom:20px}
.api-panel{padding:15px;border:1px solid #e0e0e0;border-radius:6px;background-color:#fff}
.advanced-options{margin-top:15px}
.form-group{margin-bottom:12px}
.form-group label:not(.radio-group label){display:block;margin-bottom:6px;font-weight:600;font-size:.9em;color:#555}
.form-group .range-helper-text{font-size:.8em;color:#777;display:block;margin-top:4px}
.form-group .api-type-label{font-weight:600;font-size:.9em;color:#555;margin-bottom:8px}
.radio-group{display:flex;gap:15px;align-items:center}
.radio-group label{font-weight:normal;font-size:.9em;display:flex;align-items:center;cursor:pointer}
.radio-group input[type=radio]{margin-right:6px;transform:scale(.9)}
.api-type-helper{font-size:.8em;color:#777;display:block;margin-top:6px}
.form-group input[type=text],.form-group input[type=password],.form-group input[type=number],.form-group select{width:100%;padding:9px 12px;border:1px solid #ccc;border-radius:4px;box-sizing:border-box;font-size:.95em;background-color:#fff}
.form-group input[type=range]{width:100%;margin-top:5px}
.save-config-btn{margin-top:10px}
.main-content{display:flex;flex-grow:1;padding:20px 25px 25px 25px;gap:25px;overflow:hidden}
.actions-panel,.results-panel{background-color:#fff;border-radius:8px;box-shadow:0 3px 10px rgba(0,0,0,0.07);padding:20px;display:flex;flex-direction:column;overflow-y:auto}
.actions-panel{flex:0 0 380px;gap:25px}
.results-panel{flex-grow:1}
.action-step h2,.results-panel h2{margin-top:0;margin-bottom:15px;font-size:1.3em;color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:10px;font-weight:500}
.file-upload-controls{display:flex;gap:10px;margin-bottom:10px}
.file-upload-controls .btn{flex-grow:1}

.selected-files-list { margin-top: 10px; font-size: 0.9em; }
.selected-files-list ul { list-style-type: none; padding-left: 0; }
.selected-files-list li { background-color: #f9f9f9; border: 1px solid #eee; padding: 5px 8px; margin-bottom: 3px; border-radius: 3px; }

.action-step textarea{width:100%;min-height:120px;padding:10px;border:1px solid #ccc;border-radius:4px;box-sizing:border-box;font-family:inherit;font-size:.95em;margin-bottom:10px;resize:vertical}
.query-buttons{display:flex;gap:10px;margin-top:5px}
.query-buttons .btn{flex:1}
.btn{padding:9px 16px;border:none;border-radius:5px;cursor:pointer;font-size:.95em;transition:background-color .2s ease,box-shadow .2s ease,transform .1s ease;font-weight:500;text-align:center}
.btn:hover:not(:disabled){box-shadow:0 2px 5px rgba(0,0,0,0.1);transform:translateY(-1px)}
.btn:active:not(:disabled){transform:translateY(0);box-shadow:inset 0 1px 3px rgba(0,0,0,0.1)}
.btn:disabled{opacity:.6;cursor:not-allowed}
.btn-primary{background-color:#3498db;color:#fff}
.btn-primary:hover:not(:disabled){background-color:#2980b9}
.btn-secondary{background-color:#7f8c8d;color:#fff}
.btn-secondary:hover:not(:disabled){background-color:#6c7a7b}
.btn-success{background-color:#2ecc71;color:#fff}
.btn-success:hover:not(:disabled){background-color:#27ae60}
.btn-info{background-color:#1abc9c;color:#fff}
.btn-info:hover:not(:disabled){background-color:#16a085}
.btn-outline{background-color:#fff;color:#3498db;border:1px solid #3498db}
.btn-outline:hover:not(:disabled){background-color:#f0f8ff}
.file-info{font-size:.85em;color:#555;margin-top:8px;word-break:break-all;padding:8px;background-color:#e9ecef;border-radius:4px}
.status-message{margin-top:10px;padding:10px 12px;border-radius:4px;font-size:.9em;border:1px solid transparent}
.status-message.initial-message{text-align:center;padding:15px;color:#555}
.status-message.success{background-color:#e6ffed;border-color:#b7ebc3;color:#257942}
.status-message.error{background-color:#ffebeb;border-color:#f5c0c0;color:#c0392b}
.status-message.warning{background-color:#fff9e6;border-color:#ffecb3;color:#8a6d3b}
.status-message.info{background-color:#e7f3fe;border-color:#b3d7f9;color:#31708f}
.parsed-conditions{background-color:#2d2d2d;color:#f0f0f0;padding:12px 15px;border-radius:5px;margin-bottom:15px;max-height:180px;overflow-y:auto;font-size:.85em}
.parsed-conditions strong{color:#87ceeb;display:block;margin-bottom:5px}
.parsed-conditions pre{white-space:pre-wrap;word-wrap:break-word;font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,Courier,monospace;margin:0}
.results-table-container{flex-grow:1;overflow:auto;border:1px solid #ddd;border-radius:5px;position:relative}
.results-count{padding:8px 12px 5px;font-weight:600;color:#444;font-size:.9em}
.results-table{width:100%;border-collapse:collapse;font-size:.88em}
.results-table th,.results-table td{border:1px solid #e0e0e0;padding:9px 12px;text-align:left;vertical-align:top}
.results-table th{background-color:#ecf0f1;color:#34495e;position:sticky;top:0;z-index:10;font-weight:600}
.results-table td{max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:normal}
.results-table td[title]:hover{cursor:help}
@media (max-width:900px){.app-header h1{font-size:1.4em}.main-content{flex-direction:column;overflow-y:auto;padding:15px;gap:15px}.actions-panel{flex:0 0 auto;order:1}.results-panel{min-height:300px;order:2}.api-panels{grid-template-columns:1fr}}
@media (max-width:600px){.app-header{padding:10px 15px}.app-header h1{font-size:1.2em}.user-info span{display:none}.config-section{padding:10px 15px}.config-options{padding:10px}.actions-panel,.results-panel{padding:15px}.action-step h2,.results-panel h2{font-size:1.2em;padding-bottom:8px;margin-bottom:12px}.file-upload-controls,.query-buttons{flex-direction:column}.btn{font-size:.9em;padding:8px 12px}.action-step textarea{min-height:100px}}

</style>