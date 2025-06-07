<template>
  <div class="authenticated-layout">
    <AppHeader
      :username="username"
      :is-logged-in="true"
      title="通用Excel智能查询工具"
      @logout="performLogout"
    />
    <div class="authenticated-layout-content">
      <router-view :current-username="username" @user-logout="performLogout" />
      <!-- Passing currentUsername and handling user-logout for child components -->
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import AppHeader from '../components/AppHeader.vue';
import { jwtDecode } from 'jwt-decode';

const router = useRouter();
const username = ref('');

const updateUsernameFromToken = () => {
  const token = localStorage.getItem('authToken');
  if (token) {
    try {
      const decoded = jwtDecode(token);
      username.value = decoded.sub;
    } catch (e) {
      console.error("Error decoding token in layout:", e);
      performLogout(); // Log out if token is invalid
    }
  } else {
    username.value = ''; // Clear username if no token
  }
};

onMounted(() => {
  updateUsernameFromToken();
});

// Watch for token changes (e.g., login in another tab)
// This is a bit advanced; simpler is App.vue re-checking auth.
// For now, App.vue's logic will handle the main auth state.
// This layout assumes it's only rendered when authenticated.

const performLogout = () => {
  localStorage.removeItem('authToken');
  localStorage.removeItem('tokenType');
  username.value = '';
  // Instead of directly manipulating App.vue state, we let App.vue handle it.
  // The router guard or App.vue's logic will redirect/re-render.
  // For this setup, App.vue will detect the change via its own checkAuth
  // when the user tries to navigate or an event occurs.
  // We can also force a navigation that App.vue will intercept.
  // A simple way is to just reload, App.vue will then show login.
  window.location.reload(); // Simplest way to trigger App.vue's auth check
};
</script>

<style scoped>
.authenticated-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100vw;
  overflow: hidden; /* Layout itself doesn't scroll */
}

.authenticated-layout-content {
  flex-grow: 1; /* Takes all space below header */
  overflow: hidden; /* This content wrapper doesn't scroll, its child (router-view's component) will */
  display: flex; /* Allow child to take full height */
  flex-direction: column; /* Allow child to take full height */
}
/* The component rendered by router-view (e.g., ExcelQueryTool or SettingsPage)
   will need to be styled with height: 100% and overflow: auto if it needs to scroll its own content */
</style>