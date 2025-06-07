<template>
  <div class="settings-view-placeholder card">
    <h2>个人信息</h2>
    <p>此功能正在开发中。您可以在这里管理您的个人资料，例如更新您的显示名称或联系信息。</p>
    <!-- Example form fields (non-functional without backend) -->
    <form @submit.prevent="updateProfile">
      <div class="form-group">
        <label for="displayName">显示名称:</label>
        <input type="text" id="displayName" v-model="profile.displayName" placeholder="您的显示名称">
      </div>
      <div class="form-group">
        <label for="contactEmail">联系邮箱 (不可更改):</label>
        <input type="email" id="contactEmail" :value="props.currentUsername" disabled>
      </div>
      <button type="submit" class="btn btn-primary">保存更改</button>
      <p v-if="status" :class="isError ? 'error-message' : 'success-message'">{{ status }}</p>
    </form>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';

// This component would ideally get the current user's email/username via props
// or a global state if it's to display existing info.
// For now, let's assume App.vue or AuthenticatedLayout passes currentUsername
const props = defineProps({
  currentUsername: String // Assuming this will be the email or username
});

const profile = reactive({
  displayName: '',
  // email: props.currentUsername // Can't directly assign prop to reactive like this for initial value
});
const status = ref('');
const isError = ref(false);

onMounted(() => {
    // Fetch current profile data if applicable, or set defaults
    // For now, we'll use the prop if available for email, and user can set display name
    if (props.currentUsername) {
        // profile.email = props.currentUsername; // This is not directly editable
    }
});

const updateProfile = () => {
  status.value = '个人信息更新功能待实现。';
  isError.value = false;
  console.log("Profile update attempt:", JSON.parse(JSON.stringify(profile)));
  // Here you would make an API call to update the profile
};
</script>

<style scoped>
.settings-view-placeholder { padding: 25px; background-color: #fff; border-radius: 8px; }
.card h2 { margin-top:0; margin-bottom: 20px; font-size: 1.4em; color: #34495e; }
.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 5px; font-weight: 500; }
.form-group input[type="text"], .form-group input[type="email"] {
  width: 100%;
  max-width: 400px; /* Limit width of input fields */
  padding: 8px 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
.form-group input[disabled] {
  background-color: #e9ecef;
  cursor: not-allowed;
}
.btn-primary {
  background-color: #007bff; color: white; padding: 10px 15px;
  border: none; border-radius: 4px; cursor: pointer;
}
.btn-primary:hover { background-color: #0056b3; }
.status-message { margin-top: 15px; }
.error-message { color: red; }
.success-message { color: green; }
</style>