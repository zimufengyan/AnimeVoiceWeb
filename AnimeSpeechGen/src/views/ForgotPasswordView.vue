<template>
  <el-row class="forgot-page">
    <el-col :span="14" class="content-left"></el-col>
    <el-col :span="6" class="content-right">
      <div class="forgot-content">
        <div class="forgot-contentTop">
          <div class="header">
            <img src="@/assets/logo.svg" alt="Logo" class="logo" />
            <span class="title">AnimeVoice</span>
          </div>
        </div>
        <div class="forgot-content-form">
          <el-form
            ref="forgotFormRef"
            :model="forgotForm"
            style="width: 100%"
            @keyup.enter="toResetPassword"
            size="large"
            :inline-message="true"
            :rules="forgotRules"
          >
            <el-form-item label="" prop="email" class="forgot-sub-form-item">
              <el-input
                :prefix-icon="User"
                placeholder="邮箱账号"
                v-model="forgotForm.email"
                style="width: 100%; height: auto"
                inline-message
              ></el-input>
            </el-form-item>
            <el-form-item label="" prop="password" class="forgot-sub-form-item">
              <el-input
                :prefix-icon="Lock"
                placeholder="新密码"
                type="password"
                v-model="forgotForm.password"
                inline-message
              ></el-input>
            </el-form-item>
            <el-form-item label="" prop="repassword" class="forgot-sub-form-item">
              <el-input
                :prefix-icon="Lock"
                placeholder="确认新密码"
                type="password"
                v-model="forgotForm.repassword"
                inline-message
              ></el-input>
            </el-form-item>
            <el-form-item prop="validationCode">
              <el-input
                v-model="forgotForm.validationCode"
                class="form-input"
                placeholder="请输入验证码"
              >
                <template #suffix>
                  <span id="suffix-span">
                    <span style="margin-right: 10px">|</span>
                    <span
                      id="suffix-span-2"
                      @click="sendValidationCode(forgotForm.email)"
                      style="color: #1764ff"
                      ref="spanRef"
                    >
                      {{ sendCodeText }}
                    </span>
                  </span>
                </template>
              </el-input>
            </el-form-item>
          </el-form>
        </div>
        <div class="forgot-content-btn">
          <el-button type="primary" class="forgot-btn" @click="toResetPassword" title="reset-password">
            重置密码
          </el-button>
          <el-button
            type="primary"
            link
            @click="backToLogin"
            class="back-to-login"
            title="back-login"
          >
            返回登录
          </el-button>
        </div>
      </div>
    </el-col>
  </el-row>
</template>

<script lang="ts" setup>
import { User, Lock } from '@element-plus/icons-vue'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { ResetPasswordForm, ResetPasswordResponseData } from '@/util/types'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElNotification } from 'element-plus'
import { resetPasswordApi, sendResetPasswordCodeApi } from '@/api'
import bcrypt from 'bcryptjs'

const router = useRouter()
const forgotFormRef = ref<FormInstance>()
const spanRef = ref<HTMLElement | null>(null)
const sendCodeText = ref<string>('发送验证码')

const forgotForm = reactive<ResetPasswordForm>({
  email: '',
  password: '',
  repassword: '',
  validationCode: '',
  salt: '',
})

const forgotFormSend: ResetPasswordForm = {
  email: '',
  password: '',
  repassword: '',
  validationCode: '',
  salt: '',
}

const resetResponse = reactive<ResetPasswordResponseData>({
  code: '',
  message: '',
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
      validator: (rule, value, callback) => {
        if (value !== forgotForm.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  validationCode: [{ required: true, message: '请输入验证码', trigger: 'blur' }],
})

/**
 * 发送找回密码验证码，并复用注册页的倒计时体验。
 * @param email 当前输入框里的邮箱。
 */
async function sendValidationCode(email: string) {
  if (!sendCodeText.value.endsWith('发送验证码')) return
  if (!forgotFormRef.value || !spanRef.value) return

  await forgotFormRef.value.validateField('email')
  sendCodeText.value = '60秒后重新发送'
  spanRef.value.style.color = 'gray'
  const countDown = ref<number>(60)
  const timer = setInterval(() => {
    countDown.value--
    sendCodeText.value = `${countDown.value}秒后重新发送`
    if (!countDown.value) {
      clearInterval(timer)
      if (spanRef.value) {
        spanRef.value.style.color = '#1764FF'
      }
      sendCodeText.value = '重新发送验证码'
      countDown.value = 60
    }
  }, 1000)

  await sendResetPasswordCodeApi(email)
    .then((response) => {
      ElMessage({
        type: 'success',
        message: response.message || '验证码发送成功',
      })
    })
    .catch((error) => {
      ElMessage.error(error.message)
    })
}

/**
 * 提交重置密码表单，沿用现有前端加盐加密方式。
 */
const toResetPassword = async () => {
  if (!forgotFormRef.value) return

  forgotFormRef.value.validate(async (valid) => {
    if (!valid) return

    const encryptionSalt = bcrypt.genSaltSync(12)
    const hashedPassword = bcrypt.hashSync(forgotForm.password, encryptionSalt)
    forgotFormSend.email = forgotForm.email
    forgotFormSend.password = hashedPassword
    forgotFormSend.repassword = hashedPassword
    forgotFormSend.validationCode = forgotForm.validationCode
    forgotFormSend.salt = encryptionSalt

    await resetPasswordApi(forgotFormSend)
      .then((response) => {
        resetResponse.code = `${response.code}`
        resetResponse.message = response.message
        ElMessage({
          type: 'success',
          message: response.message,
        })
        router.replace({ path: '/login' })
      })
      .catch((error) => {
        ElNotification({
          message: error.message,
          type: 'error',
        })
      })
  })
}

const backToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.forgot-page {
  height: 100%;
  width: 100%;
  background-color: #fff;

  .content-right {
    display: flex;
    flex-direction: column;
    justify-content: center;
    user-select: none;

    .forgot-content {
      width: 80%;
      justify-content: center;
      margin-left: 10%;
      margin-right: 10%;
    }

    .logo {
      width: 30%;
      height: 30%;
      margin-right: 10px;
      margin-bottom: 0%;
    }

    .title {
      font-size: clamp(2.2rem, 1.8rem + 1.45vw, 3rem);
      font-weight: bold;
      margin: 0 0 0 10%;
    }

    .header {
      width: 90%;
      display: flex;
      justify-content: center;
      align-items: center;
      margin-left: 10px;
      margin-right: 10%;
      margin-bottom: 20px;
    }

    .forgot-btn {
      width: 100%;
      margin-top: 15px;
      height: 50px;
    }

    .back-to-login {
      margin-top: 15px;
      margin-left: 0%;
    }
  }

  .content-left {
    background: url('@/assets/slideImgs/slideImg5.png') center center / cover no-repeat;
  }
}

.forgot-content-form {
  display: flex;
  justify-content: center;
}

.forgot-sub-form-item {
  margin-bottom: 18px;
}

#suffix-span {
  user-select: none;
}

#suffix-span-2 {
  cursor: pointer;
}

@media (max-width: 1200px) {
  .forgot-page {
    .content-left {
      display: none;
    }

    .content-right {
      width: 100%;
      margin: 0 auto;

      .forgot-content {
        width: min(420px, 88vw);
        margin: 0 auto;
      }
    }
  }
}
</style>
