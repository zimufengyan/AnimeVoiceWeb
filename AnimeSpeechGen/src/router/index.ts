import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'
import AuthRouteBridge from '@/views/AuthRouteBridge.vue'
import SeachHome from '@/views/SeachHome.vue'
import VoiceGenerationView from '@/views/VoiceGenerationView.vue'
import ProfileView from '@/views/ProfileView.vue'
import { voiceIpConfigs } from '@/config/voiceIp'

/**
 * 根据统一的 IP 配置生成语音生成页路由，避免为每个 IP 维护一份重复 view。
 */
const voiceIpRoutes = voiceIpConfigs.map((config) => ({
  path: config.routePath.replace(/^\//, ''),
  name: config.routeName,
  component: VoiceGenerationView,
  props: {
    belong: config.belong,
  },
}))

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: HomeView,
      children: [
        { path: '', name: 'home', component: SeachHome },
        { path: 'profile', name: 'profile', component: ProfileView },
        ...voiceIpRoutes,
      ],
    },

    {
      path: '/login',
      name: 'login',
      component: AuthRouteBridge,
      props: {
        mode: 'login',
      },
    },
    {
      path: '/register',
      name: 'register',
      component: AuthRouteBridge,
      props: {
        mode: 'register',
      },
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: AuthRouteBridge,
      props: {
        mode: 'forgot-password',
      },
    },
  ],
})

export default router
