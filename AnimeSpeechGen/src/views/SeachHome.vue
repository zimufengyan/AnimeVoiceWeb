<template>
  <div class="search-home">
    <section class="hero-panel">
      <div class="hero-glow hero-glow-left"></div>
      <div class="hero-glow hero-glow-right"></div>
      <div class="hero-grid">
        <div class="hero-copy">
          <div class="hero-chip-row">
            <span class="hero-chip">AnimeVoice Stage</span>
            <span class="hero-chip subtle">Multi-IP Collection</span>
          </div>

          <div class="hero-title-block">
            <h1>二次元语音工坊</h1>
            <p class="hero-description">
              搜索角色，切换形象，快速生成台词演绎。
            </p>
          </div>

          <el-autocomplete
            v-model="searchQuery"
            :fetch-suggestions="querySearch"
            placeholder="搜索角色或主题"
            class="hero-search"
            popper-class="hero-search-popper"
            @select="handleSelect"
          >
            <template #prefix>
              <Icon icon="ph:magnifying-glass-bold" class="search-prefix-icon" />
            </template>

            <template #default="{ item }">
              <div class="suggestion-item">
                <span class="suggestion-title">
                  <span>{{ item.value }}</span>
                  <span class="suggestion-title-english">{{ item.englishName }}</span>
                </span>
                <span class="suggestion-meta">{{ item.metaText }}</span>
              </div>
            </template>
          </el-autocomplete>

          <div class="quick-action-row">
            <el-button class="primary-action" type="primary" @click="navigateTo('/genshin')">
              进入原神工坊
            </el-button>
            <el-button class="secondary-action" plain @click="scrollToFeatureHall">
              查看推荐角色
            </el-button>
            <el-button class="secondary-action" plain @click="showComingSoonMessage">
              查看更多主题
            </el-button>
          </div>

          <div class="hero-metric-grid">
            <article
              v-for="metric in homeHeroMetrics"
              :key="metric.label"
              class="hero-metric-card"
            >
              <span class="metric-label">{{ metric.label }}</span>
              <strong class="metric-value">{{ metric.value }}</strong>
              <span class="metric-note">{{ metric.note }}</span>
            </article>
          </div>

          <div class="quote-card">
            <div class="quote-toolbar">
              <button
                class="quote-refresh-btn"
                :class="{ rotating: isQuoteRefreshing }"
                type="button"
                @click="handleQuoteRefresh"
              >
                <Icon icon="solar:refresh-bold-duotone" class="quote-refresh-icon" />
                <span>换一句</span>
              </button>
            </div>
            <p class="quote-text">{{ activeQuote.text }}</p>
            <div class="quote-speaker-line">
              <span class="quote-speaker">——{{ activeQuote.speaker }} · {{ activeQuote.ipName }}</span>
            </div>
          </div>
        </div>

        <div class="hero-carousel-shell">
          <div class="carousel-header">
            <h2>{{ currentHeroSlide?.title || '本周精选' }}</h2>
          </div>

          <el-carousel
            ref="carouselRef"
            :interval="7000"
            arrow="never"
            height="460px"
            indicator-position="none"
            trigger="click"
            @change="handleCarouselChange"
          >
            <el-carousel-item v-for="slide in heroSlidesView" :key="slide.key">
                <article class="hero-slide" :style="getCoverStyle(slide.backgroundImage)">
                  <div class="hero-slide-overlay"></div>

                  <div class="slide-top-row">
                    <span class="slide-badge">{{ slide.badge }}</span>
                  </div>

                  <img :src="slide.logo" alt="slide-logo" class="slide-logo" />

                  <div class="slide-body">
                    <h3>{{ slide.title }}</h3>
                    <p class="slide-description">{{ slide.description }}</p>
                  </div>

                <div class="slide-bottom-area">
                  <div class="slide-character-row">
                    <button
                      v-for="character in slide.characters"
                      :key="character.key"
                      class="slide-character-pill"
                      type="button"
                      @click="openCharacterWorkshop(character)"
                    >
                      <img :src="character.avatarUrl" :alt="character.displayName" class="slide-avatar" />
                      <div class="slide-character-copy">
                        <strong>{{ character.displayName }}</strong>
                        <span>{{ character.subtitle }}</span>
                      </div>
                    </button>
                  </div>

                  <div class="slide-action-row">
                    <el-button class="slide-primary-btn" type="primary" @click="navigateTo(slide.route)">
                      {{ slide.ctaText }}
                    </el-button>
                    <button class="slide-text-btn" @click="scrollToFeatureHall">查看主题入口</button>
                  </div>
                </div>
              </article>
            </el-carousel-item>
          </el-carousel>

          <div class="carousel-indicator-row">
            <button
              v-for="(slide, index) in heroSlidesView"
              :key="slide.key"
              class="carousel-indicator"
                :class="{ active: activeHeroIndex === index }"
                @click="setActiveHero(index)"
              >
                <span class="indicator-title">{{ slide.indicatorLabel }}</span>
              </button>
            </div>
        </div>
      </div>
    </section>

    <section ref="featureSectionRef" class="feature-section">
      <div class="section-heading">
        <div>
          <p class="section-eyebrow">IP 入口大厅</p>
          <h2>当前开放与筹备中的主题入口</h2>
        </div>
        <p class="section-description">
          原神主题现已开放，星穹铁道主题将于后续上线。
        </p>
      </div>

      <div class="feature-grid">
        <article
          v-for="card in featureCardsView"
          :key="card.key"
          class="feature-card"
          :class="{ 'is-upcoming': card.state === 'upcoming' }"
        >
          <div class="feature-cover" :style="getCoverStyle(card.coverImage)"></div>
          <div class="feature-cover-overlay"></div>

          <div class="feature-content">
            <div class="feature-top-row">
              <img :src="card.logo" :alt="card.title" class="feature-logo" />
              <span class="feature-state">{{ card.state === 'active' ? 'LIVE' : 'COMING SOON' }}</span>
            </div>

            <div class="feature-copy">
              <p class="feature-subtitle">{{ card.subtitle }}</p>
              <h3>{{ card.title }}</h3>
              <p class="feature-description">{{ card.description }}</p>
            </div>

            <div class="feature-tag-row">
              <span v-for="tag in card.tags" :key="tag" class="feature-tag">{{ tag }}</span>
            </div>

            <div v-if="card.characters.length" class="feature-avatar-row">
              <button
                v-for="character in card.characters"
                :key="character.key"
                class="feature-avatar-pill"
                type="button"
                @click="openCharacterWorkshop(character)"
              >
                <img
                  :src="character.avatarUrl"
                  :alt="character.displayName"
                  class="feature-avatar"
                />
                <span>{{ character.displayName }}</span>
              </button>
            </div>

            <div class="feature-action-row">
              <el-button
                class="feature-action-btn feature-primary-action"
                type="primary"
                @click="handleFeaturePrimaryAction(card)"
              >
                {{ card.primaryAction }}
              </el-button>
              <el-button
                class="feature-action-btn feature-secondary-action"
                @click="handleFeatureSecondaryAction(card)"
              >
                {{ card.secondaryAction }}
              </el-button>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script lang="ts" setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { CarouselInstance } from 'element-plus'
