<template>
  <div class="settings-view-placeholder card">
    <h2>修改密码</h2>
    <p>您可以在这里修改您的账户密码。</p>
    <form @submit.prevent="handleChangePassword" class="change-password-form">
      <div class="form-group">
        <label for="current-password">当前密码:</label>
        <input type="password" id="current-password" v-model="currentPassword" required>
      </div>
      <div class="form-group">
        <label for="new-password">新密码:</label>
        <input type="password" id="new-password" v-model="newPassword" required>
      </div>
      <div class="form-group">
        <label for="confirm-new-password">确认新密码:</label>
        <input type="password" id="confirm-new-password" v-model="confirmNewPassword" required>
      </div>
      <button type="submit" class="btn btn-primary" :disabled="isSubmitting">
        {{ isSubmitting ? '更新中...' : '更新密码' }}
      </button>
      <p v-if="statusMessage" :class="['status-message', isError ? 'error' : 'success']">{{ statusMessage }}</p>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios'; // Assuming you'll use axios for the API call

const FASTAPI_AUTH_URL = import.meta.env.VITE_API_AUTH_URL || 'http://localhost:8000/api/v1'; // Adjust if needed

const currentPassword = ref('');
const newPassword = ref('');
const confirmNewPassword = ref('');
const statusMessage = ref('');
const isError = ref(false);
const isSubmitting = ref(false);

const getAuthHeaders = () => { // Copied from ExcelQueryTool for consistency
  const token = localStorage.getItem('authToken');
  if (token) return { Authorization: `Bearer ${token}` };
  throw new Error("用户未认证");
};

const handleChangePassword = async () => {
  setStatusMessage('', false, 0); // Clear previous message
  if (newPassword.value !== confirmNewPassword.value) {
    setStatusMessage('新密码和确认密码不匹配。', true);
    return;
  }
  if (newPassword.value.length < 6) {
    setStatusMessage('新密码至少需要6个字符。', true);
    return;
  }

  isSubmitting.value = true;
  try {
    const headers = getAuthHeaders();
    // TODO: Replace with your actual backend endpoint for changing password
    // Example:
    // await axios.post(`${FASTAPI_AUTH_URL}/users/change-password`, {
    //   current_password: currentPassword.value,
    //   new_password: newPassword.value,
    // }, { headers });

    console.log('Change password attempt:', { currentPassword: currentPassword.value, newPassword: newPassword.value });
    setStatusMessage('密码修改功能待后端实现。 (模拟成功)', false); // Placeholder
    currentPassword.value = '';
    newPassword.value = '';
    confirmNewPassword.value = '';

  } catch (error) {
    console.error("Change password error:", error);
    if (error.message === "用户未认证") {
        setStatusMessage(error.message, true);
        // Optionally emit logout or trigger redirect via App.vue
    } else if (error.response && error.response.data && error.response.data.detail) {
      setStatusMessage(`密码修改失败: ${error.response.data.detail}`, true);
    } else {
      setStatusMessage('密码修改失败，请稍后再试。', true);
    }
  } finally {
    isSubmitting.value = false;
  }
};

const setStatusMessage = (message, errorFlag, duration = 4000) => {
  statusMessage.value = message;
  isError.value = errorFlag;
  if (duration > 0 && message) {
    setTimeout(() => {
      statusMessage.value = '';
    }, duration);
  }
};
</script>

<style scoped>
.settings-view-placeholder { padding: 25px; background-color: #fff; border-radius: 8px; }
.card h2 { margin-top:0; margin-bottom: 20px; font-size: 1.4em; color: #34495e; }
.change-password-form { max-width: 400px; /* Limit form width */ }
.form-group { margin-bottom: 18px; }
.form-group label { display: block; margin-bottom: 6px; font-weight: 500; color: #333; }
.form-group input[type="password"] {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
  font-size: 1em;
}
.btn-primary {
  background-color: #007bff; color: white; padding: 10px 15px;
  border: none; border-radius: 4px; cursor: pointer; font-size: 1em;
}
.btn-primary:hover:not(:disabled) { background-color: #0056b3; }
.btn-primary:disabled { background-color: #6c757d; }
.status-message { margin-top: 15px; padding: 10px; border-radius: 4px; }
.status-message.error { color: #721c24; background-color: #f8d7da; border: 1px solid #f5c6cb;}
.status-message.success { color: #155724; background-color: #d4edda; border: 1px solid #c3e6cb;}
</style>