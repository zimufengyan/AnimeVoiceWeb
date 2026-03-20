import { request } from '@/util/request'
import type {
  AudioRecordsResponseData,
  BelongStaticsResponseData,
  GenerateVoiceResponseData,
  GetSaltResponseData,
  LoginForm,
  LoginResponseData,
  RegisterForm,
  RegisterResponseData,
} from './util/types'

const API_PORT = import.meta.env.VITE_API_PORT || '25683'
const BASEURL =
  (import.meta.env.VITE_API_ORIGIN as string | undefined)?.replace(/\/$/, '') ||
  `${window.location.protocol}//${window.location.hostname}:${API_PORT}`

const API = {
  LOGIN: `${BASEURL}/login`,
  LOGOUT: `${BASEURL}/logout`,
  REGISTER: `${BASEURL}/register`,
  EMAILCODE: `${BASEURL}/get_email_code`,
  BCRYPTSALT: `${BASEURL}/get_salt`,
  CHARSTATICURL: `${BASEURL}/get_belong_statics`,
  GENERATE_VOICE: `${BASEURL}/generate_voice`,
  GET_AUDIO_RECORDS: `${BASEURL}/get_recent_audio_records`,
  DELETE_AURIO_RECORD: `${BASEURL}/delete_audio_record`,
  DELETE_AURIO_RECORDS: `${BASEURL}/delete_audio_records`,
  HITOKITO_API: 'https://v1.hitokoto.cn',
} as const

type HitokotoResponse = {
  href: string
  text: string
}

type LoginApiRaw = {
  meta: LoginResponseData['meta']
  username: string
  avatar: string
  index: string
  rate: string
  token: string
  user_id: string
}

type RegisterApiRaw = {
  meta: RegisterResponseData['meta']
  username: string
  avatar: string
  index: string
  rate: string
  user_id: string
}

type ExternalHitokotoRaw = {
  hitokoto: string
  from_who?: string | null
  from?: string | null
}

export const loginApi = async (data: LoginForm): Promise<LoginResponseData> => {
  const response = await request<unknown, LoginApiRaw>({
    url: API.LOGIN,
    method: 'POST',
    data,
  })

  return {
    meta: response.meta,
    username: response.username,
    avatar: response.avatar,
    index: response.index,
    rate: response.rate,
    token: response.token,
    id: response.user_id,
  }
}

export const logoutApi = async (): Promise<void> => {
  await request({
    url: API.LOGOUT,
    method: 'GET',
  })
}

export const getSaltApi = async (email: string): Promise<GetSaltResponseData> => {
  const response = await request<unknown, GetSaltResponseData>({
    url: API.BCRYPTSALT,
    method: 'GET',
    params: { email },
  })

  return response
}

export const sendEmailCodeApi = async (email: string): Promise<{ meta?: { message: string }; message?: string }> => {
  return await request({
    url: API.EMAILCODE,
    method: 'GET',
    params: { email },
  })
}

export const registerApi = async (data: RegisterForm): Promise<RegisterResponseData> => {
  const response = await request<unknown, RegisterApiRaw>({
    url: API.REGISTER,
    method: 'POST',
    data,
  })

  return {
    username: response.username,
    avatar: response.avatar,
    index: response.index,
    rate: response.rate,
    meta: response.meta,
    id: response.user_id,
  }
}

export const getStaticsUrlApi = async (belong: string): Promise<BelongStaticsResponseData> => {
  return await request<unknown, BelongStaticsResponseData>({
    url: API.CHARSTATICURL,
    method: 'GET',
    params: { belong },
  })
}

export const getGeneratedVoiceApi = async (
  text: string,
  character: string,
  belong: string,
  lang: string = 'zh',
): Promise<GenerateVoiceResponseData> => {
  const response = await request<unknown, GenerateVoiceResponseData>({
    url: API.GENERATE_VOICE,
    method: 'POST',
    timeout: 60000,
    data: {
      text,
      character,
      belong,
      lang,
    },
  })

  if (`${response.code}` !== '1' || !response.audio_url) {
    throw new Error(response.message || '语音生成失败')
  }
  return response
}

export const getAudioRecordsApi = async (): Promise<AudioRecordsResponseData> => {
  return await request<unknown, AudioRecordsResponseData>({
    url: API.GET_AUDIO_RECORDS,
    method: 'GET',
  })
}

export const getHiToKiToApi = async (category: string): Promise<HitokotoResponse> => {
  const response = await request<unknown, ExternalHitokotoRaw>({
    url: API.HITOKITO_API,
    method: 'GET',
    params: {
      c: category,
    },
  })

  return {
    href: response.from ? `https://hitokoto.cn/?from=${encodeURIComponent(response.from)}` : 'https://hitokoto.cn/',
    text: response.hitokoto,
  }
}

export const deleteAudioRecordApi = async (audio_id: number): Promise<AudioRecordsResponseData> => {
  return await request<unknown, AudioRecordsResponseData>({
    url: API.DELETE_AURIO_RECORD,
    method: 'GET',
    params: {
      audio_id,
    },
  })
}

export const deleteAudioRecordsApi = async (audio_ids: number[]): Promise<AudioRecordsResponseData> => {
  const params = new URLSearchParams()
  audio_ids.forEach((audioId) => {
    params.append('audio_ids', `${audioId}`)
  })

  return await request<unknown, AudioRecordsResponseData>({
    url: `${API.DELETE_AURIO_RECORDS}?${params.toString()}`,
    method: 'GET',
  })
}
