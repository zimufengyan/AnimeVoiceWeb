<template>
  <el-dialog
    v-model="dialogVisible"
    class="auth-dialog"
    align-center
    :show-close="false"
    :lock-scroll="true"
    :close-on-click-modal="true"
  >
    <div class="auth-shell">
      <div class="auth-brand">
        <button type="button" class="brand-mark" @click="goHome">
          <img :src="logoUrl" alt="AnimeVoice logo" class="brand-logo" />
        </button>
        <div class="brand-copy">
          <span class="brand-title">AnimeVoice</span>
        </div>
        <button type="button" class="auth-close" @click="handleClose">
          <el-icon><Close /></el-icon>
        </button>
      </div>

      <el-alert
        v-if="authDialogState.reason && currentMode === 'login'"
        class="auth-notice"
        type="warning"
        :closable="false"
        show-icon
        title="登录状态已失效，请重新登录。"
      />

      <el-alert
        v-if="feedback.message"
        class="auth-feedback"
        :type="feedback.type"
        :closable="false"
        show-icon
        :title="feedback.message"
      />

      <div class="auth-body">
        <div class="auth-head">
          <h2 class="auth-head-title">{{ modeTitle }}</h2>
        </div>

        <el-form
          v-if="currentMode === 'login'"
          ref="loginFormRef"
          :model="loginForm"
          :rules="loginRules"
          size="large"
          class="auth-form"
          @keyup.enter="requestLogin"
        >
          <el-form-item prop="email">
            <el-input
              v-model="loginForm.email"
              :prefix-icon="Message"
              placeholder="邮箱账号"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              :prefix-icon="Lock"
              placeholder="密码"
              type="password"
              show-password
            />
          </el-form-item>

          <div class="auth-actions">
            <el-button type="primary" class="primary-action" @click="requestLogin">
              登录
            </el-button>
            <div class="secondary-links stacked">
              <button type="button" class="text-link" @click="switchMode('forgot-password')">
                忘记密码？
              </button>
              <button type="button" class="text-link strong" @click="switchMode('register')">
                还没有账号？<span>注册账号</span>
              </button>
            </div>
          </div>
        </el-form>

        <el-form
          v-else-if="currentMode === 'register'"
          ref="registerFormRef"
          :model="registerForm"
          :rules="registerRules"
          size="large"
          class="auth-form"
          @keyup.enter="submitRegister"
        >
          <el-form-item prop="email">
            <el-input
              v-model="registerForm.email"
              :prefix-icon="Message"
              placeholder="邮箱账号"
            />
          </el-form-item>
          <el-form-item prop="username">
            <el-input
              v-model="registerForm.username"
              :prefix-icon="User"
              placeholder="用户名"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="registerForm.password"
              :prefix-icon="Lock"
              placeholder="密码"
              type="password"
              show-password
            />
          </el-form-item>
          <el-form-item prop="repassword">
            <el-input
              v-model="registerForm.repassword"
              :prefix-icon="Lock"
              placeholder="确认密码"
              type="password"
              show-password
            />
          </el-form-item>
          <el-form-item prop="validationCode">
            <el-input
              v-model="registerForm.validationCode"
              placeholder="请输入验证码"
            >
              <template #suffix>
                <button
                  type="button"
                  class="code-trigger"
                  :disabled="registerCountdown > 0"
                  @click="sendRegisterCode"
                >
                  {{ registerCodeText }}
                </button>
              </template>
            </el-input>
          </el-form-item>

          <div class="auth-actions">
            <el-button type="primary" class="primary-action" @click="submitRegister">
              注册账号
            </el-button>
            <div class="secondary-links stacked">
              <button type="button" class="text-link strong" @click="switchMode('login')">
                已有账号？<span>返回登录</span>
              </button>
            </div>
          </div>
        </el-form>

        <el-form
          v-else
          ref="forgotFormRef"
          :model="forgotForm"
          :rules="forgotRules"
          size="large"
          class="auth-form"
          @keyup.enter="submitForgotPassword"
        >
          <el-form-item prop="email">
            <el-input
              v-model="forgotForm.email"
              :prefix-icon="Message"
              placeholder="邮箱账号"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="forgotForm.password"
              :prefix-icon="Lock"
              placeholder="新密码"
              type="password"
              show-password
            />
          </el-form-item>
          <el-form-item prop="repassword">
            <el-input
              v-model="forgotForm.repassword"
              :prefix-icon="Lock"
              placeholder="确认新密码"
              type="password"
              show-password
            />
          </el-form-item>
          <el-form-item prop="validationCode">
            <el-input
              v-model="forgotForm.validationCode"
              placeholder="请输入验证码"
            >
              <template #suffix>
                <button
                  type="button"
                  class="code-trigger"
                  :disabled="forgotCountdown > 0"
                  @click="sendForgotCode"
                >
                  {{ forgotCodeText }}
                </button>
              </template>
            </el-input>
          </el-form-item>

          <div class="auth-actions">
            <el-button type="primary" class="primary-action" @click="submitForgotPassword">
              重置密码
            </el-button>
            <div class="secondary-links stacked">
              <button type="button" class="text-link strong" @click="switchMode('login')">
                返回登录<span>重新输入账号密码</span>
              </button>
            </div>
          </div>
        </el-form>
      </div>
    </div>

    <DiyMask v-if="sliderVisible">
      <SlideVerify
        v-if="sliderVisible"
        @success="handleSlideSuccess"
        @close="handleSlideClose"
      />
    </DiyMask>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Close, Lock, Message, User } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElNotification } from 'element-plus'
