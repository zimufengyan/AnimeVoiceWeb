import slideImg from '@/assets/slideImgs/slideimg.png'
import slideImg1 from '@/assets/slideImgs/slideimg1.png'
import slideImg2 from '@/assets/slideImgs/slideimg2.png'
import slideImg3 from '@/assets/slideImgs/slideimg3.png'
import slideImg4 from '@/assets/slideImgs/slideimg4.png'
import slideImg5 from '@/assets/slideImgs/slideimg5.png'
import slideImg6 from '@/assets/slideImgs/slideimg6.png'
import slideImg7 from '@/assets/slideImgs/slideimg7.png'
import slideImg8 from '@/assets/slideImgs/slideimg8.png'
import slideImg9 from '@/assets/slideImgs/slideimg9.png'

export type SlideVerifyImageGroup = 'default' | 'genshin' | 'starrail'

const defaultImages = [
  slideImg,
  slideImg1,
  slideImg2,
  slideImg3,
  slideImg4,
  slideImg5,
  slideImg6,
  slideImg7,
  slideImg8,
  slideImg9,
]

export const slideVerifyImageGroups: Record<SlideVerifyImageGroup, string[]> = {
  default: defaultImages,
  genshin: defaultImages,
  starrail: defaultImages,
}
