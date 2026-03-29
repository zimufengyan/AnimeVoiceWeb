import genshinLogo from '@/assets/ip-themes/genshin/home/logos/genshin-logo.jpg'
import genshinFeatureMain from '@/assets/ip-themes/genshin/home/feature-cards/genshin-home-feature-main.png'
import starrailLogo from '@/assets/ip-themes/starrail/home/logos/starrail-logo-2.png'
import starrailFeaturePlaceholder from '@/assets/ip-themes/starrail/home/feature-cards/starrail-feature-card.png'

export type HomeAssetKey = 'genshin' | 'starrail'

export type IpHomeAsset = {
  logo: string
  featureCardCover: string
}

export const ipHomeAssets: Record<HomeAssetKey, IpHomeAsset> = {
  genshin: {
    logo: genshinLogo,
    featureCardCover: genshinFeatureMain,
  },
  starrail: {
    logo: starrailLogo,
    featureCardCover: starrailFeaturePlaceholder,
  },
}