import bcrypt from 'bcryptjs'
import logoUrl from '@/assets/logo.svg'
import SlideVerify from '@/components/SlideVerify.vue'
import DiyMask from '@/components/DiyMask.vue'
import { getSaltApi, registerApi, resetPasswordApi, sendEmailCodeApi, sendResetPasswordCodeApi } from '@/api'
import { useUserStore } from '@/stores/counter'
import { authDialogState, closeAuthDialog, switchAuthDialogMode, type AuthDialogMode } from '@/composables/useAuthDialog'
import type { LoginForm, RegisterForm, ResetPasswordForm } from '@/util/types'

type FeedbackState = {
  type: 'error' | 'success' | 'warning' | 'info'
  message: string
}

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const loginFormRef = ref<FormInstance>()
const registerFormRef = ref<FormInstance>()
const forgotFormRef = ref<FormInstance>()

const sliderVisible = ref(false)
const isLoginVerified = ref(false)

const loginForm = reactive<LoginForm>({
  email: '',
  password: '',
  salt: '',
})

const registerForm = reactive<RegisterForm>({
  email: '',
  username: '',
  password: '',
  repassword: '',
  validationCode: '',
  salt: '',
})

const forgotForm = reactive<ResetPasswordForm>({
  email: '',
  password: '',
  repassword: '',
  validationCode: '',
  salt: '',
})

const feedback = reactive<FeedbackState>({
  type: 'info',
  message: '',
})

const registerCountdown = ref(0)
const registerCodeSentOnce = ref(false)
const forgotCountdown = ref(0)
const forgotCodeSentOnce = ref(false)
let registerTimer: ReturnType<typeof setInterval> | null = null
let forgotTimer: ReturnType<typeof setInterval> | null = null

const dialogVisible = computed({
  get: () => authDialogState.visible,
  set: (value: boolean) => {
    if (!value) {
      handleClose()
    }
  },
})

const currentMode = computed(() => authDialogState.mode)
const modeTitle = computed(() => {
  if (currentMode.value === 'register') return '注册账号'
  if (currentMode.value === 'forgot-password') return '找回密码'
  return '登录'
})

const registerCodeText = computed(() => {
  if (registerCountdown.value > 0) {
    return `${registerCountdown.value}秒后重发`
  }
  return registerCodeSentOnce.value ? '重新发送验证码' : '发送验证码'
})

const forgotCodeText = computed(() => {
  if (forgotCountdown.value > 0) {
    return `${forgotCountdown.value}秒后重发`
  }
  return forgotCodeSentOnce.value ? '重新发送验证码' : '发送验证码'
})

const loginRules = reactive<FormRules<LoginForm>>({
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
  ],
  password: [
    {
      required: true,
      message: '密码为 6 到 18 位',
      min: 6,
      max: 18,
      trigger: 'blur',
    },
  ],
})

