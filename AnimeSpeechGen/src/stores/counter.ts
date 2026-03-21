import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { loginApi, logoutApi } from '@/api'
import type { LoginForm, LoginResponseData } from '@/util/types'

type StoredUser = {
  username: string
  avatar: string
  uid: string
  rate: string
  signature?: string
  profileBanner?: string
  birthday?: string
  gender?: string
}

const emptyUser = (): StoredUser => ({
  username: '',
  avatar: '',
  uid: '',
  rate: '',
  signature: '',
  profileBanner: '',
  birthday: '',
  gender: '',
})

const parseStoredUser = (): StoredUser => {
  const rawUser = localStorage.getItem('user')
  if (!rawUser) return emptyUser()

  try {
    return JSON.parse(rawUser) as StoredUser
  } catch {
    return emptyUser()
  }
}

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
    token: localStorage.getItem('token') || '',
    user: parseStoredUser(),
  }),

  getters: {
    getUserInfo: (state) => state.user,
    getUsername: (state) => state.user?.username || 'Guest',
  },

  actions: {
    async login(data: LoginForm): Promise<LoginResponseData> {
      const res = await loginApi(data)
      this.token = res.token
      this.user = {
        username: res.username,
        avatar: res.avatar,
        uid: res.uid,
        rate: res.rate,
      }
      localStorage.setItem('token', res.token)
      localStorage.setItem('user', JSON.stringify(this.user))
      return res
    },

    async logout() {
      try {
        await logoutApi()
      } finally {
        this.clearState()
      }
    },

    clearState() {
      this.token = ''
      this.user = emptyUser()
      localStorage.removeItem('token')
      localStorage.removeItem('user')
    },

    /**
     * 更新当前登录用户的本地资料信息，并同步写回 localStorage。
     * @param profilePatch 允许局部更新昵称、头像、评级、签名、横幅图、生日与性别。
     */
    updateProfile(
      profilePatch: Partial<
        Pick<
          StoredUser,
          'username' | 'avatar' | 'uid' | 'rate' | 'signature' | 'profileBanner' | 'birthday' | 'gender'
        >
      >,
    ) {
      this.user = {
        ...this.user,
        ...profilePatch,
      }
      localStorage.setItem('user', JSON.stringify(this.user))
    },
  },
})
