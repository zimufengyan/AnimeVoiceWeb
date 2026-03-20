import { request } from '@/util/request'
import type { LoginForm, RegisterForm, LoginFormPhone, LoginResponseData } from './util/types'

const API_PORT = import.meta.env.VITE_API_PORT || '25683'
const BASEURL =
  (import.meta.env.VITE_API_ORIGIN as string | undefined)?.replace(/\/$/, '') ||
  `${window.location.protocol}//${window.location.hostname}:${API_PORT}`

enum API {
  LOGIN = `${BASEURL}/login`,
  LOGOUT = `${BASEURL}/logout`,
  REGISTER = `${BASEURL}/register`,
  EMAILCODE = `${BASEURL}/get_email_code`,
  BCRYPTSALT = `${BASEURL}/get_salt`,
  CHARSTATICURL = `${BASEURL}/get_belong_statics`,
  GENERATE_VOICE = `${BASEURL}/generate_voice`,
  GET_AUDIO_RECORDS = `${BASEURL}/get_recent_audio_records`,
  DELETE_AURIO_RECORD = `${BASEURL}/delete_audio_record`,
  DELETE_AURIO_RECORDS = `${BASEURL}/delete_audio_records`,
  HITOKITO_API = 'https://v1.hitokoto.cn',
}

//登录接口
export const loginApi = async (data: LoginForm) => {
  // request.post<any,LoginResponseData>(API.LOGIN,data)
  return await request({
    url: API.LOGIN,
    method: 'POST',
    data: data,
  })
    .then((response) => {
      console.log('请求成功:', response)
      return {
        meta: response.meta,
        username: response.username,
        avatar: response.avatar,
        index: response.index,
        rate: response.rate,
        token: response.token,
        id: response.user_id,
      }
    })
    .catch((error) => {
      console.error('请求失败:', error.response?.status, error.message)
      throw error
    })
}

export const logoutApi = () => {
  return request.get(API.LOGOUT)
}

export const getSaltApi = async (email: string) => {
  return await request({
    url: API.BCRYPTSALT,
    method: 'GET',
    params: {
      email: email,
    },
  })
    .then((response) => {
      console.log('请求成功:', response)
      return {
        salt: response.salt,
        meta: response.meta,
      }
    })
    .catch((error) => {
      console.error('请求失败:', error.response?.status, error.message)
      throw error
    })
}

export const sendEmailCodeApi = async (email: string) => {
  return await request({
    url: API.EMAILCODE,
    method: 'GET',
    params: {
      email: email,
    },
  })
}

export const registerApi = async (data: RegisterForm) => {
  return await request({
    url: API.REGISTER,
    method: 'POST',
    data: data,
  })
    .then((response) => {
      console.log('请求成功:', response)
      return {
        username: response.username,
        avatar: response.avatar,
        index: response.index,
        rate: response.rate,
        meta: response.meta,
        id: response.user_id,
      }
    })
    .catch((error) => {
      console.error('请求失败:', error.response?.status, error.message)
      throw error
    })
}

export const getStaticsUrlApi = async (belong: string) => {
  return await request({
    url: API.CHARSTATICURL,
    method: 'GET',
    params: {
      belong: belong,
    },
  })
}

export const getGeneratedVoiceApi = async (
  text: string,
  character: string,
  belong: string,
  lang: string = 'zh',
) => {
  const response = await request({
    url: API.GENERATE_VOICE,
    method: 'POST',
    timeout: 60000,
    data: {
      text: text,
      character: character,
      belong: belong,
      lang: lang,
    },
  })
  if (`${response.code}` !== '1' || !response.audio_url) {
    throw new Error(response.message || '语音生成失败')
  }
  return response
}

export const getAudioRecordsApi = async () => {
  return await request({
    url: API.GET_AUDIO_RECORDS,
    method: 'GET',
  })
}

export const getHiToKiToApi = async (category: string) => {
  return await request({
    url: API.HITOKITO_API,
    method: 'GET',
    params: {
      c: category,
    },
  })
    .then((response) => {
      console.log('请求成功:', response)
      return {
        href: response.href,
        text: response.innerText,
      }
    })
    .catch((error) => {
      console.error('请求失败:', error.response?.status, error.message)
      throw error
    })
}

export const deleteAudioRecordApi = async (audio_id: number) => {
  return await request({
    url: API.DELETE_AURIO_RECORD,
    method: 'GET',
    params: {
      audio_id: audio_id,
    },
  })
}

export const deleteAudioRecordsApi = async (audio_ids: number[]) => {
  const params = new URLSearchParams()
  audio_ids.forEach((audioId) => {
    params.append('audio_ids', `${audioId}`)
  })

  return await request({
    url: `${API.DELETE_AURIO_RECORDS}?${params.toString()}`,
    method: 'GET',
  })
}