import { Icon } from '@iconify/vue'
import {
  genshinShowcaseCharacters,
  homeFeatureCards,
  homeHeroMetrics,
  homeHeroSlides,
} from '@/config/homeShowcase'
import { homeQuotes } from '@/config/homeQuotes'

type SearchSuggestionItem = {
  value: string
  route: string
  category: string
  keywords: string[]
  isAvailable: boolean
  characterName?: string
  ipName: string
  englishName: string
  metaText: string
}

const router = useRouter()
const carouselRef = ref<CarouselInstance | null>(null)
const featureSectionRef = ref<HTMLElement | null>(null)
const quoteIndex = ref(0)
const quoteTimerId = ref<ReturnType<typeof setInterval> | null>(null)
const quoteRefreshResetTimer = ref<ReturnType<typeof setTimeout> | null>(null)
const isQuoteRefreshing = ref(false)
const activeHeroIndex = ref(0)
const searchQuery = ref('')

const API_PORT = import.meta.env.VITE_API_PORT || '25683'
const apiOrigin =
  (import.meta.env.VITE_API_ORIGIN as string | undefined)?.replace(/\/$/, '') ||
  `${window.location.protocol}//${window.location.hostname}:${API_PORT}`

const buildBackendAvatarUrl = (belong: string, filename: string) => {
  return `${apiOrigin}/static/character_avator/${belong}/${encodeURIComponent(filename)}`
}