const registerRules = reactive<FormRules<RegisterForm>>({
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为 3 到 20 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 20, message: '密码长度应为 8 到 20 个字符', trigger: 'blur' },
    {
      pattern: /^(?!.*[^a-zA-Z0-9]).*$/,
      message: '密码不能包含特殊字符',
      trigger: 'blur',
    },
    {
      pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      message: '密码必须包含大写字母、小写字母和数字',
      trigger: 'blur',
    },
  ],
  repassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== registerForm.password) {
          callback(new Error('两次输入的密码不一致'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
  validationCode: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
})

const forgotRules = reactive<FormRules<ResetPasswordForm>>({
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 20, message: '密码长度应为 8 到 20 个字符', trigger: 'blur' },
    {
      pattern: /^(?!.*[^a-zA-Z0-9]).*$/,
      message: '密码不能包含特殊字符',
      trigger: 'blur',
    },
    {
      pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      message: '密码必须包含大写字母、小写字母和数字',
      trigger: 'blur',
    },
  ],
  repassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== forgotForm.password) {
          callback(new Error('两次输入的密码不一致'))
          return
        }
        callback()
      },
      trigger: 'blur',
    },
  ],
  validationCode: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
})

const clearFeedback = () => {
  feedback.message = ''
  feedback.type = 'info'
}

const resetLoginState = () => {
  sliderVisible.value = false
  isLoginVerified.value = false
  loginForm.password = ''
  loginForm.salt = ''
}

const stopRegisterTimer = () => {
  if (registerTimer) {
    clearInterval(registerTimer)
    registerTimer = null
  }
}

const stopForgotTimer = () => {
  if (forgotTimer) {
    clearInterval(forgotTimer)
    forgotTimer = null
  }
}

const startCountdown = (
  countdownRef: typeof registerCountdown,
  timerSetter: 'register' | 'forgot',
) => {
  countdownRef.value = 60
  const timer = setInterval(() => {
    countdownRef.value -= 1
    if (countdownRef.value <= 0) {
      countdownRef.value = 0
      clearInterval(timer)
      if (timerSetter === 'register') {
        registerTimer = null
      } else {
        forgotTimer = null
      }
    }
  }, 1000)

  if (timerSetter === 'register') {
    registerTimer = timer
  } else {
    forgotTimer = timer
  }
}

const switchMode = (mode: AuthDialogMode, options: { email?: string } = {}) => {
  clearFeedback()
  sliderVisible.value = false
  isLoginVerified.value = false
  switchAuthDialogMode(mode, {
    redirectTo: authDialogState.redirectTo,
    email: options.email,
  })
}

const goHome = () => {
  router.push('/')
}

const handleClose = () => {
  sliderVisible.value = false
  closeAuthDialog()
}

const handleSlideSuccess = () => {
  sliderVisible.value = false
  isLoginVerified.value = true
  submitLogin()
}

const handleSlideClose = () => {
  sliderVisible.value = false
  isLoginVerified.value = false
}

const resolveRedirectTarget = () => {
  const currentPath = route.fullPath
  const redirectPath = authDialogState.redirectTo
  if (!redirectPath || redirectPath.startsWith('/login') || redirectPath.startsWith('/register') || redirectPath.startsWith('/forgot-password')) {
    return currentPath.startsWith('/login') || currentPath.startsWith('/register') || currentPath.startsWith('/forgot-password')
      ? '/'
      : currentPath
  }
  return redirectPath
}

const requestLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate((valid) => {
    if (!valid) return
    if (!isLoginVerified.value) {
      sliderVisible.value = true
      return
    }
    void submitLogin()
  })
}

const submitLogin = async () => {
  if (!loginForm.email || !loginForm.password) return
  clearFeedback()

  try {
    const saltResponse = await getSaltApi(loginForm.email)
    if (!saltResponse?.salt) return

    loginForm.salt = saltResponse.salt
    const loginPayload: LoginForm = {
      email: loginForm.email,
      password: bcrypt.hashSync(loginForm.password, saltResponse.salt),
      salt: saltResponse.salt,
    }

    await userStore.login(loginPayload)
    ElMessage({
      type: 'success',
      message: '登录成功',
    })

    const targetPath = resolveRedirectTarget()
    resetLoginState()
    closeAuthDialog()
    if (router.currentRoute.value.fullPath !== targetPath) {
      await router.replace(targetPath)
    }
  } catch (error: unknown) {
    feedback.type = 'error'
    feedback.message = error instanceof Error ? error.message : '登录失败，请稍后重试'
    isLoginVerified.value = false
  }
}

