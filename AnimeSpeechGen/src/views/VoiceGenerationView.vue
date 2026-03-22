<template>
  <div class="voice-workshop" :class="`theme-${theme.key}`" :style="workshopStyle">
    <div class="atmosphere-layer">
      <div class="ambient-orb ambient-orb-left"></div>
      <div class="ambient-orb ambient-orb-right"></div>
      <div class="ambient-grid"></div>
      <div class="ambient-particles"></div>
    </div>

    <section class="workshop-frame">
      <header class="workshop-toolbar">
        <el-autocomplete
          v-model="searchQuery"
          :fetch-suggestions="querySearch"
          :placeholder="theme.searchPlaceholder"
          class="workshop-search"
          popper-class="workshop-search-popper"
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
      </header>

      <section class="workshop-main">
        <div class="stage-column">
          <div class="stage-shell" @mousemove="handleStagePointerMove" @mouseleave="resetStageParallax">
            <div class="stage-canvas">
              <Transition name="stage-character" mode="out-in">
                <div v-if="chooseCharacter.url" :key="`character-${chooseCharacter.name}`" class="stage-character-card">
                  <div class="stage-character-glow"></div>
                  <img
                    :src="chooseCharacter.url"
                    :alt="currentCharacterDisplayName"
                    class="stage-character-image"
                    loading="lazy"
                    :style="stageCharacterStyle"
                  />
                </div>
                <div v-else key="character-empty" class="stage-empty-card">
                  <Icon icon="solar:gallery-minimalistic-broken" class="stage-empty-icon" />
                  <p>{{ theme.emptyDescription }}</p>
                </div>
              </Transition>
            </div>
          </div>

          <div class="character-rail-shell" @wheel.prevent="handleCharacterRailWheel">
            <Swiper
              class="character-swiper"
              :modules="swiperModules"
              effect="coverflow"
              :slides-per-view="'auto'"
              :centered-slides="true"
              :grab-cursor="true"
              :space-between="16"
              :slide-to-clicked-slide="true"
              :mousewheel="{ enabled: false }"
              :coverflow-effect="coverflowEffect"
              @swiper="handleSwiperReady"
              @slideChange="handleSwiperChange"
            >
              <SwiperSlide
                v-for="card in characterCards"
                :key="`${belong}-${card.index}`"
                class="character-slide"
              >
                <button
                  class="character-card"
                  :class="{ active: chooseCharacter.index === card.index }"
                  type="button"
                  @click.stop="handleCharacterCardClick(card.index)"
                >
                  <span class="character-card-glow"></span>
                  <img :src="card.avator" :alt="card.meta.displayName" class="character-card-avatar" />
                  <span class="character-card-copy">
                    <strong>{{ card.meta.displayName }}</strong>
                    <small>{{ card.meta.englishName }}</small>
                  </span>
                </button>
              </SwiperSlide>
            </Swiper>
          </div>
        </div>

        <aside class="control-column">
          <div class="control-shell">
            <div class="character-summary">
              <div class="summary-avatar-wrap">
                <img
                  v-if="chooseCharacter.avator"
                  :src="chooseCharacter.avator"
                  :alt="currentCharacterDisplayName"
                  class="summary-avatar"
                />
                <div v-else class="summary-avatar empty">
                  <Icon icon="solar:user-rounded-broken" />
                </div>
              </div>

              <div class="summary-copy">
                <strong>{{ currentCharacterDisplayName }}</strong>
                <span>{{ currentCharacterMeta.englishName || theme.displayName }}</span>
              </div>

              <div class="summary-tags">
                <span
                  v-for="tag in currentCharacterMeta.tags.slice(0, 2)"
                  :key="tag"
                  class="summary-tag"
                >
                  {{ tag }}
                </span>
              </div>
            </div>

            <el-input
              v-model="textarea"
              :rows="9"
              type="textarea"
              :placeholder="theme.textPlaceholder"
              maxlength="120"
              show-word-limit
              class="voice-textarea"
            />

            <div class="action-row">
              <el-button
                class="generate-action"
                :class="{ generating: isGeneratingVoice }"
                type="primary"
                :loading="isGeneratingVoice"
                :disabled="!canGenerate"
                @click="handleGenerateBtn"
              >
                <Icon icon="solar:magic-stick-3-bold-duotone" />
                <span>生成语音</span>
              </el-button>

              <el-button class="download-action" :disabled="!canDownload" @click="handleDownloadBtn">
                <Icon icon="solar:download-bold-duotone" />
              </el-button>
            </div>

            <div class="audio-shell" :class="{ ready: Boolean(audio_url) }">
              <audio
                v-if="audio_url"
                ref="audioPlayer"
                :key="audio_url"
                :src="audio_url"
                preload="metadata"
                class="audio-player"
                @loadedmetadata="handleAudioLoadedMetadata"
                @timeupdate="handleAudioTimeUpdate"
                @ended="handleAudioEnded"
              ></audio>
              <div v-if="audio_url" class="audio-player-card">
                <button class="audio-play-button" type="button" @click="togglePlayback">
                  <Icon :icon="isAudioPlaying ? 'ph:pause-fill' : 'ph:play-fill'" />
                </button>

                <div class="audio-player-copy">
                  <div class="audio-player-meta">
                    <strong>{{ currentCharacterDisplayName }}</strong>
                    <span>{{ formattedCurrentTime }} / {{ formattedDuration }}</span>
                  </div>

                  <input
                    class="audio-progress"
                    type="range"
                    min="0"
                    :max="Math.max(audioDuration, 0)"
                    :value="audioCurrentTime"
                    step="0.01"
                    @input="handleSeek"
                  />
                </div>
              </div>
              <div v-else class="audio-placeholder">
                <Icon icon="solar:play-stream-bold-duotone" />
                <span>生成后可试听与下载</span>
              </div>
            </div>

            <div class="agent-space" aria-hidden="true"></div>
          </div>
        </aside>
      </section>
    </section>
  </div>