const showcasedCharacters = computed(() =>
  genshinShowcaseCharacters.map((character) => ({
    ...character,
    selectionName: character.filename.replace(/\.[^.]+$/, ''),
    avatarUrl: buildBackendAvatarUrl('GenShin', character.filename),
  })),
)

const characterMap = computed(() => {
  return new Map(showcasedCharacters.value.map((character) => [character.key, character]))
})

const heroSlidesView = computed(() =>
  homeHeroSlides.map((slide) => ({
    ...slide,
    logo: homeFeatureCards[0].logo,
    characters: slide.characterKeys
      .map((characterKey) => characterMap.value.get(characterKey))
      .filter((character): character is (typeof showcasedCharacters.value)[number] => Boolean(character)),
  })),
)

const featureCardsView = computed(() =>
  homeFeatureCards.map((card) => ({
    ...card,
    characters: card.featuredCharacterKeys
      .map((characterKey) => characterMap.value.get(characterKey))
      .filter((character): character is (typeof showcasedCharacters.value)[number] => Boolean(character)),
  })),
)

const activeQuote = computed(() => {
  return homeQuotes[quoteIndex.value] || homeQuotes[0]
})

const suggestionItems = computed<SearchSuggestionItem[]>(() => {
  const activeCards = featureCardsView.value
    .filter((card) => card.state === 'active' && card.route)
    .map((card) => ({
      value: card.title,
      route: card.route || '/',
      category: 'IP 页面',
      keywords: [card.title, card.subtitle, ...card.tags, '原神', 'genshin'],
      isAvailable: true,
      ipName: '原神',
      englishName: 'Genshin Impact',
      metaText: '原神',
    }))

  const characterSuggestions = showcasedCharacters.value.map((character) => ({
    value: character.displayName,
    route: '/genshin',
    category: '角色',
    keywords: [...character.keywords, character.subtitle, '原神', 'genshin'],
    isAvailable: true,
    characterName: character.selectionName,
    ipName: '原神',
    englishName: character.subtitle,
    metaText: '角色 · 原神',
  }))

  return [...activeCards, ...characterSuggestions]
})

const rotateQuote = (withAnimation = true) => {
  if (!homeQuotes.length) return

  if (withAnimation) {
    isQuoteRefreshing.value = true
    if (quoteRefreshResetTimer.value) {
      clearTimeout(quoteRefreshResetTimer.value)
    }
    quoteRefreshResetTimer.value = setTimeout(() => {
      isQuoteRefreshing.value = false
      quoteRefreshResetTimer.value = null
    }, 320)
  }

  quoteIndex.value = (quoteIndex.value + 1) % homeQuotes.length
}

const handleQuoteRefresh = (event: MouseEvent) => {
  rotateQuote()
  ;(event.currentTarget as HTMLButtonElement | null)?.blur()
}

const startQuoteTimer = () => {
  if (quoteTimerId.value) clearInterval(quoteTimerId.value)
  quoteTimerId.value = setInterval(() => {
    rotateQuote(false)
  }, 12000)
}

