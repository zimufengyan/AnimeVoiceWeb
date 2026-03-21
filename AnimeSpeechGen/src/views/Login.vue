<template>
  <el-row class="login-page">
    <el-col :span="14" class="content-left"></el-col>
    <el-col :span="6" class="content-right">
      <div class="loginContent">
        <div class="verification"></div>
        <div class="loginContentTop">
          <div class="header">
            <img src="@/assets/logo.svg" alt="Logo" class="logo" />
            <span class="title">AnimeVoice</span>
          </div>
        </div>
        <div class="loginContentForm">
          <div class="loginMethods">
            <el-tabs v-model="activeName" class="login-tabs" @tab-click="handleClick">
              <el-tab-pane label="账号密码登录" class="tab-left" name="account">
                <!-- loginForm: 表单数据对象-->
                <el-form
                  ref="loginFormRef"
                  :model="loginForm"
                  style="width: 100%"
                  @keyup.enter="tologin"
                  size="large"
                  :rules="loginRules"
                  :inline-message="true"
                >
                  <el-form-item label="" prop="email">
                    <el-input
                      :prefix-icon="User"
                      placeholder="邮箱账号"
                      v-model="loginForm.email"
                      style="width: 100%; height: auto"
                      inline-message
                    ></el-input>
                  </el-form-item>
                  <el-form-item label="" prop="password">
                    <el-input
                      :prefix-icon="Lock"
                      placeholder="密码"
                      type="password"
                      v-model="loginForm.password"
                      inline-message
                    ></el-input>
                  </el-form-item>
                </el-form>
              </el-tab-pane>
              <el-tab-pane label="手机号码登录" class="tab-right" name="phone">
                <!-- loginForm: 表单数据对象-->
                <el-form
                  :model="loginFormPhone"
                  style="width: 208px"
                  size="large"
                  :inline-message="true"
                >
                  <el-form-item label="">
                    <el-input
                      :prefix-icon="Cellphone"
                      placeholder="请输入手机号"
                      style="width: 100%; height: auto"
                      v-model="loginFormPhone.phone"
                      inline-message
                    ></el-input>
                  </el-form-item>
                  <el-form-item label="" prop="code">
                    <el-input
                      :prefix-icon="Lock"
                      placeholder="请输入验证码"
                      v-model="loginFormPhone.code"
                      inline-message
                    ></el-input>
                  </el-form-item>
                </el-form>
              </el-tab-pane>
            </el-tabs>
          </div>
        </div>
        <div class="loginContentButton">
          <!-- <el-form-item label-position="right" label="自动登录" label-width="auto">
            <el-switch v-model="isAutoLogin" class="autoLogin" inline-prompt :active-icon="Check"
              :inactive-icon="Close" />
          </el-form-item> -->
          <a-alert v-if="showLoginError" :message="loginErrorTip" type="error" show-icon />
          <el-button type="primary" class="loginButton" @click="showVerification" title="login">
            登录
          </el-button>
          <div class="button-row">
            <el-button
              type="primary"
              link
              @click="gotoForgetPw"
              class="goto-btn"
              title="forget-password"
              >忘记密码</el-button
            >
            <el-button type="primary" link @click="goToRegister" class="goto-btn" title="register"
              >注册账号</el-button
            >
          </div>
        </div>
      </div>
      <DiyMask ref="maskRef" v-if="sliderVisible">
        <SlideVerify
          v-if="sliderVisible"
          @success="handleSlideSuccess"
          @close="handleSlideClose"
        ></SlideVerify>
      </DiyMask>
    </el-col>
  </el-row>
</template>

<script lang="ts" setup>
import { User, Lock, Cellphone } from '@element-plus/icons-vue'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { GetSaltResponseData, LoginForm, LoginFormPhone, LoginResponseData } from '@/util/types'
import type { FormInstance, TabsPaneContext, FormRules } from 'element-plus'
import { useUserStore } from '@/stores/counter'
import bcrypt from 'bcryptjs'
import { ElMessage } from 'element-plus'
import SlideVerify from '@/components/SlideVerify.vue'
import DiyMask from '@/components/DiyMask.vue'
import { getSaltApi } from '@/api'

