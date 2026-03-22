import { reactive } from 'vue'

export type AuthDialogMode = 'login' | 'register' | 'forgot-password'

type AuthDialogOptions = {
  redirectTo?: string
  email?: string
  reason?: string
}

type AuthDialogState = {
  visible: boolean
  mode: AuthDialogMode
  redirectTo: string
  email: string
  reason: string
}

export const authDialogState = reactive<AuthDialogState>({
  visible: false,
  mode: 'login',
  redirectTo: '',
  email: '',
  reason: '',
})

/**
 * 打开全局认证弹窗，并可附带回跳路径与预填邮箱。
 * @param mode 弹窗当前模式。
 * @param options 可选的回跳路径、邮箱与提示原因。
 */
export const openAuthDialog = (mode: AuthDialogMode, options: AuthDialogOptions = {}) => {
  authDialogState.mode = mode
  authDialogState.visible = true
  authDialogState.redirectTo = options.redirectTo ?? authDialogState.redirectTo
  authDialogState.email = options.email ?? ''
  authDialogState.reason = options.reason ?? ''
}

/**
 * 在不关闭弹窗的前提下切换认证模式。
 * @param mode 目标模式。
 * @param options 可选的回跳路径、邮箱与提示原因。
 */
export const switchAuthDialogMode = (mode: AuthDialogMode, options: AuthDialogOptions = {}) => {
  openAuthDialog(mode, options)
}

/**
 * 关闭全局认证弹窗，并清理临时上下文。
 */
export const closeAuthDialog = () => {
  authDialogState.visible = false
  authDialogState.redirectTo = ''
  authDialogState.reason = ''
  authDialogState.email = ''
}