const sendRegisterCode = async () => {
  if (registerCountdown.value > 0 || !registerFormRef.value) return
  clearFeedback()

  try {
    await registerFormRef.value.validateField('email')
    const response = await sendEmailCodeApi(registerForm.email)
    registerCodeSentOnce.value = true
    stopRegisterTimer()
    startCountdown(registerCountdown, 'register')
    ElMessage({
      type: 'success',
      message: response.meta?.message || response.message || '验证码发送成功',
    })
  } catch (error: unknown) {
    if (error instanceof Error) {
      feedback.type = 'error'
      feedback.message = error.message
    }
  }
}

const submitRegister = async () => {
  if (!registerFormRef.value) return
  clearFeedback()

  registerFormRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      const encryptionSalt = bcrypt.genSaltSync(12)
      const hashedPassword = bcrypt.hashSync(registerForm.password, encryptionSalt)
      await registerApi({
        email: registerForm.email,
        username: registerForm.username,
        password: hashedPassword,
        repassword: hashedPassword,
        validationCode: registerForm.validationCode,
        salt: encryptionSalt,
      })

      ElMessage({
        type: 'success',
        message: '注册成功，请登录',
      })

      registerForm.password = ''
      registerForm.repassword = ''
      registerForm.validationCode = ''
      switchMode('login', { email: registerForm.email })
    } catch (error: unknown) {
      feedback.type = 'error'
      feedback.message = error instanceof Error ? error.message : '注册失败，请稍后重试'
    }
  })
}

const sendForgotCode = async () => {
  if (forgotCountdown.value > 0 || !forgotFormRef.value) return
  clearFeedback()

  try {
    await forgotFormRef.value.validateField('email')
    const response = await sendResetPasswordCodeApi(forgotForm.email)
    forgotCodeSentOnce.value = true
    stopForgotTimer()
    startCountdown(forgotCountdown, 'forgot')
    ElMessage({
      type: 'success',
      message: response.message || '验证码发送成功',
    })
  } catch (error: unknown) {
    if (error instanceof Error) {
      feedback.type = 'error'
      feedback.message = error.message
    }
  }
}

const submitForgotPassword = async () => {
  if (!forgotFormRef.value) return
  clearFeedback()

  forgotFormRef.value.validate(async (valid) => {
    if (!valid) return

    try {
      const encryptionSalt = bcrypt.genSaltSync(12)
      const hashedPassword = bcrypt.hashSync(forgotForm.password, encryptionSalt)
      await resetPasswordApi({
        email: forgotForm.email,
        password: hashedPassword,
        repassword: hashedPassword,
        validationCode: forgotForm.validationCode,
        salt: encryptionSalt,
      })

      ElMessage({
        type: 'success',
        message: '密码已重置，请重新登录',
      })

      forgotForm.password = ''
      forgotForm.repassword = ''
      forgotForm.validationCode = ''
      switchMode('login', { email: forgotForm.email })
    } catch (error: unknown) {
      feedback.type = 'error'
      feedback.message = error instanceof Error ? error.message : '重置失败，请稍后重试'
    }
  })
}

watch(
  () => [authDialogState.visible, authDialogState.mode, authDialogState.email] as const,
  ([visible, mode, email]) => {
    if (!visible) return

    clearFeedback()
    sliderVisible.value = false
    isLoginVerified.value = false

    if (mode === 'login' && email) {
      loginForm.email = email
    }
    if (mode === 'register' && email) {
      registerForm.email = email
    }
    if (mode === 'forgot-password' && email) {
      forgotForm.email = email
    }
  },
  { immediate: true },
)

watch(
  () => [loginForm.email, loginForm.password],
  () => {
    isLoginVerified.value = false
  },
)

onBeforeUnmount(() => {
  stopRegisterTimer()
  stopForgotTimer()
})
</script>

<style scoped>
.auth-dialog :deep(.el-dialog) {
  width: min(760px, calc(100vw - 24px));
  max-width: 760px;
  border-radius: 32px;
  padding: 0;
  overflow: hidden;
  border: 1px solid rgba(169, 214, 214, 0.56);
  background:
    radial-gradient(circle at top left, rgba(210, 244, 243, 0.86), transparent 30%),
    linear-gradient(180deg, rgba(247, 252, 252, 0.98), rgba(236, 246, 247, 0.98));
  box-shadow:
    0 28px 70px rgba(35, 74, 92, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.84);
  backdrop-filter: blur(24px);
}