</template>

<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Swiper, SwiperSlide } from 'swiper/vue'
import { EffectCoverflow, Mousewheel } from 'swiper/modules'
import type { Swiper as SwiperInstance } from 'swiper'
import 'swiper/css'
import 'swiper/css/effect-coverflow'
import { getGeneratedVoiceApi, getIpCharactersApi } from '@/api'
import { Icon } from '@iconify/vue'
import { ElMessage } from 'element-plus'
import { getVoiceWorkshopTheme } from '@/config/voiceWorkshopTheme'
import type { IpCharacterItem } from '@/util/types'

type CharacterState = {
  name: string
  url: string
  avator: string
  index: number
}

type SearchSuggestion = {
  value: string
  route: string
  category: string
  keywords: string[]
  characterName?: string
  ipName: string
  englishName: string
  metaText: string
  index?: number
}

type CharacterMeta = {
  key: string
  displayName: string
  englishName: string
  tags: string[]
  accent: string
  accentSoft: string
  aliases: string[]
  available: boolean
}

type CharacterCard = CharacterState & {
  meta: CharacterMeta
}

type ViewProps = {
  belong: string
}

const props = defineProps<ViewProps>()

const router = useRouter()
const route = useRoute()
const swiperModules = [EffectCoverflow, Mousewheel]
const coverflowEffect = { rotate: 0, stretch: -22, depth: 120, modifier: 1.1, scale: 0.92, slideShadows: false }
const searchQuery = ref('')
const chooseCharacter = ref<CharacterState>({ name: '', url: '', avator: '', index: 0 })
const latestVoiceUrl = ref('')
const audio_url = ref('')
const audioPlayer = ref<HTMLAudioElement | null>(null)
const isAudioPlaying = ref(false)
const audioCurrentTime = ref(0)
const audioDuration = ref(0)
const isGeneratingVoice = ref(false)
const isDownloadAvilabel = ref(true)
const swiperRef = ref<SwiperInstance | null>(null)
const parallaxX = ref(0)
const parallaxY = ref(0)
const charactersData = ref<IpCharacterItem[]>([])

const theme = computed(() => getVoiceWorkshopTheme(props.belong))
const belong = computed(() => props.belong)
const workshopRoute = computed(() => {
  if (theme.value.key === 'genshin') return '/genshin'
  if (theme.value.key === 'starrail') return '/starrail'
  return '/'
})
const englishIpName = computed(() => {
  if (theme.value.key === 'genshin') return 'Genshin Impact'
  if (theme.value.key === 'starrail') return 'Honkai: Star Rail'
  return theme.value.displayName
})
const textareaKey = computed(() => `${props.belong}-Textarea`)
const selectedCharacterKey = computed(() => `${props.belong}-SelectedCharacter`)
const textarea = ref(localStorage.getItem(textareaKey.value) || '')

const normalizeCharacterLookup = (value: string) => value.trim().replace(/\s+/g, '').toLowerCase()

const buildAccentSoft = (accent: string) => {
  const normalized = accent.replace('#', '')
  const expanded = normalized.length === 3
    ? normalized
        .split('')
        .map((char) => `${char}${char}`)
        .join('')
    : normalized

  if (!/^[0-9a-fA-F]{6}$/.test(expanded)) return theme.value.primarySoft
  const red = parseInt(expanded.slice(0, 2), 16)
  const green = parseInt(expanded.slice(2, 4), 16)
  const blue = parseInt(expanded.slice(4, 6), 16)
  return `rgba(${red}, ${green}, ${blue}, 0.18)`
}

const buildFallbackMeta = (name: string): CharacterMeta => ({
  key: name || '',
  displayName: name || '未命名角色',
  englishName: name || theme.value.displayName,
  tags: [theme.value.displayName],
  accent: theme.value.primary,
  accentSoft: buildAccentSoft(theme.value.primary),
  aliases: [name].filter(Boolean),
  available: true,
})