const navigateTo = (
  route: string,
  isAvailable = true,
  query?: Record<string, string>,
) => {
  if (!isAvailable) {
    showComingSoonMessage()
    return
  }

  router.push({
    path: route,
    query,
  })
}

const showComingSoonMessage = () => {
  ElMessage({
    message: '星穹铁道主题仍在制作中，完成后会以独立主题页上线。',
    type: 'info',
  })
}

const scrollToFeatureHall = () => {
  featureSectionRef.value?.scrollIntoView({
    behavior: 'smooth',
    block: 'start',
  })
}

const handleFeaturePrimaryAction = (card: (typeof featureCardsView.value)[number]) => {
  navigateTo(card.route || '/genshin', card.state === 'active')
}

const handleFeatureSecondaryAction = (card: (typeof featureCardsView.value)[number]) => {
  if (card.state === 'active') {
    navigateTo(card.route || '/genshin')
    return
  }

  navigateTo('/genshin')
}

const openCharacterWorkshop = (character: (typeof showcasedCharacters.value)[number]) => {
  navigateTo('/genshin', true, {
    character: character.selectionName,
  })
}

const querySearch = (
  queryString: string,
  cb: (results: SearchSuggestionItem[]) => void,
) => {
  const normalizedQuery = queryString.trim().toLowerCase()
  const results = suggestionItems.value.filter((item) => {
    if (!normalizedQuery) return true

    const haystack = [item.value, item.englishName, item.ipName, item.metaText, item.category, ...item.keywords]
      .join(' ')
      .toLowerCase()
    return haystack.includes(normalizedQuery)
  })

  cb(results.slice(0, 8))
}

const handleSelect = (item: SearchSuggestionItem) => {
  searchQuery.value = item.value
  navigateTo(
    item.route,
    item.isAvailable,
    item.characterName
      ? {
          character: item.characterName,
        }
      : undefined,
  )
}

const handleCarouselChange = (index: number) => {
  activeHeroIndex.value = index
}

const currentHeroSlide = computed(() => heroSlidesView.value[activeHeroIndex.value] ?? heroSlidesView.value[0] ?? null)

const setActiveHero = (index: number) => {
  carouselRef.value?.setActiveItem(index)
  activeHeroIndex.value = index
}

const getCoverStyle = (imageUrl: string) => {
  return {
    backgroundImage: `linear-gradient(135deg, rgba(9, 27, 40, 0.2), rgba(10, 19, 45, 0.78)), url(${imageUrl})`,
  }
}

onMounted(() => {
  startQuoteTimer()
})

onUnmounted(() => {
  if (quoteTimerId.value) {
    clearInterval(quoteTimerId.value)
    quoteTimerId.value = null
  }
  if (quoteRefreshResetTimer.value) {
    clearTimeout(quoteRefreshResetTimer.value)
    quoteRefreshResetTimer.value = null
  }
})
</script>

<style scoped>
.search-home {
  position: relative;
  min-height: 100%;
  padding: 1.4rem clamp(1rem, 2vw, 2rem) 3.5rem;
  color: #17303d;
  background:
    radial-gradient(circle at top left, rgba(134, 199, 193, 0.4), transparent 28%),
    radial-gradient(circle at top right, rgba(248, 204, 142, 0.24), transparent 24%),
    linear-gradient(180deg, #edf4f6 0%, #eef3f7 42%, #f7f9fc 100%);
  overflow: hidden;
}

.search-home::before,
.search-home::after {
  content: '';
  position: absolute;
  inset: auto;
  pointer-events: none;
}

.search-home::before {
  top: 4rem;
  right: -8rem;
  width: 22rem;
  height: 22rem;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(120, 196, 188, 0.22), transparent 68%);
  filter: blur(4px);
}

