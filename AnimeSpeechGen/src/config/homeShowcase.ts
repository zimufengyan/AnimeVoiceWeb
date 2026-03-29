import genshinHeroMain from '@/assets/ip-themes/genshin/home/carousel/genshin-hero-main.webp'
import genshinWeeklyNew from '@/assets/ip-themes/genshin/home/carousel/genshin-weekly-new.webp'
import genshinPopularVoices from '@/assets/ip-themes/genshin/home/carousel/genshin-popular-voices.webp'
import { ipHomeAssets } from '@/config/ipHomeAssets'

export type HomeShowcaseCharacter = {
  key: string
  filename: string
  displayName: string
  subtitle: string
  highlight: string
  keywords: string[]
}

export type HomeHeroSlide = {
  key: string
  badge: string
  title: string
  description: string
  ctaText: string
  route: string
  backgroundImage: string
  characterKeys: string[]
  indicatorLabel: string
}

export type HomeFeatureCard = {
  key: string
  title: string
  subtitle: string
  description: string
  accent: string
  state: 'active' | 'upcoming'
  route?: string
  coverImage: string
  logo: string
  tags: string[]
  featuredCharacterKeys: string[]
  primaryAction: string
  secondaryAction: string
}

export const genshinShowcaseCharacters: HomeShowcaseCharacter[] = [
  {
    key: 'ayaka',
    filename: 'Kamizato Ayaka.png',
    displayName: '神里绫华',
    subtitle: 'Ayaka',
    highlight: '清冷优雅，适合抒情与叙事',
    keywords: ['ayaka', 'kamisato ayaka', 'kamizato ayaka', '神里绫华'],
  },
  {
    key: 'furina',
    filename: 'Furina.png',
    displayName: '芙宁娜',
    subtitle: 'Furina',
    highlight: '情绪张力强，适合高光台词',
    keywords: ['furina', '芙宁娜'],
  },
  {
    key: 'yae-miko',
    filename: 'YaeMiko.png',
    displayName: '八重神子',
    subtitle: 'Yae Miko',
    highlight: '慵懒灵动，适合剧情对白',
    keywords: ['yae miko', 'yaemiko', '八重神子'],
  },
  {
    key: 'nahida',
    filename: 'Nahida.png',
    displayName: '纳西妲',
    subtitle: 'Nahida',
    highlight: '温柔治愈，适合陪伴系文案',
    keywords: ['nahida', '纳西妲'],
  },
  {
    key: 'ganyu',
    filename: 'Ganyu.png',
    displayName: '甘雨',
    subtitle: 'Ganyu',
    highlight: '克制柔和，适合日常陪伴',
    keywords: ['ganyu', '甘雨'],
  },
  {
    key: 'shenhe',
    filename: 'Shenhe.png',
    displayName: '申鹤',
    subtitle: 'Shenhe',
    highlight: '冷冽疏离，适合战斗风格',
    keywords: ['shenhe', '申鹤'],
  },
]

export const homeHeroSlides: HomeHeroSlide[] = [
  {
    key: 'genshin-main',
    badge: '精选推荐',
    title: '热门 IP',
    description: '搜索角色，切换立绘，快速生成台词演绎。',
    ctaText: '进入原神工坊',
    route: '/genshin',
    backgroundImage: genshinHeroMain,
    characterKeys: ['ayaka', 'furina', 'yae-miko'],
    indicatorLabel: '工坊入口',
  },
  {
    key: 'weekly-new',
    badge: '本周更新',
    title: '新角色已加入',
    description: '新角色、新推荐、新内容集中展示。',
    ctaText: '查看更新',
    route: '/genshin',
    backgroundImage: genshinWeeklyNew,
    characterKeys: ['furina', 'shenhe', 'ganyu'],
    indicatorLabel: '本周更新',
  },
  {
    key: 'popular-voices',
    badge: '热门角色',
    title: '从高人气角色开始',
    description: '高人气角色与常用风格直接前置。',
    ctaText: '挑选角色',
    route: '/genshin',
    backgroundImage: genshinPopularVoices,
    characterKeys: ['nahida', 'yae-miko', 'ayaka'],
    indicatorLabel: '热门角色',
  },
]

export const homeFeatureCards: HomeFeatureCard[] = [
  {
    key: 'genshin',
    title: '原神语音工坊',
    subtitle: '提瓦特主题舞台',
    description: '角色立绘、主题舞台与语音生成联动，进入即开玩。',
    accent: '#7db7b3',
    state: 'active',
    route: '/genshin',
    coverImage: ipHomeAssets.genshin.featureCardCover,
    logo: ipHomeAssets.genshin.logo,
    tags: ['角色切换', '主题舞台', '热门推荐'],
    featuredCharacterKeys: ['ayaka', 'furina', 'yae-miko', 'nahida'],
    primaryAction: '立即体验',
    secondaryAction: '查看角色推荐',
  },
  {
    key: 'starrail',
    title: '星穹铁道主题页',
    subtitle: '下一站：星海终端',
    description: '主题内容筹备中，敬请期待后续上线。',
    accent: '#5f75d5',
    state: 'upcoming',
    route: '/starrail',
    coverImage: ipHomeAssets.starrail.featureCardCover,
    logo: ipHomeAssets.starrail.logo,
    tags: ['筹备中', '独立主题', '敬请期待'],
    featuredCharacterKeys: [],
    primaryAction: '敬请期待',
    secondaryAction: '浏览原神工坊',
  },
]

export const homeHeroMetrics = [
  { label: '当前开放', value: '原神', note: `等 ${homeFeatureCards.length} 个 IP` },
  { label: '已收录角色', value: `${genshinShowcaseCharacters.length} 位`, note: '持续更新中' },
  { label: '体验流程', value: '搜索 / 选角 / 生成', note: '一步直达' },
]