const characterCards = computed<CharacterCard[]>(() => {
  const sortedCharacters = [...charactersData.value].sort((left, right) => left.order - right.order)
  return sortedCharacters.map((character, index) => {
    const accent = character.accent || theme.value.primary
    return {
      index,
      name: character.key,
      url: character.standUrl,
      avator: character.avatarUrl,
      meta: {
        key: character.key,
        displayName: character.displayName,
        englishName: character.englishName,
        tags: character.tags || [],
        accent,
        accentSoft: buildAccentSoft(accent),
        aliases: character.aliases || [],
        available: character.available !== false,
      },
    }
  })
})

const currentCharacterCard = computed(
  () => characterCards.value.find((card) => card.index === chooseCharacter.value.index) || null,
)
const currentCharacterMeta = computed(() => currentCharacterCard.value?.meta || buildFallbackMeta(''))
const currentCharacterDisplayName = computed(() => currentCharacterMeta.value.displayName)
const canGenerate = computed(() => Boolean(chooseCharacter.value.name && textarea.value.trim()))
const canDownload = computed(() => Boolean(isDownloadAvilabel.value && audio_url.value))
const formattedCurrentTime = computed(() => formatDuration(audioCurrentTime.value))
const formattedDuration = computed(() => formatDuration(audioDuration.value))

const searchSuggestions = computed<SearchSuggestion[]>(() => {
  const workshopEntry: SearchSuggestion = {
    value: `${theme.value.displayName}语音工坊`,
    route: workshopRoute.value,
    category: 'IP 页面',
    keywords: [theme.value.displayName, englishIpName.value, '语音工坊'],
    ipName: theme.value.displayName,
    englishName: englishIpName.value,
    metaText: theme.value.displayName,
  }

  const characterEntries = characterCards.value.map((card) => ({
    value: card.meta.displayName,
    route: workshopRoute.value,
    category: '角色',
    keywords: [
      card.meta.displayName,
      card.meta.englishName,
      card.name,
      ...card.meta.aliases,
      ...card.meta.tags,
      theme.value.displayName,
      englishIpName.value,
    ],
    characterName: card.name,
    ipName: theme.value.displayName,
    englishName: card.meta.englishName,
    metaText: `角色 · ${theme.value.displayName}`,
    index: card.index,
  }))

  return [workshopEntry, ...characterEntries]
})

const workshopStyle = computed(
  () =>
    ({
      '--workshop-primary': currentCharacterMeta.value.accent,
      '--workshop-primary-soft': currentCharacterMeta.value.accentSoft,
      '--workshop-secondary': theme.value.secondary,
      '--workshop-background': theme.value.backgroundGradient,
      '--workshop-ambient': theme.value.ambientGradient,
      '--workshop-panel': theme.value.panelGradient,
      '--workshop-accent-gradient': theme.value.accentGradient,
    }) as Record<string, string>,
)

const stageCharacterStyle = computed(() => ({
  transform: `perspective(1800px) translate3d(${parallaxX.value * 16}px, ${parallaxY.value * 10}px, 0) rotateX(${parallaxY.value * -2.6}deg) rotateY(${parallaxX.value * 3.6}deg) scale(1.015)`,
}))

watch(textarea, (value) => localStorage.setItem(textareaKey.value, value || ''))
watch(() => chooseCharacter.value.name, (value) => value && localStorage.setItem(selectedCharacterKey.value, value))
watch(
  () => chooseCharacter.value.index,
  (index) => {
    if (swiperRef.value && swiperRef.value.activeIndex !== index) swiperRef.value.slideTo(index)
  },
)

const applySelectedCharacterByIndex = async (index: number, syncSwiper = true) => {
  if (index < 0 || index >= characterCards.value.length) return
  const target = characterCards.value[index]
  chooseCharacter.value = {
    index: target.index,
    name: target.name,
    url: target.url,
    avator: target.avator,
  }
  searchQuery.value = target.meta.displayName
  if (syncSwiper && swiperRef.value && swiperRef.value.activeIndex !== index) swiperRef.value.slideTo(index)
}

const applySelectedCharacterByName = async (name: string) => {
  const normalizedName = normalizeCharacterLookup(name)
  if (!normalizedName) return false
  const index = characterCards.value.findIndex((card) =>
    [card.name, card.meta.displayName, card.meta.englishName, ...card.meta.aliases]
      .filter(Boolean)
      .some((candidate) => normalizeCharacterLookup(candidate) === normalizedName),
  )
  if (index < 0) return false
  await applySelectedCharacterByIndex(index)
  return true
}

const getSavedCharacterName = () => localStorage.getItem(selectedCharacterKey.value)?.trim() || ''
const getRouteCharacterName = () => {
  const characterQuery = route.query.character
  const rawName = Array.isArray(characterQuery) ? (characterQuery[0] ?? '') : (characterQuery ?? '')
  return `${rawName}`.trim()
}

const restoreSelectedCharacter = async () => {
  if (!characterCards.value.length) {
    chooseCharacter.value = { name: '', url: '', avator: '', index: 0 }
    searchQuery.value = `${theme.value.displayName}语音工坊`
    return
  }

  const routeCharacterName = getRouteCharacterName()
  if (routeCharacterName && (await applySelectedCharacterByName(routeCharacterName))) return

  const savedCharacterName = getSavedCharacterName()
  if (savedCharacterName && (await applySelectedCharacterByName(savedCharacterName))) return

  await applySelectedCharacterByIndex(0)
}