const sliderVisible = ref(false) //滑动验证ui
const isVerified = ref(false)
const maskRef = ref<InstanceType<typeof DiyMask> | null>(null)
const loginErrorTip = ref('')
const showLoginError = ref(false)

const handleSlideSuccess = () => {
  sliderVisible.value = false
  isVerified.value = true
  tologin()
}

const handleSlideClose = () => {
  sliderVisible.value = false
  isVerified.value = false
}

// 显示滑动验证和遮罩层
const showVerification = () => {
  sliderVisible.value = true
}

const router = useRouter()

const userStore = useUserStore()

const activeName = ref('account')
const loginFormRef = ref<FormInstance>()
const loginForm = reactive<LoginForm>({
  email: '',
  password: '',
  salt: '',
}) // reactive 的变量不需要.value

const loginFormSend: LoginForm = {
  email: '',
  password: '',
  salt: '',
}
let loginResponse = reactive<LoginResponseData>({
  meta: {
    code: '',
    message: '',
    timestamp: '',
  },
  username: '',
  avatar: '',
  uid: '',
  rate: '',
  token: '',
})

const loginFormPhone = reactive<LoginFormPhone>({
  phone: '',
  code: '',
  salt: '',
})

const loginRules = reactive<FormRules<LoginForm>>({
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' },
  ],
  password: [
    {
      required: true,
      message: '密码为6~18位字母、数字和符号',
      min: 6,
      max: 18,
      trigger: 'blur',
    },
  ],
})

const handleClick = (tab: TabsPaneContext, event: Event) => {
  console.log(tab, event)
}

const gotoForgetPw = () => {
  // router.push('/login');
}
const goToRegister = () => {
  router.push('/register')
}
const tologin = async () => {
  if (!loginFormRef.value) return

  loginFormRef.value.validate(async (valid) => {
    // var valid_message = `验证结果: ${valid}`
    // console.log(valid_message)

    // 以valid作为判断条件，如果通过校验才执行登录
    if (valid) {
      if (!isVerified.value) {
        console.log('请先通过滑动验证！')
        return
      }

      // 前端密码加密
      // 获取后端该用户的盐值
      const saltResponse: GetSaltResponseData | void = await getSaltApi(loginForm.email).catch(() => {
        return
      })
      if (!saltResponse?.salt) {
        return
      }
      console.log(saltResponse.salt)
      const ENCRYPTION_SALT = saltResponse.salt
      const hashedPassword = bcrypt.hashSync(loginForm.password, ENCRYPTION_SALT)
      loginFormSend.email = loginForm.email
      loginFormSend.password = hashedPassword
      loginFormSend.salt = ENCRYPTION_SALT
      console.log(loginFormSend)

      await userStore
        .login(loginFormSend)
        .then((response) => {
          showLoginError.value = false
          //  1.提示用户
          ElMessage({ type: 'success', message: '登陆成功' })
          // 2.跳转首页
          router.replace({ path: '/' })
        })
        .catch((error) => {
          loginErrorTip.value = error.message
          showLoginError.value = true
        })
    }
  })
}
</script>

<style scoped>
.login-page {
  height: 100%;
  width: 100%;
  background-color: #fff;

  .content-right {
    display: flex;
    flex-direction: column;
    justify-content: center;
    user-select: none;

    .loginContent {
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

    .loginButton {
      width: 100%;
      margin-top: 15px;
      height: 50px;
      /* border-radius: 1rem; */
    }

    .autoLoginBlock {
      display: flex;
      align-items: center;
    }

    .autoLoginText {
      margin-left: 10px;
      text-align: center;
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

    .goto-btn {
      margin-top: 15px;
      width: 50%;
      margin-left: 0;
      margin-right: 0;
    }

    .go-register {
      margin-top: 15px;
      width: 50%;
    }

    .loginContentForm {
      margin-top: 5%;
    }

    .left-tab {
      text-align: left;
    }

    .right-tab {
      text-align: right;
    }
  }
}

.mask {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  z-index: 999999;
  background: rgba(0, 0, 0, 0.5);
}

.verification {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: white;
}

::v-deep(.el-button--link) {
  padding: 0;
}

::v-deep(.el-form) {
  width: 100%;
}

::v-deep(.el-form-item__content) {
  width: 100%;
  position: relative;
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
