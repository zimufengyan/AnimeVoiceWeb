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

export type AudioRecord = {
  audio_id: number
  user_id: number
  audio_character: string
  audio_belong: string
  audio_path: string
  created_at?: string
  audio_text: string
  text_lang: string
  character_avator_path: string
  audio_filename: string
}

export type UserGender = '' | 'male' | 'female' | 'private'

export type UserProfile = {
  username: string
  avatar: string
  uid: string
  rate: string
  signature: string
  profileBanner: string
  birthday: string
  gender: UserGender
}

export type UpdateProfilePayload = {
  username?: string
  avatar?: string
  signature?: string
  profileBanner?: string
  birthday?: string
  gender?: UserGender
}

export type LoginResponseData = {
  meta: MetaForm
  username: string
  avatar: string
  uid: string
  rate: string
  token: string
}

export type GetSaltResponseData = {
  salt: string
  meta?: MetaForm
  code?: string | number
  message?: string
}

export type RegisterResponseData = {
  username: string
  avatar: string
  uid: string
  rate: string
  meta: MetaForm
}

export type GenerateVoiceResponseData = {
  code: string | number
  message: string
  audio_url: string
}

export type BelongStaticsResponseData = {
  code?: string | number
  names: string[]
  stands: string[]
  avators: string[]
}

export type AudioRecordsResponseData = {
  meta?: MetaForm
  records: AudioRecord[]
}

export type ProfileResponseData = {
  meta?: MetaForm
  profile: UserProfile
}

export type ProfileUploadResponseData = {
  meta?: MetaForm
  profile?: UserProfile
  assetUrl?: string
}