const handleSwiperReady = (swiper: SwiperInstance) => {
  swiperRef.value = swiper
  if (characterCards.value.length && swiper.activeIndex !== chooseCharacter.value.index) {
    swiper.slideTo(chooseCharacter.value.index)
  }
}

const handleSwiperChange = (swiper: SwiperInstance) => {
  if (swiper.activeIndex !== chooseCharacter.value.index) applySelectedCharacterByIndex(swiper.activeIndex, false)
}

const handleCharacterCardClick = (index: number) => {
  applySelectedCharacterByIndex(index)
}

const handleCharacterRailWheel = (event: WheelEvent) => {
  if (!characterCards.value.length) return
  const delta = Math.abs(event.deltaY) > Math.abs(event.deltaX) ? event.deltaY : event.deltaX
  if (!delta) return

  if (delta > 0) {
    const nextIndex = Math.min(chooseCharacter.value.index + 1, characterCards.value.length - 1)
    applySelectedCharacterByIndex(nextIndex)
    return
  }

  const prevIndex = Math.max(chooseCharacter.value.index - 1, 0)
  applySelectedCharacterByIndex(prevIndex)
}

const handleStagePointerMove = (event: MouseEvent) => {
  const currentTarget = event.currentTarget as HTMLElement | null
  if (!currentTarget) return
  const rect = currentTarget.getBoundingClientRect()
  const x = (event.clientX - rect.left) / rect.width - 0.5
  const y = (event.clientY - rect.top) / rect.height - 0.5
  parallaxX.value = Math.max(-1, Math.min(1, x * 2))
  parallaxY.value = Math.max(-1, Math.min(1, y * 2))
}

const resetStageParallax = () => {
  parallaxX.value = 0
  parallaxY.value = 0
}

const syncAudioStateFromElement = () => {
  if (!audioPlayer.value) return
  audioCurrentTime.value = audioPlayer.value.currentTime || 0
  audioDuration.value = Number.isFinite(audioPlayer.value.duration) ? audioPlayer.value.duration : 0
  isAudioPlaying.value = !audioPlayer.value.paused
}

const handleAudioLoadedMetadata = () => {
  syncAudioStateFromElement()
}

const handleAudioTimeUpdate = () => {
  syncAudioStateFromElement()
}

const handleAudioEnded = () => {
  isAudioPlaying.value = false
  audioCurrentTime.value = audioDuration.value
}

const togglePlayback = async () => {
  if (!audioPlayer.value) return
  if (audioPlayer.value.paused) {
    await audioPlayer.value.play()
    isAudioPlaying.value = true
    return
  }
  audioPlayer.value.pause()
  isAudioPlaying.value = false
}

const handleSeek = (event: Event) => {
  const target = event.target as HTMLInputElement | null
  const nextTime = Number(target?.value || 0)
  audioCurrentTime.value = nextTime
  if (audioPlayer.value) audioPlayer.value.currentTime = nextTime
}

const formatDuration = (seconds: number) => {
  if (!Number.isFinite(seconds) || seconds <= 0) return '00:00'
  const minutes = Math.floor(seconds / 60)
  const remainSeconds = Math.floor(seconds % 60)
  return `${String(minutes).padStart(2, '0')}:${String(remainSeconds).padStart(2, '0')}`
}

const handleGenerateBtn = async () => {
  if (!chooseCharacter.value.name) {
    ElMessage({ message: `当前 ${props.belong} 还没有可生成的角色`, type: 'warning' })
    return
  }

  if (!textarea.value.trim()) {
    ElMessage({ message: '请输入需要生成的文本', type: 'warning' })
    return
  }

  isGeneratingVoice.value = true
  try {
    const response = await getGeneratedVoiceApi(textarea.value, chooseCharacter.value.name, props.belong, 'zh')
    latestVoiceUrl.value = response.audio_url
    audio_url.value = response.audio_url
    audioCurrentTime.value = 0
    audioDuration.value = 0
    isAudioPlaying.value = false
    if (audioPlayer.value) {
      audioPlayer.value.pause()
      audioPlayer.value.currentTime = 0
      audioPlayer.value.src = audio_url.value
    }
    isDownloadAvilabel.value = true
    ElMessage({ message: response.message || '语音生成成功', type: 'success' })
  } catch (error: unknown) {
    isDownloadAvilabel.value = false
    ElMessage({ message: error instanceof Error ? error.message : '语音生成失败', type: 'error' })
  } finally {
    isGeneratingVoice.value = false
  }
}

