<template>
  <el-row class="register-page">
    <el-col :span="14" class="content-left"></el-col>
    <el-col :span="6" class="content-right">
      <div class="register-content">
        <div class="register-contentTop">
          <div class="header">
            <img src="@/assets/logo.svg" alt="Logo" class="logo" />
            <span class="title">AnimeVoice</span>
          </div>
        </div>
        <div class="register-content-form">
          <el-form
            ref="registerFormRef"
            :model="registerForm"
            style="width: 100%"
            @keyup.enter="toRegister"
            size="large"
            :inline-message="true"
            :rules="registerRules"
          >
            <el-form-item label="" prop="email" class="register-sub-form-item">
              <el-input
                :prefix-icon="User"
                placeholder="邮箱账号"
                v-model="registerForm.email"
                style="width: 100%; height: auto"
                inline-message
              ></el-input>
            </el-form-item>
            <el-form-item label="" prop="username" class="register-sub-form-item">
              <el-input
                :prefix-icon="User"
                placeholder="用户名"
                v-model="registerForm.username"
                style="width: 100%; height: auto"
                inline-message
              ></el-input>
            </el-form-item>
            <el-form-item label="" prop="password" class="register-sub-form-item">
              <el-input
                :prefix-icon="Lock"
                placeholder="密码"
                type="password"
                v-model="registerForm.password"
                inline-message
              ></el-input>
            </el-form-item>
            <el-form-item label="" prop="repassword" class="register-sub-form-item">
              <el-input
                :prefix-icon="Lock"
                placeholder="确认密码"
                type="password"
                v-model="registerForm.repassword"
                inline-message
              ></el-input>
            </el-form-item>
            <el-form-item prop="validationCode">
              <el-input
                v-model="registerForm.validationCode"
                class="form-input"
                placeholder="请输入验证码"
              >
                <template #suffix>
                  <span id="suffix-span">
                    <span style="margin-right: 10px">|</span>
                    <span
                      id="suffix-span-2"
                      @click="sendValidationCode(registerForm.email)"
                      style="color: #1764ff"
                      ref="spanRef"
                    >
                      {{ isSendValidationCode }}
                    </span>
                  </span>
                </template>
              </el-input>
            </el-form-item>
          </el-form>
        </div>
        <div class="register-content-btn">
          <el-button type="primary" class="register-btn" @click="toRegister" title="register">
            注册
          </el-button>
          <!-- <el-link
              type="primary"
              :underline="false"
              class="back-to-login"
              :href="/login"
            >
              <span>已有账号</span>
            </el-link> -->
          <el-button
            type="primary"
            link
            @click="backToLogin"
            class="back-to-login"
            title="has-account"
            >已有账号</el-button
          >
        </div>
      </div>
    </el-col>
  </el-row>
</template>

<script lang="ts" setup>
import { User, Lock } from '@element-plus/icons-vue'
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import type { RegisterForm, RegisterResponseData } from '@/util/types'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElNotification } from 'element-plus'
import { registerApi, sendEmailCodeApi } from '@/api'
import bcrypt from 'bcryptjs'

const router = useRouter()
const registerFormRef = ref<FormInstance>()
const registerForm = reactive<RegisterForm>({
  email: '',
  username: '',
  password: '',
  repassword: '',
  validationCode: '',
  salt: '',
})
const registerFormSend: RegisterForm = {
  email: '',
  username: '',
  password: '',
  repassword: '',
  validationCode: '',
  salt: '',
}

// 验证码区域文字说明
const spanRef = ref<HTMLElement | null>(null)
const isSendValidationCode = ref<string>('发送验证码')

let registerResponse = reactive<RegisterResponseData>({
  meta: {
    code: '',
    message: '',
    timestamp: '',
  },
  username: '',
  avatar: '',
  uid: '',
  rate: '',
})