.search-home::after {
  left: -6rem;
  bottom: 4rem;
  width: 18rem;
  height: 18rem;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(240, 201, 140, 0.16), transparent 70%);
}

.hero-panel,
.feature-card,
.hero-metric-card,
.quote-card {
  border: 1px solid rgba(114, 159, 174, 0.18);
  box-shadow: 0 24px 60px rgba(26, 66, 91, 0.08);
}

.hero-panel {
  position: relative;
  overflow: hidden;
  padding: clamp(1.4rem, 2vw, 2rem);
  border-radius: 36px;
  background:
    linear-gradient(140deg, rgba(255, 255, 255, 0.95), rgba(244, 251, 255, 0.88)),
    linear-gradient(180deg, rgba(123, 190, 184, 0.12), rgba(255, 224, 179, 0.1));
}

.hero-glow {
  position: absolute;
  width: 18rem;
  height: 18rem;
  border-radius: 50%;
  filter: blur(16px);
  pointer-events: none;
}

.hero-glow-left {
  left: -8rem;
  top: 2rem;
  background: radial-gradient(circle, rgba(111, 196, 187, 0.3), transparent 70%);
}

.hero-glow-right {
  right: -6rem;
  bottom: -6rem;
  background: radial-gradient(circle, rgba(251, 204, 144, 0.28), transparent 72%);
}

.hero-grid {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.05fr) minmax(320px, 0.95fr);
  align-items: stretch;
  gap: 1.75rem;
  z-index: 1;
}

.hero-copy,
.hero-carousel-shell {
  position: relative;
  z-index: 1;
}

.hero-copy {
  display: flex;
  flex-direction: column;
  min-height: 100%;
  gap: 1rem;
}

.hero-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.hero-chip {
  display: inline-flex;
  align-items: center;
  padding: 0.4rem 0.9rem;
  border-radius: 999px;
  color: #1d5c63;
  font-size: 0.82rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  background: rgba(111, 196, 187, 0.16);
}

.hero-chip.subtle {
  color: #7a5a35;
  background: rgba(246, 201, 139, 0.2);
}

.hero-title-block {
  margin-top: 0;
}

.hero-eyebrow,
.section-eyebrow {
  color: #4b7b88;
  font-size: 0.9rem;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.hero-title-block h1,
.section-heading h2,
.carousel-header h2 {
  margin: 0;
  color: #19313b;
  font-size: clamp(2rem, 2.7vw, 3rem);
  line-height: 1.1;
  font-weight: 700;
}

.hero-description,
.section-description {
  max-width: 41rem;
  margin-top: 0.9rem;
  color: #5b7280;
  font-size: 0.98rem;
  line-height: 1.75;
}

.hero-search {
  width: 100%;
  margin-top: 0;
}

.search-prefix-icon {
  font-size: 1.2rem;
  color: #5a8d96;
}

::v-deep(.hero-search .el-input__wrapper) {
  min-height: 4.4rem;
  padding: 0 1.15rem;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.78);
  box-shadow:
    0 18px 40px rgba(24, 63, 84, 0.09),
    inset 0 0 0 1px rgba(126, 172, 182, 0.16);
}

::v-deep(.hero-search .el-input__inner) {
  font-size: 1rem;
  color: #19313b;
}

.quick-action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.9rem;
  margin-top: 0;
}

.primary-action,
.slide-primary-btn,
.feature-primary-action {
  min-height: 2.95rem;
  padding: 0 1.35rem;
  border: none;
  border-radius: 999px;
  background: linear-gradient(135deg, #63b5ae, #82c8c1);
  box-shadow: 0 14px 30px rgba(83, 173, 164, 0.26);
}

.secondary-action {
  min-height: 2.95rem;
  border-radius: 999px;
  border-color: rgba(110, 155, 164, 0.25);
  color: #315966;
  background: rgba(255, 255, 255, 0.66);
}

.hero-metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.85rem;
  margin-top: 0;
}

