export type HomeQuote = {
  key: string
  text: string
  speaker: string
  ipName: string
}

/**
 * 首页角色台词库。
 * 后续新增台词时，继续按照同样结构补充即可。
 */
export const homeQuotes: HomeQuote[] = [
  {
    key: 'furina-welcome',
    text: '欢迎来到水的国度，我芙卡洛斯将承认你们旅途的价值与意义，现在，你们可以尽情欢呼了。',
    speaker: '芙宁娜',
    ipName: '原神',
  },
  {
    key: 'ayaka-greeting',
    text: '若你愿意驻足片刻，我也很乐意陪你把这一段心意轻声说完。',
    speaker: '神里绫华',
    ipName: '原神',
  },
  {
    key: 'nahida-wish',
    text: '每一句温柔的话语，都会像种子一样，在某个人心里慢慢发芽。',
    speaker: '纳西妲',
    ipName: '原神',
  },
]