const getServerFileName = async () => {
  try {
    const response = await fetch(audio_url.value, { method: 'HEAD' })
    const disposition = response.headers.get('Content-Disposition')
    const fileNameMatch = disposition?.match(/filename=\"?(.+?)\"?$/)
    return fileNameMatch ? fileNameMatch[1] : null
  } catch {
    return null
  }
}

const handleDownloadBtn = async () => {
  if (!canDownload.value) {
    ElMessage({ message: '请先生成语音后再下载', type: 'warning' })
    return
  }

  const serverName = await getServerFileName()
  const fallbackName =
    latestVoiceUrl.value.split('/').pop()?.split('?')[0] ||
    audio_url.value.split('/').pop()?.split('?')[0] ||
    'generated.wav'
  const newTab = window.open(audio_url.value, '_blank')

  setTimeout(() => {
    if (!newTab || newTab.closed || newTab.document.readyState === 'complete') {
      const link = document.createElement('a')
      link.href = audio_url.value
      link.download = serverName || fallbackName
      link.click()
    }
  }, 1000)
}

const querySearch = (queryString: string, cb: (results: SearchSuggestion[]) => void) => {
  const normalizedQuery = queryString.trim().toLowerCase()
  const results = searchSuggestions.value.filter((item) => {
    if (!normalizedQuery) return true
    const haystack = [item.value, item.englishName, item.ipName, item.metaText, item.category, ...item.keywords]
      .join(' ')
      .toLowerCase()
    return haystack.includes(normalizedQuery)
  })

  cb(results.slice(0, 8))
}

const handleSelect = async (item: SearchSuggestion) => {
  searchQuery.value = item.value

  if (item.characterName) {
    await router.replace({ path: workshopRoute.value, query: { character: item.characterName } })
    await applySelectedCharacterByName(item.characterName)
    return
  }

  await router.replace({ path: workshopRoute.value })
}

onBeforeMount(async () => {
  try {
    const response = await getIpCharactersApi(props.belong)
    charactersData.value = response.characters || []
    await restoreSelectedCharacter()
  } catch (error: unknown) {
    charactersData.value = []
    await restoreSelectedCharacter()
    ElMessage({ message: error instanceof Error ? error.message : '角色清单加载失败', type: 'error' })
  }
})

watch(
  () => route.query.character,
  async () => {
    if (!characterCards.value.length) return
    const routeCharacterName = getRouteCharacterName()
    if (!routeCharacterName) return
    await applySelectedCharacterByName(routeCharacterName)
  },
)
</script>

<style scoped>
.voice-workshop {
  position: relative;
  min-height: calc(100vh - 80px);
  padding: 1rem clamp(0.9rem, 2vw, 1.8rem) 1.3rem;
  color: #17313e;
  background: var(--workshop-background);
  overflow: hidden;
}

.atmosphere-layer {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: var(--workshop-ambient);
}

.ambient-orb,
.ambient-grid,
.ambient-particles {
  position: absolute;
}

.ambient-orb {
  width: 26rem;
  height: 26rem;
  border-radius: 50%;
  filter: blur(24px);
  opacity: 0.8;
}

.ambient-orb-left {
  top: -8rem;
  left: -8rem;
  background: radial-gradient(circle, color-mix(in srgb, var(--workshop-primary) 24%, transparent), transparent 72%);
}

.ambient-orb-right {
  right: -10rem;
  bottom: -12rem;
  background: radial-gradient(circle, color-mix(in srgb, var(--workshop-secondary) 24%, transparent), transparent 72%);
}

.ambient-grid {
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.22) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.16) 1px, transparent 1px);
  background-size: 140px 140px;
  opacity: 0.1;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.32), transparent 78%);
}

.ambient-particles {
  inset: 0;
  background-image:
    radial-gradient(circle at 16% 26%, rgba(255, 255, 255, 0.82) 0 2px, transparent 2px),
    radial-gradient(circle at 76% 18%, rgba(255, 255, 255, 0.62) 0 1.5px, transparent 1.5px),
    radial-gradient(circle at 62% 68%, rgba(255, 255, 255, 0.42) 0 2px, transparent 2px),
    radial-gradient(circle at 28% 78%, rgba(255, 255, 255, 0.45) 0 1.5px, transparent 1.5px);
  opacity: 0.55;
}

.workshop-frame {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 0.9rem;
  min-height: calc(100vh - 80px - 2.3rem);
}

.workshop-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.workshop-search {
  width: min(100%, 38rem);
}

.workshop-search :deep(.el-input__wrapper) {
  min-height: 3.6rem;
  padding: 0 1.15rem;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.72);
  background:
    linear-gradient(160deg, rgba(255, 255, 255, 0.92), rgba(248, 252, 255, 0.76));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.86),
    0 18px 34px rgba(89, 114, 131, 0.14);
}

.workshop-search :deep(.el-input__wrapper.is-focus) {
  box-shadow:
    0 0 0 1px color-mix(in srgb, var(--workshop-primary) 44%, white),
    0 20px 38px color-mix(in srgb, var(--workshop-primary) 14%, rgba(89, 114, 131, 0.16));
}

.workshop-search :deep(.el-input__inner) {
  font-size: 1rem;
  color: #244252;
}

