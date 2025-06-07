<template>
  <div class="form-card">
    <h2>Login to Your Account</h2>
    <form @submit.prevent="handleLogin">
      <div class="input-group">
        <label for="login-identifier">Username or Email</label>
        <input type="text" id="login-identifier" v-model="formData.identifier" required />
        <div v-if="errors.identifier" class="error-detail">{{ errors.identifier }}</div>
      </div>

      <div class="input-group">
        <label for="login-password">Password</label>
        <input type="password" id="login-password" v-model="formData.password" required />
        <div v-if="errors.password" class="error-detail">{{ errors.password }}</div>
      </div>

      <button type="submit" class="btn-submit" :disabled="isLoading">
        <span v-if="isLoading" class="loader-small-auth"></span>
        {{ isLoading ? 'Logging in...' : 'Login' }}
      </button>
    </form>

    <div v-if="message" :class="['message-auth', messageType === 'success' ? 'success' : 'error']">
      {{ message }}
    </div>

    <div class="links-auth">
      <p>
        Don't have an account?
        <a href="#" @click.prevent="$emit('switchToRegister')">Register here</a>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'; // NO defineEmits here
import axios from 'axios';

// defineEmits is a compiler macro, no need to import
const emit = defineEmits(['loginSuccess', 'switchToRegister']);

const formData = reactive({
  identifier: '',
  password: '',
});

const isLoading = ref(false);
const message = ref('');
const messageType = ref(''); // 'success' or 'error'
const errors = reactive({}); // For field-specific errors from backend (optional)

const clearMessagesAndErrors = () => {
  message.value = '';
  messageType.value = '';
  for (const key in errors) {
    delete errors[key];
  }
};

const handleLogin = async () => {
  clearMessagesAndErrors();
  isLoading.value = true;

  if (!formData.identifier || !formData.password) {
    message.value = 'Username/Email and Password are required.';
    messageType.value = 'error';
    isLoading.value = false;
    return;
  }

  try {
    const response = await axios.post(`/api/v1/users/login`, { // Ensure this endpoint is correct
        identifier: formData.identifier,
        password: formData.password
    });

    if (response.status === 200 && response.data.access_token) {
      localStorage.setItem('authToken', response.data.access_token);
      localStorage.setItem('tokenType', response.data.token_type);

      // No explicit success message here, App.vue will handle UI change
      // message.value = 'Login successful! Redirecting...';
      // messageType.value = 'success';

      formData.identifier = ''; // Clear form
      formData.password = '';

      emit('loginSuccess'); // Signal App.vue that login was successful
    }
  } catch (error) {
    messageType.value = 'error';
    if (error.response && error.response.data && error.response.data.detail) {
      message.value = error.response.data.detail; // Display backend error
    } else if (error.response && error.response.status === 422) { // Unprocessable Entity (validation error)
        message.value = "Invalid input format or data.";
        // You could parse error.response.data.detail for more specific messages if backend provides field errors
        // Example: error.response.data.detail.forEach(err => errors[err.loc[1]] = err.msg);
    } else if (error.request) {
        message.value = 'Login failed. Server did not respond. Please try again later.';
    }
    else {
      message.value = 'Login failed. An unexpected error occurred.';
    }
    console.error('Login error:', error);
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
/* Styles specific to LoginForm, using classes from your global styles or RAGFlow example */
.form-card {
  background-color: #fff;
  padding: 30px 40px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  width: 100%;
  max-width: 400px;
  text-align: center;
}
.form-card h2 { color: #1d2129; font-size: 24px; margin-bottom: 25px; }
.input-group { margin-bottom: 20px; text-align: left; }
.input-group label { display: block; font-weight: 600; margin-bottom: 6px; color: #4b4f56; font-size: 0.9rem; }
.input-group input {
  width: 100%; padding: 10px 12px; border: 1px solid #ccd0d5;
  border-radius: 6px; font-size: 1rem; box-sizing: border-box;
}
.input-group input:focus {
  border-color: #1877f2; outline: none;
  box-shadow: 0 0 0 2px rgba(24, 119, 242, 0.2);
}
.btn-submit {
  background-color: #1877f2; color: white; border: none;
  padding: 12px 20px; font-size: 1rem; font-weight: bold;
  border-radius: 6px; cursor: pointer; width: 100%;
  transition: background-color 0.2s;
  display: inline-flex; align-items: center; justify-content: center; gap: 8px;
}
.btn-submit:hover:not(:disabled) { background-color: #166fe5; }
.btn-submit:disabled { background-color: #cccccc; cursor: not-allowed; }

.message-auth { /* Renamed to avoid conflict */
  margin-top: 15px; padding: 10px; border-radius: 4px;
  font-size: 0.9rem; text-align: left; border: 1px solid transparent;
}
.message-auth.success { background-color: #d4edda; color: #155724; border-color: #c3e6cb; }
.message-auth.error { background-color: #f8d7da; color: #721c24; border-color: #f5c6cb; }
.error-detail { font-size: 0.8rem; color: #dc3545; margin-top: 4px; text-align: left; }

.links-auth { margin-top: 20px; font-size: 0.9rem; }
.links-auth a { color: #1877f2; text-decoration: none; }
.links-auth a:hover { text-decoration: underline; }

.loader-small-auth { /* Renamed to avoid conflict */
  width: 16px; height: 16px; border: 2.5px solid rgba(255,255,255,0.5);
  border-top-color: #fff; border-radius: 50%;
  animation: spin-auth 0.7s linear infinite;
}
@keyframes spin-auth { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>