.hero-metric-card,
.quote-card {
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(12px);
}

.hero-metric-card {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  padding: 0.9rem 1rem;
  background: rgba(255, 255, 255, 0.58);
  box-shadow: inset 0 0 0 1px rgba(129, 170, 182, 0.1);
}

.metric-label,
.metric-note {
  color: #66818e;
  font-size: 0.85rem;
}

.metric-value {
  color: #183540;
  font-size: 1.18rem;
  font-weight: 700;
}

.quote-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 0.95rem;
  flex: 1;
  min-height: 0;
  padding: 1.15rem 1.2rem 1.05rem;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(244, 251, 254, 0.78)),
    linear-gradient(135deg, rgba(111, 196, 187, 0.1), rgba(247, 206, 148, 0.08));
  border-color: rgba(106, 167, 176, 0.24);
  box-shadow:
    0 22px 46px rgba(30, 72, 94, 0.1),
    inset 0 0 0 1px rgba(255, 255, 255, 0.4);
}

.quote-text {
  color: #2a4f5b;
  font-size: 1.02rem;
  line-height: 1.9;
  margin: 0;
}

.quote-toolbar {
  display: flex;
  justify-content: flex-end;
}

.quote-refresh-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.42rem;
  min-height: 2.15rem;
  padding: 0 0.82rem;
  border: 1px solid rgba(83, 148, 158, 0.26);
  border-radius: 999px;
  color: #35626f;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.86), rgba(241, 248, 251, 0.92)),
    linear-gradient(135deg, rgba(111, 196, 187, 0.12), rgba(247, 206, 148, 0.08));
  cursor: pointer;
  box-shadow:
    0 8px 20px rgba(46, 92, 114, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.55);
  transition:
    transform 0.2s ease,
    background-color 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease;
  font-size: 0.82rem;
  font-weight: 600;
  letter-spacing: 0.03em;
  outline: none;
}

.quote-refresh-icon {
  font-size: 1rem;
  color: #58a59d;
  transition: transform 0.32s ease;
}

.quote-refresh-btn:hover {
  border-color: rgba(88, 165, 157, 0.34);
  color: #274d58;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(242, 250, 251, 0.98)),
    linear-gradient(135deg, rgba(111, 196, 187, 0.16), rgba(247, 206, 148, 0.1));
  box-shadow:
    0 12px 26px rgba(46, 92, 114, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.65);
}

.quote-refresh-btn:focus,
.quote-refresh-btn:focus-visible,
.quote-refresh-btn:active {
  outline: none;
  border-color: rgba(83, 148, 158, 0.26);
  color: #35626f;
  box-shadow:
    0 8px 20px rgba(46, 92, 114, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.55);
}

.quote-refresh-btn.rotating .quote-refresh-icon {
  transform: rotate(180deg);
}

.quote-speaker-line {
  display: flex;
  justify-content: flex-end;
  margin-top: auto;
  padding-top: 0.15rem;
}

.quote-speaker {
  position: relative;
  padding-left: 1.35rem;
  color: #5b7f8b;
  font-size: 0.9rem;
  text-align: right;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.quote-speaker::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  width: 0.95rem;
  height: 1px;
  background: linear-gradient(90deg, rgba(88, 165, 157, 0), rgba(88, 165, 157, 0.55));
}

.hero-carousel-shell {
  display: flex;
  flex-direction: column;
  gap: 0.78rem;
  padding: 0.8rem 1rem 1rem;
  border-radius: 30px;
  background: rgba(17, 28, 44, 0.82);
  box-shadow: inset 0 0 0 1px rgba(133, 180, 194, 0.14);
}

.carousel-header {
  display: flex;
  align-items: center;
  min-height: 2.7rem;
  padding: 0.05rem 0 0.1rem;
}

.carousel-header h2 {
  margin: 0;
  color: #f5fbfe;
  font-size: 1.55rem;
  line-height: 1.08;
}