.search-prefix-icon {
  color: color-mix(in srgb, var(--workshop-primary) 70%, #456);
  font-size: 1.12rem;
}

.workshop-main {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(320px, 0.82fr);
  gap: 1rem;
}

.stage-column,
.control-column {
  min-height: 0;
}

.stage-column {
  display: grid;
  grid-template-rows: minmax(0, 1fr) auto;
  gap: 0.9rem;
}

.stage-shell,
.character-rail-shell,
.control-shell {
  border: 1px solid rgba(255, 255, 255, 0.62);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.56);
  backdrop-filter: blur(22px);
  box-shadow: 0 28px 55px rgba(86, 116, 130, 0.12);
}

.stage-shell {
  position: relative;
  overflow: hidden;
  min-height: 0;
  padding: 0.9rem;
}

.stage-shell::before {
  content: '';
  position: absolute;
  inset: 1rem;
  border-radius: 24px;
  background:
    radial-gradient(circle at 50% 18%, color-mix(in srgb, var(--workshop-primary) 26%, transparent), transparent 34%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(241, 247, 251, 0.46));
}

.stage-canvas {
  position: relative;
  height: 100%;
  min-height: clamp(25rem, 62vh, 42rem);
  border-radius: 24px;
  overflow: hidden;
  isolation: isolate;
}

.stage-character-card,
.stage-empty-card {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.stage-character-glow {
  position: absolute;
  left: 50%;
  bottom: 8%;
  width: 58%;
  height: 16%;
  transform: translateX(-50%);
  border-radius: 999px;
  background: radial-gradient(circle, color-mix(in srgb, var(--workshop-primary) 36%, white), transparent 72%);
  filter: blur(28px);
  opacity: 0.72;
}

.stage-character-image {
  position: relative;
  z-index: 1;
  max-height: 94%;
  max-width: 88%;
  object-fit: contain;
  transform-origin: center bottom;
  filter: drop-shadow(0 28px 42px rgba(45, 66, 81, 0.18));
  transition: transform 0.22s ease;
  will-change: transform;
}

.stage-empty-card {
  flex-direction: column;
  justify-content: center;
  gap: 0.8rem;
  color: #6b8693;
  text-align: center;
}

.stage-empty-icon {
  font-size: 2rem;
}

.character-rail-shell {
  position: relative;
  padding: 0.95rem 0.95rem 1.05rem;
  overflow: hidden;
  min-height: 7.5rem;
}

.character-rail-shell::before,
.character-rail-shell::after {
  content: '';
  position: absolute;
  top: 0.85rem;
  bottom: 0.85rem;
  width: 3.8rem;
  z-index: 2;
  pointer-events: none;
}

.character-rail-shell::before {
  left: 0;
  background: linear-gradient(90deg, rgba(245, 250, 252, 0.92), rgba(245, 250, 252, 0));
}

.character-rail-shell::after {
  right: 0;
  background: linear-gradient(270deg, rgba(245, 250, 252, 0.92), rgba(245, 250, 252, 0));
}

.character-swiper {
  width: 100%;
  overflow: visible;
}

.character-slide {
  width: 176px;
}

.character-card {
  position: relative;
  width: 100%;
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr);
  align-items: center;
  gap: 0.8rem;
  min-height: 5.1rem;
  padding: 0.82rem 0.92rem;
  border: 1px solid rgba(255, 255, 255, 0.76);
  border-radius: 24px;
  background:
    linear-gradient(160deg, rgba(255, 255, 255, 0.92), rgba(246, 250, 252, 0.76));
  color: #274452;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.82),
    0 12px 26px rgba(71, 97, 113, 0.08);
  transition:
    transform 0.22s ease,
    border-color 0.22s ease,
    box-shadow 0.22s ease,
    background 0.22s ease;
  overflow: hidden;
}

.character-card-glow {
  position: absolute;
  inset: auto auto -24px 50%;
  width: 90px;
  height: 44px;
  transform: translateX(-50%);
  background: radial-gradient(circle, color-mix(in srgb, var(--workshop-primary) 22%, transparent), transparent 72%);
  filter: blur(14px);
  opacity: 0;
  transition: opacity 0.22s ease;
}

.character-card:hover,
.character-card.active {
  transform: translateY(-3px);
  border-color: color-mix(in srgb, var(--workshop-primary) 48%, white);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.92),
    0 18px 34px rgba(71, 97, 113, 0.14);
}

.character-card.active {
  background:
    linear-gradient(
      145deg,
      color-mix(in srgb, var(--workshop-primary-soft) 38%, white),
      rgba(255, 255, 255, 0.9)
    );
}

.character-card.active .character-card-glow {
  opacity: 1;
}

.character-card-avatar {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  object-fit: cover;
  box-shadow: 0 10px 18px rgba(59, 88, 104, 0.18);
}

.character-card-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.18rem;
  text-align: left;
}

.character-card-copy strong,
.character-card-copy small {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.character-card-copy strong {
  font-size: 0.95rem;
  font-weight: 700;
}

.character-card-copy small {
  color: #75909d;
  font-size: 0.76rem;
}

.control-shell {
  height: 100%;
  display: flex;
  flex-direction: column;
  min-height: 0;
  padding: 1rem;
  gap: 0.85rem;
}

.character-summary {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 0.8rem;
  min-height: 4.6rem;
}

.summary-avatar-wrap {
  width: 3.4rem;
  height: 3.4rem;
}

.summary-avatar {
  width: 100%;
  height: 100%;
  border-radius: 18px;
  object-fit: cover;
  box-shadow: 0 14px 26px rgba(70, 96, 111, 0.16);
}

.summary-avatar.empty {
  width: 100%;
  height: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  color: #6d8693;
}

.summary-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.16rem;
}

