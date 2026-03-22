export type VoiceWorkshopTheme = {
  key: string
  belong: string
  displayName: string
  searchPlaceholder: string
  textPlaceholder: string
  emptyDescription: string
  primary: string
  primarySoft: string
  secondary: string
  backgroundGradient: string
  ambientGradient: string
  panelGradient: string
  accentGradient: string
}

export const voiceWorkshopThemes: Record<string, VoiceWorkshopTheme> = {
  GenShin: {
    key: 'genshin',
    belong: 'GenShin',
    displayName: '原神',
    searchPlaceholder: '搜索原神角色',
    textPlaceholder: '输入想让角色说的话，适合中文台词、问候语和短句。',
    emptyDescription: '当前 IP 还没有可用角色资源',
    primary: '#67bbb3',
    primarySoft: '#c9f1ec',
    secondary: '#f6cc96',
    backgroundGradient:
      'linear-gradient(180deg, #eff8fb 0%, #edf6fa 40%, #f8fbff 100%)',
    ambientGradient:
      'radial-gradient(circle at 18% 16%, rgba(117, 205, 196, 0.28), transparent 30%), radial-gradient(circle at 82% 14%, rgba(249, 209, 149, 0.22), transparent 24%), linear-gradient(180deg, rgba(255,255,255,0.64), rgba(255,255,255,0))',
    panelGradient:
      'linear-gradient(160deg, rgba(255,255,255,0.9), rgba(244,250,255,0.82))',
    accentGradient:
      'linear-gradient(135deg, rgba(103,187,179,0.24), rgba(246,204,150,0.18))',
  },
  StarRail: {
    key: 'starrail',
    belong: 'StarRail',
    displayName: '崩坏·星穹铁道',
    searchPlaceholder: '搜索星穹铁道角色',
    textPlaceholder: '输入想让角色说的话，适合科幻广播、任务对白与角色开场。',
    emptyDescription: '当前星穹铁道主题仍在准备资源',
    primary: '#6f8dff',
    primarySoft: '#dfe7ff',
    secondary: '#64d7ff',
    backgroundGradient:
      'linear-gradient(180deg, #111827 0%, #0d1626 42%, #0b1220 100%)',
    ambientGradient:
      'radial-gradient(circle at 16% 18%, rgba(103,132,255,0.18), transparent 28%), radial-gradient(circle at 84% 12%, rgba(95,228,255,0.16), transparent 24%), linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0))',
    panelGradient:
      'linear-gradient(160deg, rgba(12,20,34,0.9), rgba(17,28,48,0.84))',
    accentGradient:
      'linear-gradient(135deg, rgba(111,141,255,0.22), rgba(100,215,255,0.16))',
  },
}

export const getVoiceWorkshopTheme = (belong: string): VoiceWorkshopTheme => {
  return voiceWorkshopThemes[belong] || voiceWorkshopThemes.GenShin
}