.auth-dialog :deep(.el-dialog__header) {
  display: none;
}

.auth-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.auth-shell {
  position: relative;
  padding: 28px 28px 30px;
}

.auth-shell::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(135deg, rgba(97, 188, 187, 0.14), transparent 38%),
    radial-gradient(circle at bottom right, rgba(255, 216, 159, 0.18), transparent 26%);
  pointer-events: none;
}

.auth-brand,
.auth-notice,
.auth-feedback,
.auth-body {
  position: relative;
  z-index: 1;
}

.auth-brand {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 16px;
  align-items: center;
  margin-bottom: 20px;
}

.brand-mark,
.auth-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: transparent;
  cursor: pointer;
}

.brand-mark {
  width: 58px;
  height: 58px;
  border-radius: 20px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.92), rgba(236, 246, 247, 0.88));
  box-shadow:
    0 12px 24px rgba(35, 74, 92, 0.1),
    inset 0 0 0 1px rgba(173, 220, 221, 0.58);
}

.brand-logo {
  width: 34px;
  height: 34px;
}

.brand-copy {
  min-width: 0;
}

.brand-title {
  display: block;
  color: #14384c;
  font-size: 24px;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.auth-close {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  color: #54717d;
  background: rgba(255, 255, 255, 0.62);
  box-shadow: inset 0 0 0 1px rgba(166, 205, 207, 0.42);
  transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;
}

.auth-close:hover {
  color: #14384c;
  background: rgba(255, 255, 255, 0.92);
  transform: translateY(-1px);
}

.auth-notice,
.auth-feedback {
  margin-bottom: 16px;
  border-radius: 18px;
}

.auth-body {
  padding: 18px;
  border-radius: 28px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.74), rgba(244, 250, 250, 0.82));
  box-shadow:
    inset 0 0 0 1px rgba(187, 222, 223, 0.44),
    0 18px 32px rgba(35, 74, 92, 0.08);
}

.auth-head {
  margin-bottom: 18px;
}

.auth-head-title {
  margin: 0;
  color: #14384c;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.auth-form :deep(.el-form-item) {
  margin-bottom: 16px;
}

.auth-form :deep(.el-input__wrapper) {
  min-height: 56px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.88);
  box-shadow:
    0 10px 18px rgba(48, 88, 104, 0.06),
    inset 0 0 0 1px rgba(173, 212, 214, 0.54);
}

.auth-form :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 12px 22px rgba(48, 88, 104, 0.1),
    inset 0 0 0 1px rgba(77, 180, 179, 0.72);
}

.auth-form :deep(.el-input__inner) {
  color: #17374b;
}

.auth-actions {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-top: 8px;
}

.primary-action {
  width: 100%;
  min-height: 52px;
  border: none;
  border-radius: 18px;
  font-size: 15px;
  font-weight: 600;
  background: linear-gradient(135deg, #6dc6c0, #f0ba7b);
  box-shadow: 0 16px 28px rgba(94, 156, 163, 0.18);
}

.primary-action:hover {
  background: linear-gradient(135deg, #64bfb8, #eeb06a);
}

.secondary-links {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.secondary-links.stacked {
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.text-link {
  border: none;
  padding: 0;
  color: #5c8091;
  font-size: 13px;
  background: transparent;
  cursor: pointer;
  transition: color 0.2s ease;
}

.text-link:hover {
  color: #1d4c62;
}

.text-link.strong {
  color: #2b5368;
  font-weight: 600;
}

.text-link.strong span {
  margin-left: 4px;
  color: #4bb4b3;
}

.code-trigger {
  border: none;
  padding: 0 0 0 14px;
  color: #4bb4b3;
  font-size: 13px;
  font-weight: 600;
  background: transparent;
  box-shadow: inset 1px 0 0 rgba(167, 211, 214, 0.72);
  cursor: pointer;
}

.code-trigger:disabled {
  color: #8aa2ae;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .auth-dialog :deep(.el-dialog) {
    width: min(100vw - 16px, 100%);
    margin: 8px auto;
    border-radius: 28px;
  }

  .auth-shell {
    padding: 22px 18px 20px;
  }

  .auth-brand {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .auth-close {
    grid-column: 2;
    justify-self: end;
  }

  .auth-body {
    padding: 16px;
    border-radius: 24px;
  }
}
</style>
