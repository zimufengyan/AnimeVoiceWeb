export type LoginForm = {
  email: string;
  password: string;
  salt: string;
}

export type LoginFormPhone = {
  phone: string;
  code: string;
  salt: string;
}

export type RegisterForm = {
  email: string;
  username: string;
  password: string;
  repassword: string;
  validationCode: string;
  salt: string;
}

export type LoginResponseData = {
  code: string;
  username: string;
  avatar: string;
  index: string;
  rate: string;
  token: string;
  message: string
}

export type RegisterResponseData = {
  code: string;
  username: string;
  avatar: string;
  index: string;
  rate: string;
  message: string
}
