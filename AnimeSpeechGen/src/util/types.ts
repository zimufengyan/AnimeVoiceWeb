export type LoginForm = {
  email: string
  password: string
  salt: string
}

export type LoginFormPhone = {
  phone: string
  code: string
  salt: string
}

export type RegisterForm = {
  email: string
  username: string
  password: string
  repassword: string
  validationCode: string
  salt: string
}

export type MetaForm = {
  code: string
  message: string
  timestamp: string
}

export type LoginResponseData = {
  meta: MetaForm
  username: string
  avatar: string
  index: string
  rate: string
  token: string
  id: string
}

export type RegisterResponseData = {
  username: string
  avatar: string
  index: string
  rate: string
  meta: MetaForm
  id: string
}
