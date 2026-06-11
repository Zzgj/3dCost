import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/inventory' },
    { path: '/inventory', component: () => import('@/views/Inventory.vue') },
    { path: '/purchases', component: () => import('@/views/Purchases.vue') },
    { path: '/settings', component: () => import('@/views/Settings.vue') },
  ],
})

export default router