.hero-slide {
  position: relative;
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 1.15rem 1.2rem;
  border-radius: 26px;
  background-position: center;
  background-size: cover;
  overflow: hidden;
}

.hero-slide-overlay,
.feature-cover-overlay {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(8, 15, 28, 0.16), rgba(6, 14, 25, 0.72)),
    radial-gradient(circle at 20% 20%, rgba(132, 226, 217, 0.28), transparent 25%);
}

.slide-top-row,
.slide-body,
.slide-character-row,
.slide-action-row {
  position: relative;
  z-index: 1;
}

.slide-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.slide-badge {
  display: inline-flex;
  align-items: center;
  min-height: 2rem;
  padding: 0.35rem 0.8rem;
  border-radius: 999px;
  font-size: 0.78rem;
  color: #f4f7f8;
  background: rgba(255, 255, 255, 0.18);
  backdrop-filter: blur(8px);
}

.slide-logo {
  position: relative;
  z-index: 1;
  width: 6.2rem;
  margin-top: 0.45rem;
  object-fit: contain;
  filter: drop-shadow(0 10px 24px rgba(6, 14, 25, 0.25));
}

.slide-body {
  margin-top: 0.25rem;
  max-width: 23rem;
  color: #f7fbfd;
}

.slide-body h3 {
  margin: 0.35rem 0 0;
  font-size: clamp(1.42rem, 1.8vw, 2.05rem);
  line-height: 1.15;
  font-weight: 700;
}

.slide-description {
  margin-top: 0.65rem;
  color: rgba(240, 248, 250, 0.85);
  font-size: 0.92rem;
  line-height: 1.65;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.slide-bottom-area {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  margin-top: auto;
}

.slide-character-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin-top: 0.2rem;
}

.slide-character-pill,
.feature-avatar-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.38rem 0.55rem;
  border: none;
  border-radius: 999px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.14);
  backdrop-filter: blur(9px);
  transition:
    transform 0.2s ease,
    background-color 0.2s ease;
}

.slide-character-pill:hover,
.feature-avatar-pill:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.2);
}

.slide-avatar,
.feature-avatar {
  width: 2.2rem;
  height: 2.2rem;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid rgba(255, 255, 255, 0.48);
}

.slide-character-copy,
.feature-avatar-pill span {
  color: #f5fbfd;
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.slide-character-copy span {
  color: rgba(231, 245, 247, 0.72);
  font-size: 0.76rem;
}

.slide-action-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-top: 0;
}

.slide-text-btn {
  border: none;
  padding: 0;
  color: #eef8fb;
  font-size: 0.9rem;
  background: transparent;
}

.slide-text-btn:hover {
  color: #9de1d7;
}

.carousel-indicator-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0.8rem;
}

.carousel-indicator {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  align-items: flex-start;
  min-height: 4.2rem;
  padding: 0.9rem 1rem;
  border: 1px solid transparent;
  border-radius: 18px;
  color: rgba(221, 238, 242, 0.72);
  background: rgba(255, 255, 255, 0.05);
  transition:
    transform 0.25s ease,
    border-color 0.25s ease,
    background-color 0.25s ease;
}

.carousel-indicator:hover,
.carousel-indicator.active {
  transform: translateY(-2px);
  border-color: rgba(141, 214, 204, 0.38);
  color: #f4fcff;
  background: rgba(104, 173, 166, 0.18);
}

.indicator-title {
  font-size: 0.95rem;
  font-weight: 600;
}

.feature-section,
.bulletin-section {
  margin-top: 2rem;
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 1.2rem;
  margin-bottom: 1.1rem;
}

.section-heading.compact {
  align-items: center;
}

.section-heading h2 {
  font-size: clamp(1.65rem, 2.3vw, 2.35rem);
}

.feature-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1.1rem;
}

