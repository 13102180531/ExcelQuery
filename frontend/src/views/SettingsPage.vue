<template>
  <div class="settings-page-layout">
    <SettingsSidebar class="settings-sidebar" />
    <main class="settings-content-area">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import SettingsSidebar from '../components/settings/SettingsSidebar.vue';
</script>

<style scoped>
.settings-page-layout {
  display: flex;
  height: 100%; /* Fill the .authenticated-layout-content */
  width: 100%;
  overflow: hidden; /* Layout itself doesn't scroll */
  background-color: #e9ecef; /* Light background for settings area */
}

.settings-sidebar {
  width: 220px; /* Fixed width for sidebar */
  flex-shrink: 0;
  background-color: #ffffff;
  border-right: 1px solid #dee2e6;
  padding: 20px 0; /* Vertical padding, no horizontal */
  height: 100%; /* Full height of parent */
  overflow-y: auto; /* Scroll sidebar if many items */
}

.settings-content-area {
  flex-grow: 1; /* Takes remaining space */
  padding: 25px;
  overflow-y: auto; /* Allows the content of the current settings view to scroll */
  height: 100%; /* Full height of parent */
  box-sizing: border-box;
}
</style>