import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

import GenShin from '@/views/GenShin.vue'
import StarRail from '@/views/StarRail.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import SeachHome from '@/views/SeachHome.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: HomeView,
      children: [
        { path: '', name: 'home', component: SeachHome },
        {
          path: 'genshin',
          name: 'genshin',
          component: GenShin,
        },
        {
          path: 'starrail',
          name: 'starrail',
          component: StarRail,
        },
      ],
    },

    {
      path: '/login',
      name: 'login',
      component: Login,
    },
    {
      path: '/register',
      name: 'register',
      component: Register,
    },
  ],
})

export default router
