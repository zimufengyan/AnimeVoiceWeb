<template>
  <header class="site-header">
    <div class="header-shell">
      <button type="button" class="brand-link" @click="goHome">
        <span class="brand-mark">
          <img :src="logoUrl" alt="AnimeVoice logo" class="brand-logo" />
        </span>
        <span class="brand-copy">
          <strong class="brand-title">AnimeVoice</strong>
          <span class="brand-subtitle">多 IP 角色语音工坊</span>
        </span>
      </button>

      <div class="header-actions">
        <template v-if="isLoggedIn">
          <span :class="['rate-pill', rateClass]">{{ displayRate }}</span>

          <el-dropdown placement="bottom-end" trigger="click" popper-class="header-user-dropdown">
            <button type="button" class="user-trigger">
              <el-avatar :size="36" :src="user.avatar" class="user-avatar">
                {{ username.slice(0, 1).toUpperCase() }}
              </el-avatar>
              <span class="user-copy">
                <strong>{{ username }}</strong>
                <span>{{ user.uid ? `UID ${user.uid}` : '已登录' }}</span>
              </span>
            </button>

            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="goToProfile">个人中心</el-dropdown-item>
                <el-dropdown-item @click="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </template>

        <template v-else>
          <el-button class="header-btn ghost" @click="openLogin">登录</el-button>
          <el-button class="header-btn primary" @click="openRegister">注册</el-button>
        </template>
      </div>
    </div>
  </header>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import logoUrl from '@/assets/logo.svg'
import { useUserStore } from '@/stores/counter'
import { openAuthDialog } from '@/composables/useAuthDialog'

const router = useRouter()
const userStore = useUserStore()
const { token, user } = storeToRefs(userStore)

const isLoggedIn = computed(() => token.value !== '')
const username = computed(() => user.value?.username || 'Guest')
const displayRate = computed(() => user.value?.rate || 'A')
const rateClass = computed(() => {
  const currentRate = (displayRate.value || '').trim().toUpperCase()
  if (currentRate === 'S') return 'rate-s'
  if (currentRate === 'A') return 'rate-a'
  if (currentRate === 'B') return 'rate-b'
  if (currentRate === 'C') return 'rate-c'
  return 'rate-d'
})

const goHome = () => {
  router.push('/')
}

const openLogin = () => {
  openAuthDialog('login', {
    redirectTo: router.currentRoute.value.fullPath,
  })
}

const openRegister = () => {
  openAuthDialog('register', {
    redirectTo: router.currentRoute.value.fullPath,
  })
}

const goToProfile = () => {
  router.push('/profile')
}

const logout = async () => {
  await userStore.logout()
  router.push('/')
}
</script>

<style scoped>
.site-header {
  position: fixed;
  top: 0;
  left: 0;
  z-index: 1100;
  width: 100%;
  pointer-events: none;
  background: transparent;
}

.site-header::after {
  content: '';
  position: absolute;
  inset: 0 0 auto 0;
  height: 92px;
  pointer-events: none;
  background: linear-gradient(180deg, rgba(237, 244, 246, 0.16), rgba(237, 244, 246, 0));
}

.header-shell {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  width: 100%;
  max-width: none;
  margin: 0 auto;
  padding: 16px clamp(1rem, 2vw, 2rem) 14px;
  border-radius: 0;
  pointer-events: auto;
  background: transparent;
  box-shadow: none;
  backdrop-filter: none;
}

.brand-link {
  display: inline-flex;
  align-items: center;
  gap: 14px;
  border: none;
  padding: 0;
  background: transparent;
  cursor: pointer;
}

.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  border-radius: 18px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.76), rgba(237, 246, 247, 0.48));
  box-shadow:
    0 10px 22px rgba(35, 74, 92, 0.08),
    inset 0 0 0 1px rgba(173, 220, 221, 0.48);
  backdrop-filter: blur(10px);
}

.brand-logo {
  width: 30px;
  height: 30px;
}

.brand-copy {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 2px;
}

.brand-title {
  color: #14384c;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.brand-subtitle {
  color: #688390;
  font-size: 12px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-right: clamp(0.2rem, 0.5vw, 0.45rem);
}

.header-btn {
  min-width: 88px;
  min-height: 42px;
  border-radius: 16px;
  font-weight: 600;
}

.header-btn.ghost {
  color: #21465a;
  border-color: rgba(161, 207, 209, 0.82);
  background: rgba(255, 255, 255, 0.48);
  backdrop-filter: blur(10px);
}

.header-btn.primary {
  border: none;
  color: #103245;
  background: linear-gradient(135deg, rgba(124, 212, 204, 0.84), rgba(255, 210, 158, 0.8));
  box-shadow: 0 10px 20px rgba(93, 154, 161, 0.14);
  backdrop-filter: blur(10px);
}

.rate-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 42px;
  min-height: 36px;
  padding: 0 14px;
  border-radius: 999px;
  color: #17374b;
  font-size: 13px;
  font-weight: 700;
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.72),
    0 10px 18px rgba(35, 74, 92, 0.1);
}

.rate-s {
  background: linear-gradient(135deg, #fff3b7, #f3bb5b);
}

.rate-a {
  background: linear-gradient(135deg, #d8f2f0, #89d0cb);
}

.rate-b {
  background: linear-gradient(135deg, #dbe7ff, #9ab9ff);
}

.rate-c {
  background: linear-gradient(135deg, #dff5df, #9fd8a8);
}

.rate-d {
  background: linear-gradient(135deg, #ffe1dc, #f3b0a4);
}

.user-trigger {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-height: 56px;
  border: none;
  padding: 8px 10px 8px 8px;
  border-radius: 20px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.72), rgba(242, 249, 250, 0.54));
  box-shadow:
    0 10px 22px rgba(35, 74, 92, 0.08),
    inset 0 0 0 1px rgba(173, 220, 221, 0.46);
  cursor: pointer;
  backdrop-filter: blur(12px);
}

.user-avatar {
  box-shadow:
    0 10px 18px rgba(35, 74, 92, 0.16),
    0 0 0 2px rgba(255, 255, 255, 0.76);
}

.user-copy {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-width: 0;
}

.user-copy strong {
  max-width: 160px;
  overflow: hidden;
  color: #17374b;
  font-size: 14px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-copy span {
  color: #708895;
  font-size: 12px;
}

@media (max-width: 768px) {
  .site-header {
    top: 0;
  }

  .header-shell {
    width: 100%;
    padding: 12px 0.8rem 10px;
  }

  .brand-subtitle,
  .user-copy span {
    display: none;
  }

  .header-actions {
    gap: 10px;
    margin-right: 0.15rem;
  }

  .header-btn {
    min-width: 72px;
    min-height: 38px;
    padding: 0 14px;
  }

  .rate-pill {
    display: none;
  }

  .user-trigger {
    min-height: 48px;
    padding-right: 8px;
  }

  .user-copy strong {
    max-width: 86px;
  }
}

:global(.header-user-dropdown) {
  border-radius: 18px;
  border: 1px solid rgba(174, 214, 216, 0.54);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(242, 249, 250, 0.96));
  box-shadow: 0 18px 36px rgba(35, 74, 92, 0.12);
  overflow: hidden;
}

:global(.header-user-dropdown .el-dropdown-menu__item) {
  min-width: 132px;
  color: #21465a;
  font-weight: 600;
}

:global(.header-user-dropdown .el-dropdown-menu__item:not(.is-disabled):focus) {
  color: #163a4c;
  background: rgba(122, 210, 203, 0.16);
}
</style>
