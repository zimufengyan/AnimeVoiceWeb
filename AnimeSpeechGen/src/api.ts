import { request } from '@/util/request'
import type {
  AudioRecordsResponseData,
  BelongStaticsResponseData,
  GenerateVoiceResponseData,
  GetSaltResponseData,
  LoginForm,
  LoginResponseData,
  ProfileResponseData,
  ProfileUploadResponseData,
  RegisterForm,
  RegisterResponseData,
  UpdateProfilePayload,
  UserProfile,
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
  PROFILE: `${BASEURL}/profile`,
  PROFILE_AVATAR: `${BASEURL}/profile/avatar`,
  PROFILE_BANNER: `${BASEURL}/profile/banner`,
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
  uid: number | string
  rate: string
  token: string
}

type RegisterApiRaw = {
  meta: RegisterResponseData['meta']
  username: string
  avatar: string
  uid: number | string
  rate: string
}

type ExternalHitokotoRaw = {
  hitokoto: string
  from_who?: string | null
  from?: string | null
}

type ProfileApiRaw = {
  username?: string
  avatar?: string
  uid?: number | string
  rate?: string
  signature?: string
  profile_banner?: string
  birthday?: string
  gender?: UserProfile['gender']
}

type ProfileEnvelopeRaw = {
  meta?: ProfileResponseData['meta']
  profile: ProfileApiRaw
}

type ProfileUploadRaw = {
  meta?: ProfileUploadResponseData['meta']
  profile?: ProfileApiRaw
  asset_url?: string
}

/**
 * 将后端返回的 profile 原始结构映射为前端统一使用的资料对象。
 * @param profileApiRaw 后端 profile 字段原始值。
 * @returns 适用于前端的用户资料对象。
 */
const mapProfile = (profileApiRaw: ProfileApiRaw): UserProfile => {
  return {
    username: profileApiRaw.username || '',
    avatar: profileApiRaw.avatar || '',
    uid: profileApiRaw.uid === undefined || profileApiRaw.uid === null ? '' : `${profileApiRaw.uid}`,
    rate: profileApiRaw.rate || '',
    signature: profileApiRaw.signature || '',
    profileBanner: profileApiRaw.profile_banner || '',
    birthday: profileApiRaw.birthday || '',
    gender: profileApiRaw.gender || '',
  }
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
    uid: `${response.uid}`,
    rate: response.rate,
    token: response.token,
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
    uid: `${response.uid}`,
    rate: response.rate,
    meta: response.meta,
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

/**
 * 获取当前登录用户的个人资料。
 */
export const getProfileApi = async (): Promise<ProfileResponseData> => {
  const response = await request<unknown, ProfileEnvelopeRaw>({
    url: API.PROFILE,
    method: 'GET',
  })

  return {
    meta: response.meta,
    profile: mapProfile(response.profile || {}),
  }
}

/**
 * 更新当前登录用户的个人资料。
 * @param data 个人资料更新负载。
 */
export const updateProfileApi = async (data: UpdateProfilePayload): Promise<ProfileResponseData> => {
  const response = await request<unknown, ProfileEnvelopeRaw>({
    url: API.PROFILE,
    method: 'PUT',
    data: {
      username: data.username,
      avatar: data.avatar,
      signature: data.signature,
      profile_banner: data.profileBanner,
      birthday: data.birthday,
      gender: data.gender,
    },
  })

  return {
    meta: response.meta,
    profile: mapProfile(response.profile || {}),
  }
}

/**
 * 上传个人头像文件。
 * @param file 需要上传的头像文件。
 */
export const uploadProfileAvatarApi = async (file: File): Promise<ProfileUploadResponseData> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await request<unknown, ProfileUploadRaw>({
    url: API.PROFILE_AVATAR,
    method: 'POST',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return {
    meta: response.meta,
    profile: response.profile ? mapProfile(response.profile) : undefined,
    assetUrl: response.asset_url,
  }
}

/**
 * 上传个人横幅文件。
 * @param file 需要上传的横幅文件。
 */
export const uploadProfileBannerApi = async (file: File): Promise<ProfileUploadResponseData> => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await request<unknown, ProfileUploadRaw>({
    url: API.PROFILE_BANNER,
    method: 'POST',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return {
    meta: response.meta,
    profile: response.profile ? mapProfile(response.profile) : undefined,
    assetUrl: response.asset_url,
  }
}
