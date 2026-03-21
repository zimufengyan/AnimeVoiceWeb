<template>
  <!-- 左侧 LOGO 和网站标题 -->
  <div class="header">
    <div class="header-left">
      <img src="@/assets/logo.svg" alt="Logo" class="logo" />
      <span class="title">AnimeVoice</span>
    </div>

    <!-- 右侧 用户信息或登录/注册按钮 -->
    <div class="header-right">
      <template v-if="isLoggedIn">
        <!-- 用户中心：头像和昵称展示 -->
        <div class="quick-rate">
          <svg
            class="svg-icon-rate"
            xmlns="http://www.w3.org/2000/svg"
            xmlns:xlink="http://www.w3.org/1999/xlink"
            width="32"
            height="32"
            viewBox="0 0 32 32"
          >
            <path v-if="user.rate == 'S'"
              d="M21.4269 9.9987 20.2135 9.9987Q19.896 6.9312 18.0023 4.8957L18.0023 4.8957Q15.8476 2.5653 12.1622 2.5653L12.1622 2.5653Q9.1911 2.5653 7.456 4.4761L7.456 4.4761Q6.0612 5.99 6.0612 8.1276L6.0612 8.1276Q6.0612 11.7734 11.3797 13.6671L11.3797 13.6671 12.4003 14.047Q18.8584 16.3774 20.7295 18.4923L20.7295 18.4923Q22.4872 20.4825 22.4872 23.2551L22.4872 23.2551Q22.4872 27.4623 19.0966 29.6736L19.0966 29.6736Q16.6244 31.3065 13.2168 31.3065L13.2168 31.3065Q9.4859 31.3065 6.2767 29.2767L6.2767 29.2767Q5.3638 28.6586 4.8422 28.6586L4.8422 28.6586Q4.1051 28.6586 4.1051 30.49L4.1051 30.49 2.852 30.49 2.852 20.9814 4.0257 20.9814Q4.468 24.7293 6.4411 26.9009L6.4411 26.9009Q9.0323 29.6736 13.2168 29.6736L13.2168 29.6736Q15.9894 29.6736 17.6224 28.1597L17.6224 28.1597Q19.3744 26.5834 19.3744 23.8731L19.3744 23.8731Q19.3744 21.8376 17.9002 20.2443L17.9002 20.2443Q16.5621 18.8268 12.3209 17.0975L12.3209 17.0975 11.5441 16.7743Q7.0988 15.062 5.6983 14.0073L5.6983 14.0073Q3.1298 12.0342 3.1298 8.825L3.1298 8.825Q3.1298 5.1962 5.8231 3.0642L5.8231 3.0642Q8.2725 1.0911 12.0374 1.0911L12.0374 1.0911Q15.3317 1.0911 18.5409 2.8601L18.5409 2.8601Q19.2156 3.24 19.5161 3.24L19.5161 3.24Q20.0945 3.24 20.1512 1.5844L20.1512 1.5844 21.4269 1.5844 21.4269 9.9987Z"
              fill="#E1B85E"
              stroke="#E1B85E"
              stroke-width="0.2"
            ></path>
            <path v-else-if="user.rate == 'A'"
              d="M30.1425 32.6887 33.4432 32.6887 33.4432 34.0995 22.5083 34.0995 22.5083 32.6887 25.9575 32.6887Q25.377 30.5963 24.648 28.5105L24.648 28.5105 22.7512 22.4355 13.1798 22.4355Q11.2357 28.2675 9.8723 32.6887L9.8723 32.6887 14.442 32.6887 14.442 34.0995 4.236 34.0995 4.236 32.6887 7.4422 32.6887 18.4245 1.5848 19.8825 1.2945Q28.3875 27.147 30.1425 32.6887L30.1425 32.6887ZM13.8615 20.4375 22.1235 20.4375 18.087 7.7543 13.8615 20.4375Z"
              fill="#E1B85E"
              stroke="#E1B85E"
              stroke-width="0.2"
            ></path>
            <path v-else-if="user.rate == 'B'"
              d="M20.5464 30.2 20.5464 30.2 7.6328 30.2 7.6328 29.4104Q11.4128 29.7296 11.0936 26.8904L11.0936 26.8904 11.0936 5.3136Q11.4128 2.3232 7.6328 2.6368L7.6328 2.6368 7.6328 1.8472 19.9136 1.8472Q28.7336 1.8472 28.8904 8.4664L28.8904 8.4664Q28.8904 13.0304 23.0664 15.08L23.0664 15.08Q30.1504 16.8104 30.1504 22.4832L30.1504 22.4832Q29.9936 30.0432 20.5464 30.2ZM20.0704 15.7072 20.0704 15.7072 13.6136 15.7072 13.6136 26.7336Q13.4568 29.4104 16.4528 29.2536L16.4528 29.2536 20.2328 29.2536Q27.16 28.94 27.4736 22.4832L27.4736 22.4832Q27.0032 16.1832 20.0704 15.7072ZM19.7568 2.9504 19.7568 2.9504 16.4528 2.9504Q13.4568 2.7936 13.6136 5.4704L13.6136 5.4704 13.6136 14.7664 20.0704 14.7664Q25.9 14.2904 26.2136 8.3096L26.2136 8.3096Q26.0568 3.1072 19.7568 2.9504Z"
              fill="#E1B85E"
              stroke="#E1B85E"
              stroke-width="0.2"
            ></path>
            <path v-else-if="user.rate == 'C'"
              d="M25.705 23.084 28.026 23.084 28.0645 29.893Q24.0825 32.137 19.2095 32.137L19.2095 32.137Q12.439 32.137 8.1655 28.034 4.2 23.7 4.2 16.55L4.2 16.55Q4.2 9.4 8.3415 5.4345 12.791 1.315 19.402 1.315L19.402 1.315Q23.8515 1.315 27.7565 3.515L27.7565 3.515 27.6795 10.3625 25.397 10.3625 23.659 3.5975Q22.031 2.9375 20.1005 2.9375L20.1005 2.9375Q15.497 2.9375 12.6535 6.474 8.6 9.95 8.6 16.55L8.6 16.55Q9.15 23.7 12.615 27.011 15.75 29.75 20.1005 30.509L20.1005 30.509Q22.031 30.509 23.967 29.7775L23.967 29.7775 25.705 23.084Z"
              fill="#E1B85E"
              stroke="#E1B85E"
              stroke-width="0.2"
            ></path>
            <path v-else-if="user.rate == 'D'"
              d="M1.13 31.185Q13.3679 31.2249 15.0494 31.1052L15.0494 31.1052Q21.821 30.7062 25.6115 26.7162 29.06 22.635 29.06 16.365L29.06 16.365Q29.06 9.525 26.0105 5.5749 22.5848 1.6077 16.4516 1.0434L16.4516 1.0434Q15.4541.9636 8.5172.9636L1.13.975 2.27 2.685Q4.0313 2.6508 4.5899 2.8275 5.1485 3.0099 5.3537 3.4488L5.3537 3.4488Q5.4734 3.7737 5.5532 13.1673 5.633 22.5666 5.5532 26.3742L5.5532 26.3742Q5.4734 28.62 5.1941 28.9791 4.9091 29.3439 2.27 29.475ZM15.3686 29.3439 15.3686 29.3439Q10.6433 29.3439 10.4438 28.8993L10.4438 28.8993 10.4438 3.2094Q10.8029 2.4513 13.67 2.571 16.5314 2.6907 18.3383 3.5685L18.3383 3.5685Q24.2663 6.3786 24.2663 16.0344L24.2663 16.0344Q24.2663 27.9759 15.3686 29.3439Z"
              fill="#E1B85E"
              stroke="#E1B85E"
              stroke-width="0.2"
            ></path>
          </svg>
        </div>

        <el-popover trigger="click" placement="bottom">
          <!-- 头像点击弹出 -->
          <span class="user-center">
            <el-avatar class="avatar_icon" :size="32" :src="user.avatar" alt="user avatar" />
            <span class="username">{{ username }}</span>
          </span>
          <template #reference>
            <span class="user-center">
              <el-avatar class="avatar_icon" :size="32" :src="user.avatar" alt="user avatar" />
              <span class="username">{{ user.username }}</span>
            </span>
          </template>

          <!-- 弹出内容 -->
          <el-menu>
            <el-menu-item @click="goToProfile">个人中心</el-menu-item>
            <el-menu-item @click="logout">退出登录</el-menu-item>
          </el-menu>
        </el-popover>
      </template>
      <template v-else>
        <!-- 未登录状态：登录和注册按钮 -->
        <el-button type="primary" @click="goToLogin" title="login">登录</el-button>
        <el-button type="success" @click="goToRegister" title="register">注册</el-button>
      </template>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useUserStore } from '@/stores/counter'
