// frontend/src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import ExcelQueryTool from '../components/ExcelQueryTool.vue';
import SettingsPage from '../views/SettingsPage.vue'; // We'll create this
import ConfigOptionsSettings from '../components/settings/ConfigOptionsSettings.vue'; // We'll create this
import UserGroupSettings from '../components/settings/UserGroupSettings.vue'; // Placeholder
import ProfileSettings from '../components/settings/ProfileSettings.vue'; // Placeholder
import ChangePasswordSettings from '../components/settings/ChangePasswordSettings.vue'; // Placeholder
import AuthenticatedLayout from '../layouts/AuthenticatedLayout.vue'; // We'll create this

const routes = [
  {
    path: '/',
    component: AuthenticatedLayout, // Use the layout for authenticated routes
    children: [
      {
        path: '', // Default child route for '/'
        name: 'ExcelTool',
        component: ExcelQueryTool,
        meta: { requiresAuth: true }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: SettingsPage,
        meta: { requiresAuth: true },
        children: [
          { path: '', redirect: { name: 'ConfigOptionsSettings' } }, // Default settings view
          { path: 'config', name: 'ConfigOptionsSettings', component: ConfigOptionsSettings },
          { path: 'user-groups', name: 'UserGroupSettings', component: UserGroupSettings },
          { path: 'profile', name: 'ProfileSettings', component: ProfileSettings },
          { path: 'change-password', name: 'ChangePasswordSettings', component: ChangePasswordSettings },
        ]
      }
    ],
    // Add a beforeEnter guard on the parent route if needed for all children
    beforeEnter: (to, from, next) => {
      const token = localStorage.getItem('authToken');
      if (to.meta.requiresAuth && !token) {
        // Redirect to a login page (which App.vue will handle by showing login forms)
        // For simplicity, we'll assume App.vue handles the actual login UI visibility
        // If you had a dedicated /login route, you'd redirect there.
        // For now, if no token, App.vue's logic will prevent access to AuthenticatedLayout.
        // This guard is more robust if AuthenticatedLayout wasn't directly tied to App.vue's isAuthenticated.
        // For this example, App.vue's v-if on AuthenticatedLayout serves a similar purpose.
        console.log("Router guard: Auth required, no token found for", to.fullPath);
        // Potentially emit an event or use a global state to signal App.vue to show login
        // For now, App.vue's own logic will handle showing login if no token.
        // This guard becomes more useful if App.vue doesn't directly control layout visibility.
        next(); // Allow App.vue to handle the display based on isAuthenticated
      } else {
        next();
      }
    }
  },
  // You would also define a /login route if you had a dedicated login page component
  // For now, App.vue handles showing login forms.
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
});

// Optional: Global navigation guard
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('authToken');
  if (to.meta.requiresAuth && !token && to.name !== 'Login') { // Assuming you might add a Login route
    console.log("Global guard: Redirecting to show login via App.vue's logic for", to.name);
    // If you had a login route: next({ name: 'Login' });
    // For now, allow App.vue to detect no token and show login forms.
    // If already on a path that App.vue will hide due to no auth, just proceed.
    // This logic depends on how App.vue handles unauthenticated state.
    // For simplicity, if no token, App.vue shows login, so we can just proceed.
    next();
  } else {
    next();
  }
});


export default router;