.feature-card {
  position: relative;
  min-height: 25rem;
  border-radius: 28px;
  overflow: hidden;
  background: #0f2030;
}

.feature-cover {
  position: absolute;
  inset: 0;
  background-position: center;
  background-size: cover;
  transform: scale(1.05);
}

.feature-content {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 100%;
  padding: 1.35rem;
  color: #f6fbfd;
}

.feature-card.is-upcoming {
  filter: saturate(0.9);
}

.feature-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.feature-logo {
  width: 7rem;
  max-height: 3rem;
  object-fit: contain;
  filter: drop-shadow(0 10px 22px rgba(7, 14, 26, 0.26));
}

.feature-state {
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  color: #e7f8f5;
  font-size: 0.76rem;
  letter-spacing: 0.08em;
  background: rgba(255, 255, 255, 0.16);
}

.feature-copy {
  margin-top: auto;
}

.feature-subtitle {
  color: rgba(220, 239, 243, 0.82);
  font-size: 0.92rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.feature-copy h3 {
  margin: 0.45rem 0 0;
  font-size: 1.9rem;
  font-weight: 700;
}

.feature-description {
  margin-top: 0.75rem;
  color: rgba(236, 246, 248, 0.84);
  line-height: 1.8;
}

.feature-tag-row,
.feature-avatar-row,
.feature-action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.7rem;
  margin-top: 1rem;
}

.feature-tag {
  display: inline-flex;
  align-items: center;
  min-height: 2rem;
  padding: 0.35rem 0.75rem;
  border-radius: 999px;
  color: #f4fbfd;
  font-size: 0.82rem;
  background: rgba(255, 255, 255, 0.14);
}

.feature-avatar-row {
  margin-top: 1.1rem;
}

.feature-action-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: stretch;
  margin-top: 1.25rem;
}

.feature-action-btn {
  min-height: 3rem;
  width: 100%;
  margin: 0;
  border-radius: 999px;
  font-weight: 600;
  justify-content: center;
}

.feature-primary-action {
  min-width: 8rem;
}

.feature-secondary-action {
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #f4fbfd;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
}

.feature-secondary-action:hover,
.feature-secondary-action:focus {
  color: #ffffff;
  border-color: rgba(162, 228, 218, 0.45);
  background: rgba(111, 196, 187, 0.18);
}

:global(.hero-search-popper .el-autocomplete-suggestion__list) {
  padding: 0.45rem;
}

:global(.hero-search-popper .el-autocomplete-suggestion li) {
  padding: 0;
}

.suggestion-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  min-height: 3rem;
  padding: 0.7rem 0.9rem;
  border-radius: 14px;
}

.suggestion-item:hover {
  background: rgba(110, 190, 182, 0.08);
}

.suggestion-title {
  display: inline-flex;
  align-items: baseline;
  gap: 0.45rem;
  color: #1e3845;
  font-weight: 600;
  white-space: nowrap;
}

.suggestion-title-english {
  color: #5c7581;
  font-size: 0.88rem;
  font-weight: 500;
}

.suggestion-meta {
  color: #5a7a86;
  font-size: 0.84rem;
  white-space: nowrap;
}

@media (max-width: 1200px) {
  .hero-grid,
  .feature-grid {
    grid-template-columns: 1fr;
  }

  .section-heading {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 768px) {
  .search-home {
    padding: 0.8rem 0.8rem 2rem;
  }

  .hero-panel {
    border-radius: 28px;
    padding: 1rem;
  }

  .hero-title-block h1,
  .section-heading h2,
  .carousel-header h2 {
    font-size: 1.8rem;
  }

  .hero-metric-grid,
  .carousel-indicator-row {
    grid-template-columns: 1fr;
  }

  .slide-action-row,
  .feature-action-row {
    grid-template-columns: 1fr;
  }

  .slide-primary-btn,
  .feature-action-btn,
  .quick-action-row .el-button {
    width: 100%;
  }
}
</style>
