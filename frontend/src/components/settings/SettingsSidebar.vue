<template>
  <nav class="settings-navigation">
    <ul>
      <li>
        <router-link :to="{ name: 'ConfigOptionsSettings' }" active-class="active-link">
          配置选项
        </router-link>
      </li>
      <li>
        <router-link :to="{ name: 'UserGroupSettings' }" active-class="active-link">
          用户组
        </router-link>
      </li>
      <li>
        <router-link :to="{ name: 'ProfileSettings' }" active-class="active-link">
          个人信息
        </router-link>
      </li>
      <li>
        <router-link :to="{ name: 'ChangePasswordSettings' }" active-class="active-link">
          修改密码
        </router-link>
      </li>
    </ul>
  </nav>
</template>

<script setup>
// No script needed for simple navigation
</script>

<style scoped>
.settings-navigation ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.settings-navigation li a {
  display: block;
  padding: 12px 20px;
  text-decoration: none;
  color: #343a40;
  font-size: 0.95em;
  border-left: 3px solid transparent;
  transition: background-color 0.2s, border-left-color 0.2s;
}
.settings-navigation li a:hover {
  background-color: #f8f9fa;
}
.settings-navigation li a.active-link {
  background-color: #e9ecef;
  font-weight: 600;
  color: #007bff;
  border-left-color: #007bff;
}
</style>