const router = useRouter()
const userStore = useUserStore()
const { token, user } = storeToRefs(userStore)

const isLoggedIn = computed(() => token.value !== '')
const username = computed(() => user.value?.username || 'Guest')

// 跳转到登录页
const goToLogin = () => {
  // 实现登录逻辑或页面跳转
  console.log('跳转到登录页')
  router.push('/login')
}

// 跳转到注册页
const goToRegister = () => {
  // 实现注册逻辑或页面跳转
  console.log('跳转到注册页')
  router.push('/register')
}

// 跳转到个人中心页面
const goToProfile = () => {
  router.push('/profile')
}

const logout = () => {
  userStore.logout() // 调用 store 中的登出方法
  router.push('/login') // 跳转到登录页面
}
</script>

<style scoped>
.header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.header-left {
  display: flex;
  align-items: center;
  margin-left: 10px;
}

.logo {
  width: 35px;
  height: 35;
  margin-right: 10px;
}

.title {
  font-size: 18px;
  font-weight: bold;
}

.header-right {
  display: flex;
  align-items: center;
  margin-right: 10px;
}

.user-center {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.avatar_icon {
  margin-right: 10px;
}

.username {
  font-size: 16px;
  color: #333;
  margin-right: 4px;
}

.quick-rate {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-right: 10px;
}

.svg-icon-rate {
  opacity: 1;
  fill: #e1b85e;
}
</style>
