import GenShinLogo from '@/assets/genshin_logo.jpg'
import StarRailLogo from '@/assets/starrail_logo.jpg'

export type VoiceIpConfig = {
  belong: string
  routeName: string
  routePath: string
  displayName: string
  icon: string
}

/**
 * 维护各个语音 IP 页面所需的统一配置。
 * 新增 IP 时，只需要补一条配置并让后端提供对应资源即可。
 */
export const voiceIpConfigs: VoiceIpConfig[] = [
  {
    belong: 'GenShin',
    routeName: 'genshin',
    routePath: '/genshin',
    displayName: '原神',
    icon: GenShinLogo,
  },
  {
    belong: 'StarRail',
    routeName: 'starrail',
    routePath: '/starrail',
    displayName: '崩坏·星穹铁道',
    icon: StarRailLogo,
  },
]

/**
 * 根据路由名查找对应的 IP 配置。
 * @param routeName 路由名称，例如 genshin / starrail。
 * @returns 找到的配置项；不存在时返回 undefined。
 */
export const getVoiceIpConfigByRouteName = (routeName: string) => {
  return voiceIpConfigs.find((config) => config.routeName === routeName)
}
