<template>
  <div class="form-card">
    <h2>Create Account</h2>
    <form @submit.prevent="handleRegister">
      <div class="input-group">
        <label for="reg-username">Username</label>
        <input type="text" id="reg-username" v-model="formData.username" required />
        <div v-if="errors.username" class="error-detail">{{ errors.username }}</div>
      </div>

      <div class="input-group">
        <label for="reg-email">Email</label>
        <input type="email" id="reg-email" v-model="formData.email" required />
          <div v-if="errors.email" class="error-detail">{{ errors.email }}</div>
      </div>

      <div class="input-group">
        <label for="reg-password">Password</label>
        <input type="password" id="reg-password" v-model="formData.password" required />
          <div v-if="errors.password" class="error-detail">{{ errors.password }}</div>
      </div>

      <div class="input-group">
        <label for="reg-confirmPassword">Confirm Password</label>
        <input type="password" id="reg-confirmPassword" v-model="formData.confirmPassword" required />
        <div v-if="errors.confirmPassword" class="error-detail">{{ errors.confirmPassword }}</div>
      </div>

      <!-- USER GROUP FIELD REMOVED FROM TEMPLATE -->

      <button type="submit" class="btn-submit" :disabled="isLoading">
        <span v-if="isLoading" class="loader-small-auth"></span>
        {{ isLoading ? 'Registering...' : 'Register' }}
      </button>
    </form>

    <div v-if="message" :class="['message-auth', messageType === 'success' ? 'success' : 'error']">
      {{ message }}
    </div>
     <div class="links-auth">
      <p>Already have an account? <a href="#" @click.prevent="$emit('switchToLogin')">Login here</a></p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue';
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_AUTH_URL || 'http://localhost:8000/api/v1';

const emit = defineEmits(['registrationSuccess', 'switchToLogin']);

const formData = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
  // user_group: 'default', // REMOVED user_group from formData initialization
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

const validateClientSide = () => {
    let isValid = true;
    clearMessagesAndErrors();

    if (!formData.username.trim()) {
        errors.username = "Username is required.";
        isValid = false;
    }
    if (!formData.email.trim()) {
        errors.email = "Email is required.";
        isValid = false;
    } else if (!/^\S+@\S+\.\S+$/.test(formData.email)) {
        errors.email = "Invalid email format.";
        isValid = false;
    }
    if (formData.password.length < 6) {
        errors.password = "Password must be at least 6 characters long.";
        isValid = false;
    }
    if (formData.password !== formData.confirmPassword) {
        errors.confirmPassword = "Passwords do not match.";
        isValid = false;
    }
    if (!isValid && !message.value) {
        message.value = "Please correct the errors above.";
        messageType.value = 'error';
    }
    return isValid;
};

const handleRegister = async () => {
  if (!validateClientSide()) {
    return;
  }
  clearMessagesAndErrors(); // Clear general messages if validation passed

  isLoading.value = true;

  try {
    const payload = {
      username: formData.username,
      email: formData.email,
      password: formData.password,
      confirm_password: formData.confirmPassword,
      // user_group field is NOT sent to the backend if it's removed.
      // The backend UserCreate model has a default for user_group, so it's fine.
    };

    const response = await axios.post(`/api/v1/users/register`, payload);

    if (response.status === 201) {
      message.value = `User "${response.data.username}" registered successfully! Please login.`;
      messageType.value = 'success';
      formData.username = '';
      formData.email = '';
      formData.password = '';
      formData.confirmPassword = '';
      // No need to reset user_group as it's removed
      emit('registrationSuccess');
    }
  } catch (error) {
    messageType.value = 'error';
    if (error.response && error.response.data) {
      if (error.response.data.detail && typeof error.response.data.detail === 'string') {
        message.value = error.response.data.detail;
      } else if (error.response.data.detail && Array.isArray(error.response.data.detail)) {
        message.value = "Registration failed. Please check your input:";
        error.response.data.detail.forEach(err => {
          const field = err.loc[1];
          if (errors.hasOwnProperty(field)) { // Use hasOwnProperty for safety
            errors[field] = err.msg;
          } else {
            message.value += `\n- ${field.replace("_", " ")}: ${err.msg}`;
          }
        });
      } else {
        message.value = 'An unexpected error occurred during registration.';
      }
    } else if (error.request) {
        message.value = 'Registration failed. Server did not respond. Please try again later.';
    }
    else {
      message.value = 'Registration failed. An unexpected error occurred.';
    }
    console.error('Registration error:', error);
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
/* Same styles as LoginForm.vue or your consistent auth form styling */
.form-card {
  background-color: #fff; padding: 30px 40px; border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); width: 100%;
  max-width: 400px; text-align: center;
}
.form-card h2 { color: #1d2129; font-size: 24px; margin-bottom: 25px; }
.input-group { margin-bottom: 20px; text-align: left; }
.input-group label {
  display: block; font-weight: 600; margin-bottom: 6px;
  color: #4b4f56; font-size: 0.9rem;
}
.input-group input, .input-group select {
  width: 100%; padding: 10px 12px; border: 1px solid #ccd0d5;
  border-radius: 6px; font-size: 1rem; box-sizing: border-box;
}
.input-group input:focus, .input-group select:focus {
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

.message-auth {
  margin-top: 15px; padding: 10px; border-radius: 4px;
  font-size: 0.9rem; text-align: left; border: 1px solid transparent;
}
.message-auth.success { background-color: #d4edda; color: #155724; border-color: #c3e6cb; }
.message-auth.error { background-color: #f8d7da; color: #721c24; border-color: #f5c6cb; }
.error-detail { font-size: 0.8rem; color: #dc3545; margin-top: 4px; text-align: left; }

.links-auth { margin-top: 20px; font-size: 0.9rem; }
.links-auth a { color: #1877f2; text-decoration: none; }
.links-auth a:hover { text-decoration: underline; }

.loader-small-auth {
  width: 16px; height: 16px; border: 2.5px solid rgba(255,255,255,0.5);
  border-top-color: #fff; border-radius: 50%;
  animation: spin-auth 0.7s linear infinite;
}
@keyframes spin-auth { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
</style>