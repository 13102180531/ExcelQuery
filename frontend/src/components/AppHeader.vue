<template>
  <header class="app-global-header">
    <div
      class="navigate-button"
      @click="navigateToHome"
      title="返回主页"
    >
      <h1 class="app-title">{{ title || "Excel智能查询" }}</h1>
    </div>
    <div class="header-content-right">
      <span v-if="username" class="username-display-header">欢迎, {{ username }}</span>
      <button @click="navigateToSettings" class="navigate-button" title="设置">
        ⚙️
      </button>
      <button @click="handleLogout" class="logout-button-main-header">退出登录</button>
    </div>
  </header>
</template>

<script setup>
// defineProps, defineEmits are automatically available
import { useRouter } from 'vue-router';

const props = defineProps({
  title: String,
  username: String,
  // isLoggedIn: Boolean // Can be inferred if this header is only shown when logged in
});

const emit = defineEmits(['logout']);
const router = useRouter();

const handleLogout = () => {
  emit('logout');
};

const navigateToHome = () => {
  router.push({ path: '/' });
};

const navigateToSettings = () => {
  router.push({ name: 'Settings' });
};
</script>

<style scoped>
.app-global-header {
  background-color: #2c3e50;
  color: white;
  padding: 0 20px; /* Adjusted padding */
  height: 55px; /* Adjusted height */
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  width: 100%;
  box-sizing: border-box;
  flex-shrink: 0;
}

.header-content-left, .header-content-right {
  display: flex;
  align-items: center;
}

.header-content-right {
  gap: 15px; /* Space between items */
}

.app-title { margin: 0; font-size: 1.3em; font-weight: 500; }
.username-display-header { font-size: 0.85em; color: #bdc3c7; }

.navigate-button, .logout-button-main-header {
  background: none;
  border: none;
  color: #ecf0f1;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  font-size: 0.9em; /* Adjust icon size by font-size if using text icon */
  transition: background-color 0.2s, color 0.2s;
}
.navigate-button:hover, .logout-button-main-header:hover {
  background-color: rgba(255, 255, 255, 0.1);
}
.logout-button-main-header {
  border: 1px solid #7f8c8d;
  padding: 6px 10px;
}
.logout-button-main-header:hover {
  background-color: #c0392b;
  border-color: #c0392b;
}
.navigate-button {
    font-size: 1.2em; /* For emoji icon */
}

</style>