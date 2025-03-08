import { request } from '@/util/request'
import type { LoginForm, RegisterForm, LoginFormPhone, LoginResponseData } from './util/types'

enum API {
  LOGIN = 'http://10.60.102.53:25683/login',
  LOGOUT = 'http://10.60.102.53:25683/logout',
  REGISTER = 'http://10.60.102.53:25683/register',
  EMAILCODE = 'http://10.60.102.53:25683/get_email_code',
  BCRYPTSALT = "http://10.60.102.53:25683/get_salt",
  CHARSTATICURL = "http://10.60.102.53:25683/get_belong_statics",
  GENERATE_VOICE = "http://10.60.102.53:25683/generate_voice",
}

//登录接口
export const loginApi = async (data:LoginForm)=>{
  // request.post<any,LoginResponseData>(API.LOGIN,data)
  const response = await request({
    url: API.LOGIN,
    method: "POST",
    data: data
  });
  return {
    code: response.code,
    username: response.username,
    avatar: response.avatar,
    index: response.index,
    rate: response.rate,
    token: response.token,
    message: response.message,

  };
}

export const logoutApi = () => {
  return request.post(API.LOGOUT);
};

export const getSaltApi = async (email: string) => {
  const response =  await request({
    url: API.BCRYPTSALT,
    method: "GET",
    params: {
      email: email
    }
  })
  return {
    code: response.code,
    salt: response.salt,
    message: response.message,
  }
}

export const registerApi = async (data: RegisterForm) => {
  const response = await request({
    url: API.REGISTER,
    method: "POST",
    data: data
  });
  return {
    code: response.code,
    username: response.username,
    avatar: response.avatar,
    index: response.index,
    rate: response.rate,
    message: response.message,
  }
}


export const sendEmailCodeApi = async (email_address: string) => {
 return await request({
  url: API.EMAILCODE,
  method: "GET",
  params: {
    "email": email_address
  }
 })
}


export const getStaticsUrlApi = async (belong: string) => {
  return await request({
    url: API.CHARSTATICURL,
    method: "GET",
    params: {
      belong: belong
    }
  })
}

export const getGeneratedVoiceApi = async (text: string, character: string, belong: string, lang: string="zh") => {
  return await request({
    url: API.GENERATE_VOICE,
    method: "GET",
    params: {
      text: text,
      character: character,
      belong: belong,
      lang: lang,
    }
  })
}
