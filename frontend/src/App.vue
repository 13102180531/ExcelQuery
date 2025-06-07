<template>
  <div id="app-shell">
    <div v-if="!isAuthenticated" class="auth-wrapper">
      <LoginForm v-if="showLogin" @login-success="handleAuthSuccess" @switch-to-register="showLogin = false" />
      <RegistrationForm v-else @registration-success="handleRegistrationSuccess" @switch-to-login="showLogin = true" />
    </div>
    <router-view v-else :key="$route.fullPath" />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { jwtDecode } from 'jwt-decode';

// --- ADD THESE IMPORTS ---
import LoginForm from './components/LoginForm.vue';
import RegistrationForm from './components/RegistrationForm.vue';
// --- END OF ADDED IMPORTS ---

const router = useRouter();
const route = useRoute();

const showLogin = ref(true);
const isAuthenticated = ref(false);

const checkAuthAndRedirect = () => {
  const token = localStorage.getItem('authToken');
  let validToken = false;
  if (token) {
    try {
      const decodedToken = jwtDecode(token);
      const currentTime = Date.now() / 1000;
      if (decodedToken.exp > currentTime) {
        validToken = true;
      } else {
        console.warn("App.vue: Token expired during App.vue checkAuth");
      }
    } catch (error) {
      console.error("App.vue: Invalid token during App.vue checkAuth:", error);
    }
  }

  isAuthenticated.value = validToken;

  if (!validToken && route.meta.requiresAuth) {
    // If not authenticated and trying to access a protected route,
    // App.vue will show login forms due to `isAuthenticated` being false.
    // The router guard might also redirect to a dedicated login page if you had one.
    // For now, the v-if/v-else in the template handles showing login forms.
    console.log("App.vue: Not authenticated, login forms will be shown.");
  } else if (validToken && !route.meta.requiresAuth && route.path === '/login') { // Example if you had a /login route
    // If authenticated and somehow on a login page, redirect to home
    // router.push({ name: 'ExcelTool' }); // Or router's default authenticated route
  }
};


onMounted(() => {
  checkAuthAndRedirect();
  window.addEventListener('storage', (event) => {
    if (event.key === 'authToken' || (event.key === null && !localStorage.getItem('authToken'))) {
      checkAuthAndRedirect();
    }
  });
});

watch(route, () => {
  // Re-check auth on route change, especially if navigating back/forward
  // or if router guards are not fully handling all cases.
  checkAuthAndRedirect();
});

const handleAuthSuccess = () => {
  checkAuthAndRedirect();
  router.push({ name: 'ExcelTool' }); // Ensure this matches a route name in your router config
};

const handleRegistrationSuccess = () => {
  showLogin.value = true;
};

const handleLogout = () => { // This is called by AuthenticatedLayout via router-view's emit
  localStorage.removeItem('authToken');
  localStorage.removeItem('tokenType');
  checkAuthAndRedirect(); // This will set isAuthenticated to false
  // No explicit redirect to login needed if App.vue shows forms when !isAuthenticated
};
</script>

<style>
/* ... your existing App.vue styles ... */
html, body { height: 100%; width: 100%; margin: 0; padding: 0; font-family: sans-serif; }
#app-shell {
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
}
.auth-wrapper {
  display: flex; justify-content: center; align-items: center;
  flex-grow: 1; width: 100%; padding: 20px; box-sizing: border-box;
  background-color: #f0f2f5;
}
</style>