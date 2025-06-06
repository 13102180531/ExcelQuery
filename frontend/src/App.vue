<template>
  <div id="app-shell"> <!-- This is the root element of your App.vue component -->
    <div v-if="!isAuthenticated" class="auth-wrapper">
      <!-- LoginForm and RegistrationForm will use classes like .form-card from main.css -->
      <LoginForm v-if="showLogin" @login-success="handleAuthSuccess" @switch-to-register="showLogin = false" />
      <RegistrationForm v-else @registration-success="handleRegistrationSuccess" @switch-to-login="showLogin = true" />
    </div>
    <ExcelQueryTool v-else :current-username="username" @user-logout="handleLogout" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { jwtDecode } from 'jwt-decode'; // Ensure: npm install jwt-decode

// Import your components
import LoginForm from './components/LoginForm.vue'; // Ensure path is correct
import RegistrationForm from './components/RegistrationForm.vue'; // Ensure path is correct
import ExcelQueryTool from './components/ExcelQueryTool.vue'; // Ensure path is correct

const showLogin = ref(true);
const isAuthenticated = ref(false);
const username = ref('');

const checkAuth = () => {
  const token = localStorage.getItem('authToken');
  if (token) {
    try {
      const decodedToken = jwtDecode(token);
      const currentTime = Date.now() / 1000;

      if (decodedToken.exp < currentTime) {
        console.warn("Token expired. Logging out.");
        handleLogout();
        return;
      }
      username.value = decodedToken.sub || decodedToken.username || 'User';
      isAuthenticated.value = true;
      console.log("User authenticated:", username.value);
    } catch (error) {
      console.error("Invalid token or token decoding error:", error);
      handleLogout();
    }
  } else {
    isAuthenticated.value = false;
    username.value = '';
    console.log("No auth token found.");
  }
};

onMounted(() => {
  checkAuth();
  window.addEventListener('storage', (event) => {
    if (event.key === 'authToken' || (event.key === null && !localStorage.getItem('authToken'))) {
      console.log("AuthToken changed in another tab, re-checking auth.");
      checkAuth();
    }
  });
});

const handleAuthSuccess = () => {
  console.log("Login successful.");
  checkAuth();
};

const handleRegistrationSuccess = () => {
  console.log("Registration successful. Please log in.");
  showLogin.value = true;
};

const handleLogout = () => {
  console.log("Logging out user.");
  localStorage.removeItem('authToken');
  isAuthenticated.value = false;
  username.value = '';
  showLogin.value = true;
};
</script>

<style>
/*
  These are global styles specific to App.vue's structure.
  The main.css file provides more general resets and utility styles.
  The styles for html, body from main.css should be sufficient.
  If there's any conflict, ensure the desired styles are applied.
*/

#app-shell { /* This is the root element within #app for App.vue */
  height: 100%;
  width: 100%;
  display: flex;
  flex-direction: column;
  /* background-color will be inherited from body/html (set in main.css) */
}

/* Styles for the authentication view wrapper */
.auth-wrapper {
  display: flex;
  flex-direction: column; /* To stack elements like a title above the form card */
  justify-content: center;
  align-items: center;
  flex-grow: 1; /* Takes up all available space when auth forms are shown */
  width: 100%;
  padding: 20px; /* Padding around the centered content */
  box-sizing: border-box;
  /* background-color: #f0f2f5; -- Inherited from body, or set if different for this view */
}

/*
  When ExcelQueryTool is rendered (v-else branch):
  - It will be a direct child of #app-shell.
  - #app-shell is 100% width and 100% height (filling #app).
  - ExcelQueryTool's root element (.excel-query-tool-page) is styled in its own
    component for 100% width and height to fill #app-shell.
*/
</style>