.summary-copy strong,
.summary-copy span {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.summary-copy strong {
  font-size: 1.02rem;
  font-weight: 700;
  color: #173746;
}

.summary-copy span {
  color: #718b98;
  font-size: 0.83rem;
}

.summary-tags {
  display: flex;
  gap: 0.45rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.summary-tag,
.summary-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 2rem;
  padding: 0.4rem 0.82rem;
  border-radius: 999px;
  border: 1px solid color-mix(in srgb, var(--workshop-primary) 42%, white);
  background: color-mix(in srgb, var(--workshop-primary-soft) 68%, white);
  color: color-mix(in srgb, var(--workshop-primary) 68%, #25414f);
  font-size: 0.76rem;
  font-weight: 700;
}

.voice-textarea {
  flex: 0 0 auto;
}

.voice-textarea :deep(.el-textarea__inner) {
  min-height: 13.8rem;
  padding: 1rem 1rem 2.4rem;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.66);
  background: rgba(255, 255, 255, 0.8);
  color: #183542;
  line-height: 1.75;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.45);
}

.voice-textarea :deep(.el-input__count) {
  bottom: 0.8rem;
  right: 1rem;
  color: #7993a0;
}

.action-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 0.65rem;
}

.generate-action,
.download-action {
  min-height: 3rem;
  border-radius: 18px;
  font-weight: 700;
}

.generate-action {
  border: none;
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--workshop-primary) 82%, white),
    color-mix(in srgb, var(--workshop-secondary) 68%, white)
  );
  box-shadow: 0 18px 28px color-mix(in srgb, var(--workshop-primary) 26%, transparent);
}

.generate-action.generating {
  animation: generatingPulse 1.3s ease-in-out infinite;
}

.download-action {
  width: 3.5rem;
  padding: 0;
  border: 1px solid color-mix(in srgb, var(--workshop-primary) 24%, white);
  background:
    linear-gradient(
      145deg,
      color-mix(in srgb, var(--workshop-primary-soft) 32%, white),
      rgba(255, 255, 255, 0.82)
    );
  color: color-mix(in srgb, var(--workshop-primary) 76%, #2e4a58);
  box-shadow: 0 14px 24px color-mix(in srgb, var(--workshop-primary) 12%, transparent);
}

.download-action :deep(svg) {
  font-size: 1.22rem;
}

.audio-shell {
  display: flex;
  align-items: center;
  min-height: 5.2rem;
  padding: 0.85rem 0.95rem;
  border: 1px solid color-mix(in srgb, var(--workshop-primary) 18%, rgba(255, 255, 255, 0.82));
  border-radius: 24px;
  background:
    linear-gradient(
      160deg,
      color-mix(in srgb, var(--workshop-primary-soft) 34%, white),
      rgba(255, 255, 255, 0.74)
    );
}

.audio-shell.ready {
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.78),
    0 18px 30px color-mix(in srgb, var(--workshop-primary) 14%, transparent);
}

.audio-player {
  display: none;
}

.audio-player-card {
  width: 100%;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: center;
  gap: 0.85rem;
}

.audio-play-button {
  width: 3.4rem;
  height: 3.4rem;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 20px;
  background:
    linear-gradient(
      135deg,
      color-mix(in srgb, var(--workshop-primary) 82%, white),
      color-mix(in srgb, var(--workshop-secondary) 72%, white)
    );
  color: white;
  box-shadow: 0 14px 24px color-mix(in srgb, var(--workshop-primary) 22%, transparent);
  transition: transform 0.2s ease;
}

.audio-play-button:hover {
  transform: translateY(-1px) scale(1.02);
}

.audio-play-button :deep(svg) {
  font-size: 1.5rem;
  filter: drop-shadow(0 1px 0 rgba(255, 255, 255, 0.2));
}

.audio-player-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.55rem;
}

.audio-player-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.8rem;
  color: #6d8693;
  font-size: 0.8rem;
}

.audio-player-meta strong {
  color: #20404f;
  font-size: 0.92rem;
  font-weight: 700;
}

.audio-progress {
  width: 100%;
  height: 0.42rem;
  margin: 0;
  appearance: none;
  border-radius: 999px;
  background: linear-gradient(
    90deg,
    color-mix(in srgb, var(--workshop-primary) 56%, white),
    color-mix(in srgb, var(--workshop-secondary) 44%, white)
  );
  outline: none;
}

.audio-progress::-webkit-slider-thumb {
  appearance: none;
  width: 0.92rem;
  height: 0.92rem;
  border: 2px solid white;
  border-radius: 50%;
  background: color-mix(in srgb, var(--workshop-primary) 74%, white);
  box-shadow: 0 4px 10px rgba(45, 66, 81, 0.2);
  cursor: pointer;
}

