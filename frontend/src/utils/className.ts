const CROP_CN_MAP: Record<string, string> = {
  apple: '苹果',
  blueberry: '蓝莓',
  'cherry including sour': '樱桃',
  'corn maize': '玉米',
  grape: '葡萄',
  orange: '柑橘',
  peach: '桃',
  'pepper bell': '甜椒',
  potato: '马铃薯',
  raspberry: '覆盆子',
  soybean: '大豆',
  squash: '南瓜',
  strawberry: '草莓',
  tomato: '番茄',
}

const CONDITION_CN_MAP: Record<string, string> = {
  'apple scab': '苹果疮痂病',
  'black rot': '黑腐病',
  'cedar apple rust': '雪松苹果锈病',
  healthy: '健康',
  'powdery mildew': '白粉病',
  'cercospora leaf spot gray leaf spot': '灰斑病',
  'common rust': '普通锈病',
  'northern leaf blight': '北方叶枯病',
  'esca black measles': '埃斯卡病（黑麻疹）',
  'leaf blight isariopsis leaf spot': '叶枯病（异孢叶斑）',
  'haunglongbing citrus greening': '黄龙病（柑橘黄化病）',
  'bacterial spot': '细菌性斑点病',
  'early blight': '早疫病',
  'late blight': '晚疫病',
  'leaf mold': '叶霉病',
  'septoria leaf spot': '斑枯病',
  'spider mites two spotted spider mite': '二斑叶螨',
  'target spot': '靶斑病',
  'tomato yellow leaf curl virus': '番茄黄化曲叶病毒病',
  'tomato mosaic virus': '番茄花叶病毒病',
  'leaf scorch': '叶焦病',
  unknown: '未知',
}

function normalizeKey(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, ' ').replace(/\s+/g, ' ').trim()
}

function fallbackName(value: string) {
  return value.replace(/___/g, ' - ').replace(/_/g, ' ').replace(/\s+/g, ' ').trim()
}

function translateSegment(value: string, map: Record<string, string>) {
  return map[normalizeKey(value)]
}

export function toDisplayName(name: string) {
  const text = (name || '').trim()
  if (!text) return ''
  const [cropRaw, conditionRaw] = text.split('___')
  if (conditionRaw !== undefined) {
    const crop = translateSegment(cropRaw, CROP_CN_MAP) || fallbackName(cropRaw)
    const condition = translateSegment(conditionRaw, CONDITION_CN_MAP) || fallbackName(conditionRaw)
    return `${crop} - ${condition}`
  }
  return translateSegment(text, CROP_CN_MAP) || translateSegment(text, CONDITION_CN_MAP) || fallbackName(text)
}

