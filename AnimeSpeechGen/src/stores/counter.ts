import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { loginApi, logoutApi } from '@/api'
import type { LoginForm } from '@/util/types'
import { ElMessage } from 'element-plus'; // 用于显示消息提示

export const useCounterStore = defineStore('counter', () => {
  const count = ref(0)
  const doubleCount = computed(() => count.value * 2)
  function increment() {
    count.value++
  }

  return { count, doubleCount, increment }
})


export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '', // 从 localStorage 获取初始 token
    user: JSON.parse(localStorage.getItem('user')) || { username: '', avatar: '', index: '', rate: '' },
  }),

  getters: {
    getUserInfo: (state) => state.user,
    getUsername: (state) => state.user?.username || 'Guest',
  },

  actions: {
    async login(data: LoginForm) {
      const res = await loginApi(data)
      console.log(res)
      const { code, token, username, avatar, index, rate, message } = res
      // 保存到状态和 localStorage
      this.token = token;
      this.user = { username, avatar, index, rate }; // 使用新结构保存用户信息
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(this.user));
      return res
    },

    async logout() {
      try {
        await logoutApi();
        this.clearState();
      } catch (error) {
        console.error('登出失败，但仍然清理状态:', error);
        this.clearState();
      }
    },

    // 清理状态
    clearState() {
      this.token = '';
      this.user = { username: '', avatar: '', index: '', rate: '' };
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    },
  },
  },
)




// export const useUserStore = defineStore('user', () => {
//   // 1.定义管理用户数据的state
//   const userInfo = ref()
//   // 2.定义获取接口数据的action函数
//   const getUserInfo = async (data: LoginForm) => {
//     const res = await reqLogin(data)
//     userInfo.value = res
//     return res
//   }
//   //3.以对象的格式把state和action return 出去
//   return {
//     userInfo,
//     getUserInfo
//   }
// }, {
//     persist: true,
//   }
// )