.audio-progress::-moz-range-thumb {
  width: 0.92rem;
  height: 0.92rem;
  border: 2px solid white;
  border-radius: 50%;
  background: color-mix(in srgb, var(--workshop-primary) 74%, white);
  box-shadow: 0 4px 10px rgba(45, 66, 81, 0.2);
  cursor: pointer;
}

.audio-placeholder {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 0.65rem;
  color: #6e8996;
  font-size: 0.9rem;
}

.audio-placeholder :deep(svg) {
  font-size: 1.2rem;
}

.agent-space {
  flex: 1 1 auto;
  min-height: clamp(6rem, 16vh, 10rem);
}

.stage-character-enter-active,
.stage-character-leave-active {
  transition:
    opacity 0.34s ease,
    transform 0.34s ease;
}

.stage-character-enter-from,
.stage-character-leave-to {
  opacity: 0;
  transform: translateX(18px) scale(0.96);
}

@keyframes generatingPulse {
  0%,
  100% {
    transform: translateY(0);
    box-shadow: 0 18px 28px color-mix(in srgb, var(--workshop-primary) 26%, transparent);
  }
  50% {
    transform: translateY(-1px);
    box-shadow: 0 22px 34px color-mix(in srgb, var(--workshop-primary) 34%, transparent);
  }
}

:global(.workshop-search-popper .el-autocomplete-suggestion__list) {
  padding: 0.45rem;
}

:global(.workshop-search-popper .el-autocomplete-suggestion li) {
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
  overflow: hidden;
  text-overflow: ellipsis;
}

.suggestion-title-english,
.suggestion-meta {
  color: #6f8997;
  font-size: 0.82rem;
}

.suggestion-meta {
  flex-shrink: 0;
}

.theme-starrail {
  color: #e7eff7;
}

.theme-starrail .stage-shell,
.theme-starrail .character-rail-shell,
.theme-starrail .control-shell {
  border-color: rgba(124, 146, 255, 0.26);
  background: rgba(15, 24, 40, 0.58);
  box-shadow: 0 28px 55px rgba(4, 9, 20, 0.28);
}

.theme-starrail .stage-shell::before {
  background:
    radial-gradient(circle at 50% 18%, color-mix(in srgb, var(--workshop-primary) 24%, transparent), transparent 34%),
    linear-gradient(180deg, rgba(17, 24, 38, 0.96), rgba(12, 19, 31, 0.74));
}

.theme-starrail .workshop-search :deep(.el-input__wrapper),
.theme-starrail .character-card,
.theme-starrail .summary-tag,
.theme-starrail .voice-textarea :deep(.el-textarea__inner),
.theme-starrail .audio-shell,
.theme-starrail .download-action {
  border-color: rgba(124, 146, 255, 0.24);
  background: rgba(17, 27, 44, 0.78);
  color: #dfebf4;
}

.theme-starrail .summary-copy strong,
.theme-starrail .suggestion-title,
.theme-starrail .character-card-copy strong,
.theme-starrail .audio-player-meta strong {
  color: #f3f8ff;
}

.theme-starrail .summary-copy span,
.theme-starrail .character-card-copy small,
.theme-starrail .suggestion-title-english,
.theme-starrail .suggestion-meta,
.theme-starrail .audio-placeholder,
.theme-starrail .audio-player-meta {
  color: #8ea7bb;
}

.theme-starrail .workshop-search :deep(.el-input__inner) {
  color: #ecf3fa;
}

.theme-starrail .character-rail-shell::before {
  background: linear-gradient(90deg, rgba(17, 27, 44, 0.94), rgba(17, 27, 44, 0));
}

.theme-starrail .character-rail-shell::after {
  background: linear-gradient(270deg, rgba(17, 27, 44, 0.94), rgba(17, 27, 44, 0));
}

.theme-starrail .audio-play-button {
  color: #f9fcff;
}

@media (max-width: 1200px) {
  .workshop-main {
    grid-template-columns: minmax(0, 1fr);
  }

  .control-column {
    min-height: auto;
  }

  .control-shell {
    min-height: 26rem;
  }
}

@media (max-width: 720px) {
  .voice-workshop {
    padding: 0.85rem 0.8rem 1rem;
  }

  .workshop-frame {
    min-height: auto;
  }

  .workshop-toolbar {
    width: 100%;
  }

  .stage-canvas {
    min-height: 22rem;
  }

  .character-slide {
    width: 152px;
  }

  .character-card {
    grid-template-columns: 46px minmax(0, 1fr);
    gap: 0.65rem;
    padding: 0.64rem 0.72rem;
  }

  .character-card-avatar {
    width: 46px;
    height: 46px;
  }

  .character-summary {
    grid-template-columns: auto minmax(0, 1fr);
  }

  .summary-tags {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }

  .voice-textarea :deep(.el-textarea__inner) {
    min-height: 11.5rem;
  }

  .agent-space {
    min-height: 4rem;
  }
}
</style>
