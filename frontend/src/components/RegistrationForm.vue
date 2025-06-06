<template>
  <div class="form-card">
    <h2>Create Account</h2>
    <!-- <p class="app-name">My Awesome App</p> -->

    <form @submit.prevent="handleRegister">
      <div class="input-group">
        <label for="username">Username</label>
        <input type="text" id="username" v-model="formData.username" required />
        <div v-if="errors.username" class="error-detail">{{ errors.username }}</div>
      </div>

      <div class="input-group">
        <label for="email">Email</label>
        <input type="email" id="email" v-model="formData.email" required />
          <div v-if="errors.email" class="error-detail">{{ errors.email }}</div>
      </div>

      <div class="input-group">
        <label for="password">Password</label>
        <input type="password" id="password" v-model="formData.password" required />
          <div v-if="errors.password" class="error-detail">{{ errors.password }}</div>
      </div>

      <div class="input-group">
        <label for="confirmPassword">Confirm Password</label>
        <input type="password" id="confirmPassword" v-model="formData.confirmPassword" required />
        <div v-if="errors.confirmPassword" class="error-detail">{{ errors.confirmPassword }}</div>
      </div>
      <button type="submit" class="btn-submit" :disabled="isLoading">
        {{ isLoading ? 'Registering...' : 'Register' }}
      </button>
    </form>

    <div v-if="message" :class="['message', messageType]">
      {{ message }}
    </div>
    <div class="links" style="margin-top: 20px; font-size: 0.9rem;">
        <p>Already have an account? <a href="#" @click.prevent="$emit('switchToLogin')">Login here</a></p>
    </div>
  </div>
</template>

<script setup>
// ... rest of the script setup ...
import { ref, reactive } from 'vue';
import axios from 'axios';

const emit = defineEmits(['registrationSuccess', 'switchToLogin']);

const formData = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: '',
});

const isLoading = ref(false);
const message = ref('');
const messageType = ref('');
const errors = reactive({});

const clearMessages = () => {
  message.value = '';
  messageType.value = '';
  for (const key in errors) {
    delete errors[key];
  }
};

const validateForm = () => {
  clearMessages(); // Clear all messages, including general ones
  let isValid = true;
  // Clear previous field-specific errors before re-validating
  for (const key in errors) {
    delete errors[key];
  }

  if (formData.password !== formData.confirmPassword) {
    errors.confirmPassword = 'Passwords do not match.';
    isValid = false;
  }
  if (formData.password.length < 6) {
      errors.password = 'Password must be at least 6 characters long.';
      isValid = false;
  }
  if (!formData.username.trim()) {
      errors.username = 'Username is required.';
      isValid = false;
  }
  if (!formData.email.trim()) {
      errors.email = 'Email is required.';
      isValid = false;
  } else if (!/^\S+@\S+\.\S+$/.test(formData.email)) {
      errors.email = 'Invalid email format.';
      isValid = false;
  }

  if (!isValid) {
    message.value = "Please correct the errors highlighted below."; // General message
    messageType.value = "error";
  }
  return isValid;
};

const handleRegister = async () => {
  // Clear messages from previous attempts but keep errors from validateForm if it fails
  if (!validateForm()) {
    // validateForm already set the message and errors
    return;
  }
  // If validation passed, clear any general message that might have been set by validateForm
  clearMessages();


  isLoading.value = true;

  try {
    const payload = {
      username: formData.username,
      email: formData.email,
      password: formData.password,
      confirm_password: formData.confirmPassword,
    };

    const response = await axios.post(`/api/v1/users/register`, payload);

    if (response.status === 201) {
      message.value = `User "${response.data.username}" registered successfully! Please login.`;
      messageType.value = 'success';
      formData.username = '';
      formData.email = '';
      formData.password = '';
      formData.confirmPassword = '';
      emit('registrationSuccess');
    }
  } catch (error) {
    messageType.value = 'error';
    if (error.response && error.response.data) {
      if (error.response.data.detail && typeof error.response.data.detail === 'string') {
        message.value = error.response.data.detail;
      } else if (error.response.data.detail && Array.isArray(error.response.data.detail)) {
        let errorMsgSummary = "Please correct the validation errors below.";
        error.response.data.detail.forEach(err => {
          const field = err.loc[1];
          if (errors[field]) { // Append if error already exists (e.g. from client-side)
            errors[field] += ` ${err.msg}`;
          } else {
            errors[field] = err.msg;
          }
        });
        message.value = errorMsgSummary;
      } else {
        message.value = 'An unexpected error occurred during registration.';
      }
    } else {
      message.value = 'Network error or server is unreachable.';
    }
    console.error('Registration error:', error);
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
/* Scoped styles for RegistrationForm specifically, if needed */
</style>