// 表单验证规则
const registerRules = reactive<FormRules<RegisterForm>>({
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符之间', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 20, message: '密码长度应为 8 到 20 个字符', trigger: 'blur' },
    {
      pattern: /^(?!.*[^a-zA-Z0-9]).*$/, // 不包含特殊字符
      message: '密码不能包含特殊字符',
      trigger: 'blur',
    },
    {
      pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/, // 至少包含一个小写字母、一个大写字母和一个数字
      message: '密码必须包含大写字母、小写字母和数字',
      trigger: 'blur',
    },
  ],
  repassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== registerForm.password) {
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

async function sendValidationCode(email: string) {
  // 若显示的发送验证码区域文字 不是 '发送验证码'，就直接返回不再执行
  if (!isSendValidationCode.value.endsWith('发送验证码')) return
  if (!registerFormRef.value || !spanRef.value) return

  await registerFormRef.value.validateField('email') // 表单验证
  // 重新发送逻辑
  isSendValidationCode.value = '60秒后重新发送'
  spanRef.value.style.color = 'gray' // 颜色变灰
  const countDown = ref<number>(60) // 倒计时
  const temp = setInterval(() => {
    countDown.value--
    isSendValidationCode.value = countDown.value + '秒后重新发送'
    if (!countDown.value) {
      clearInterval(temp)
      if (spanRef.value) {
        spanRef.value.style.color = '#1764FF' // 颜色变蓝
      }
      isSendValidationCode.value = '重新发送验证码'
      countDown.value = 60
    }
  }, 1000)
  // 发送
  await sendEmailCodeApi(email)
    .then((response) => {
      ElMessage({
        type: 'success',
        message: response.meta?.message || response.message || '验证码发送成功',
      })
    })
    .catch((error) => {
      ElMessage.error(error.message)
    })
}

const toRegister = async () => {
  if (!registerFormRef.value) return

  registerFormRef.value.validate(async (valid) => {
    // valid:所有表单都通过校验  才为true
    // var valid_message = `验证结果: ${valid}`
    // console.log(valid_message)
    // 以valid作为判断条件，如果通过校验才执行登录
    if (valid) {
      // 前端密码加密
      const ENCRYPTION_SALT = bcrypt.genSaltSync(12)
      const hashedPassword = bcrypt.hashSync(registerForm.password, ENCRYPTION_SALT)
      registerFormSend.email = registerForm.email
      registerFormSend.username = registerForm.username
      registerFormSend.password = hashedPassword
      registerFormSend.repassword = hashedPassword
      registerFormSend.validationCode = registerForm.validationCode
      registerFormSend.salt = ENCRYPTION_SALT
      console.log(registerFormSend)

      await registerApi(registerFormSend)
        .then((response) => {
          ElMessage({
            type: 'success',
            message: response.meta.message,
          })
          // 跳转登录页
          router.replace({ path: '/login' })
        })
        .catch((error) => {
          ElNotification({
            message: error.message,
            type: 'error',
          })
        })
    }
  })
}

const backToLogin = () => {
  router.push('/login')
}
</script>

<style scoped>
.register-page {
  height: 100%;
  width: 100%;
  background-color: #fff;

  .content-right {
    display: flex;
    flex-direction: column;
    justify-content: center;
    user-select: none;

    .register-content {
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

    .button {
      width: 100%;
    }
    .register-btn {
      width: 100%;
      margin-top: 15px;
      height: 50px;
      /* border-radius: 1rem; */
    }

    .flex {
      width: 100%;
      display: flex;
      justify-content: space-between;
    }

    .button_row {
      display: flex;
      width: 100%;
      align-items: center;
    }

    .back-to-login {
      margin-top: 15px;
      margin-left: 0%;
    }
    .register {
      margin-top: 15px;
      width: 50%;
    }

    .register-content-form {
      margin-top: 5%;
    }
  }
}

::v-deep(.el-button--link) {
  padding: 0;
}

::v-deep(.el-form) {
  width: 100%;
}

::v-deep(.el-form-item__content) {
  width: 100%;
}

::v-deep(.el-tabs__nav) {
  width: 100%;
}

::v-deep(.el-input__wrapper) {
  display: flex;
  width: 100%;
}

::v-deep(.el-tabs__item) {
  display: flex;
  width: 100%;
}

::v-deep(.el-tabs__item) {
  font-size: clamp(1rem, 0.6rem + 1.5vw, 1.1rem);
}

.header-up {
  display: flex;
}
</style>
