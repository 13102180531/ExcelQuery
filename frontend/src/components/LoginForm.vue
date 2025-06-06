<template>
  <div class="form-card">
    <h2>Login to Your Account</h2>
    <!-- <p class="app-name">My Awesome App</p> -->

    <form @submit.prevent="handleLogin">
      <div class="input-group">
        <label for="identifier">Username or Email</label>
        <input type="text" id="identifier" v-model="formData.identifier" required />
        <div v-if="errors.identifier" class="error-detail">{{ errors.identifier }}</div>
      </div>

      <div class="input-group">
        <label for="password">Password</label>
        <input type="password" id="password" v-model="formData.password" required />
        <div v-if="errors.password" class="error-detail">{{ errors.password }}</div>
      </div>

      <button type="submit" class="btn-submit" :disabled="isLoading">
        {{ isLoading ? 'Logging in...' : 'Login' }}
      </button>
    </form>

    <div v-if="message" :class="['message', messageType]">
      {{ message }}
    </div>

    <div class="links" style="margin-top: 20px; font-size: 0.9rem;">
      <p>
        Don't have an account?
        <a href="#" @click.prevent="$emit('switchToRegister')">Register here</a>
      </p>
    </div>
  </div>
</template>

<script setup>
// ... rest of the script setup ...
import { ref, reactive } from 'vue';
import axios from 'axios';


// Define emits
const emit = defineEmits(['loginSuccess', 'switchToRegister']);

const formData = reactive({
  identifier: '',
  password: '',
});

const isLoading = ref(false);
const message = ref('');
const messageType = ref(''); // 'success' or 'error'
const errors = reactive({});

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
    const response = await axios.post(`/api/v1/users/login`, {
        identifier: formData.identifier,
        password: formData.password
    });

    if (response.status === 200 && response.data.access_token) {
      localStorage.setItem('authToken', response.data.access_token); // Store the token
      localStorage.setItem('tokenType', response.data.token_type);
      emit('loginSuccess')
    }
  } catch (error) {
    messageType.value = 'error';
    if (error.response && error.response.data && error.response.data.detail) {
      message.value = error.response.data.detail;
    } else if (error.response && error.response.status === 422) {
        message.value = "Invalid input format.";
    }
    else {
      message.value = 'Login failed. Please check your credentials or try again later.';
    }
    console.error('Login error:', error);
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.links a {
  color: #007bff;
  text-decoration: none;
}
.links a:hover {
  text-decoration: underline;
}
</style>