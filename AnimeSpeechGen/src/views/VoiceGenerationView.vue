<template>
  <div class="main-container">
    <el-row class="auto-complete-row">
      <div class="auto-complete-container">
        <el-autocomplete
          v-model="searchQuery"
          :fetch-suggestions="querySearch"
          placeholder="搜索"
          class="search-bar"
          prefix-icon="flat-color-icons:search"
          @select="handleSelect"
        >
          <template #prefix>
            <Icon icon="flat-color-icons:search" height="70%" />
          </template>
        </el-autocomplete>
      </div>
    </el-row>
    <el-row>
      <el-col :span="12">
        <div class="anime-stand-container">
          <div class="stand-iamge__lazy">
            <el-image
              v-if="chooseCharacter.url"
              :key="chooseCharacter.name"
              :src="chooseCharacter.url"
              fit="scale-down"
              lazy
              class="main-stand-image"
            />
            <el-empty
              v-else
              :description="emptyStateText"
              class="empty-stand"
            />

            <el-button
              size="large"
              class="overlay-button left-btn"
              type="primary"
              :icon="ArrowLeftBold"
              :disabled="!canSwitchCharacter"
              @click="handleLeftClick"
            />

            <el-button
              size="large"
              class="overlay-button right-btn"
              type="primary"
              :icon="ArrowRightBold"
              :disabled="!canSwitchCharacter"
              @click="handleRightClick"
            />
          </div>
        </div>
      </el-col>
      <el-col :span="8">
        <div class="operation-container">
          <div class="text-input-container">
            <el-input
              v-model="textarea"
              style="width: 100%"
              :rows="10"
              type="textarea"
              placeholder="请输入文本，仅支持中文"
              maxlength="100"
              show-word-limit
            />
          </div>
          <div class="btn-container">
            <a-button
              class="generate-btn"
              type="primary"
              :loading="isGeneratingVoice"
              @click="handleGenerateBtn"
            >
              生成
            </a-button>
          </div>
          <div class="audio-container">
            <audio
              ref="audioPlayer"
              controls
              style="width: 100%; display: flex; justify-content: center"
            >
              <source :src="audio_url" />
            </audio>
          </div>
          <div class="characters-container" @wheel.prevent="handleCharacterWheel">
            <el-scrollbar ref="scrollbarRef">
              <div class="scrollbar-flex-content">
                <el-button
                  v-for="(avator, index) in avatorUrls"
                  :key="`${belong}-${index}`"
                  class="scrollbar-character-item"
                  @click="handleAvatorClick(index)"
                >
                  <el-image
                    :src="avator"
                    alt="character-icon"
                    class="character-image"
                    style="height: 100%"
                  />
                </el-button>
              </div>
            </el-scrollbar>
          </div>
        </div>
      </el-col>
      <el-col :span="2"> </el-col>
    </el-row>
  </div>
</template>

<script lang="ts" setup>
import { computed, nextTick, onBeforeMount, ref, watch } from 'vue'
import { getGeneratedVoiceApi, getStaticsUrlApi } from '@/api'
import { Icon } from '@iconify/vue'
import { ElMessage } from 'element-plus'
import { ArrowLeftBold, ArrowRightBold } from '@element-plus/icons-vue'
import type { ElScrollbar } from 'element-plus'

type CharacterState = {
  name: string
  url: string
  avator: string
  index: number
}

type ViewProps = {
  belong: string
  characterNameAliasMap?: Record<string, string>
}

const props = withDefaults(defineProps<ViewProps>(), {
  characterNameAliasMap: () => ({}),
})

const searchQuery = ref('')
const chooseCharacter = ref<CharacterState>({ name: '', url: '', avator: '', index: 0 })
const latestVoiceUrl = ref('')
const audio_url = ref('')
const audioPlayer = ref<HTMLAudioElement | null>(null)
const isGeneratingVoice = ref(false)
const isDownloadAvilabel = ref(true)
const scrollbarRef = ref<InstanceType<typeof ElScrollbar> | null>(null)
const apiOrigin = (import.meta.env.VITE_API_ORIGIN as string | undefined)?.replace(/\/$/, '')

const belong = computed(() => props.belong)
const nameKey = computed(() => `${props.belong}-Names`)
const avatorKey = computed(() => `${props.belong}-Avators`)
const standsKey = computed(() => `${props.belong}-Stands`)
const textareaKey = computed(() => `${props.belong}-Textarea`)
const selectedCharacterKey = computed(() => `${props.belong}-SelectedCharacter`)
const emptyStateText = computed(() => `${props.belong} 当前还没有可用角色资源`)
const canSwitchCharacter = computed(() => names.value.length > 1)

const textarea = ref(localStorage.getItem(textareaKey.value) || '')

watch(textarea, (value) => {
  localStorage.setItem(textareaKey.value, value || '')
})

watch(
  () => chooseCharacter.value.name,
  (value) => {
    if (value) {
      localStorage.setItem(selectedCharacterKey.value, value)
    }
  },
)

/**
 * 将前端展示名归一化为后端使用的标准角色键名。
 * @param name 页面展示、缓存或静态资源中出现的角色名称。
 */
const normalizeCharacterName = (name: string) => {
  const normalizedName = name.trim()
  if (!normalizedName) return normalizedName
  return props.characterNameAliasMap[normalizedName] || normalizedName
}

/**
 * 从本地缓存中读取当前 IP 的角色名称列表。
 * @returns 已归一化的角色名称数组。
 */
const getCharacterNamesFromLocalStorage = () => {
  return (localStorage.getItem(nameKey.value)?.split(',') || []).map(normalizeCharacterName)
}

/**
 * 从本地缓存中读取当前 IP 的立绘地址列表。
 * @returns 立绘 URL 数组。
 */
const getImageUrlsFromLocalStorage = () => {
  return localStorage.getItem(standsKey.value)?.split(',') || []
}

/**
 * 从本地缓存中读取当前 IP 的头像地址列表。
 * @returns 头像 URL 数组。
 */
const getCharacterAvatorsFromLocalStorage = () => {
  return localStorage.getItem(avatorKey.value)?.split(',') || []
}

/**
 * 清理当前 IP 对应的角色静态资源缓存。
 */
const clearImageCache = () => {
  localStorage.removeItem(nameKey.value)
  localStorage.removeItem(standsKey.value)
  localStorage.removeItem(avatorKey.value)
}

/**
 * 判断本地缓存中的资源地址是否仍然指向当前 API 源。
 * @returns 如果检测到旧主机缓存则返回 true。
 */
const hasStaleImageCache = () => {
  const cachedStandUrls = getImageUrlsFromLocalStorage()
  const cachedAvatorUrls = getCharacterAvatorsFromLocalStorage()
  const cachedUrls = [...cachedStandUrls, ...cachedAvatorUrls].filter(Boolean)

  if (cachedUrls.length === 0 || !apiOrigin) {
    return false
  }

  return cachedUrls.some((url) => !url.startsWith(apiOrigin))
}

if (hasStaleImageCache()) {
  clearImageCache()
}

const names = ref<string[]>(getCharacterNamesFromLocalStorage())
const standUrls = ref<string[]>(getImageUrlsFromLocalStorage())
const avatorUrls = ref<string[]>(getCharacterAvatorsFromLocalStorage())

/**
 * 将角色头像列表滚动到指定角色所在位置，并尽量让其显示在中间。
 * @param index 当前角色在头像列表中的索引。
 */
const centerCharacterInScroller = async (index: number) => {
  await nextTick()

  if (!scrollbarRef.value) return

  const scrollContainer = scrollbarRef.value.$el.querySelector('.el-scrollbar__wrap') as HTMLElement | null
  if (!scrollContainer) return

  const buttons = scrollContainer.querySelectorAll('.scrollbar-character-item')
  if (buttons.length <= index) return

  const targetButton = buttons[index] as HTMLElement
  const containerWidth = scrollContainer.clientWidth
  const buttonWidth = targetButton.offsetWidth
  const buttonOffset = targetButton.offsetLeft
  const scrollPosition = Math.max(buttonOffset - containerWidth / 2 + buttonWidth / 2, 0)

  scrollContainer.scrollTo({
    left: scrollPosition,
    behavior: 'smooth',
  })
}

/**
 * 按索引切换当前选中的角色，并同步立绘、头像和滚动条位置。
 * @param index 角色在 names / standUrls / avatorUrls 中的统一索引。
 */
const applySelectedCharacterByIndex = async (index: number) => {
  if (
    index < 0 ||
    index >= names.value.length ||
    index >= standUrls.value.length ||
    index >= avatorUrls.value.length
  ) {
    return
  }

  chooseCharacter.value = {
    index,
    name: names.value[index],
    url: standUrls.value[index],
    avator: avatorUrls.value[index],
  }
  await centerCharacterInScroller(index)
}

/**
 * 从本地缓存中读取上次选中的角色名。
 * @returns 归一化后的角色键名。
 */
const getSavedCharacterName = () => {
  return normalizeCharacterName(localStorage.getItem(selectedCharacterKey.value) || '')
}

/**
 * 恢复刷新前最后一次选中的角色；如果没有缓存，则回退为随机角色。
 */
const restoreSelectedCharacter = async () => {
  if (names.value.length === 0 || standUrls.value.length === 0 || avatorUrls.value.length === 0) {
    chooseCharacter.value = { name: '', url: '', avator: '', index: 0 }
    return
  }

  const savedCharacterName = getSavedCharacterName()
  const savedCharacterIndex = names.value.findIndex((name) => name === savedCharacterName)

  if (savedCharacterIndex >= 0) {
    await applySelectedCharacterByIndex(savedCharacterIndex)
    return
  }

  const randomKey = Math.floor(Math.random() * names.value.length)
  await applySelectedCharacterByIndex(randomKey)
}

/**
 * 拉取当前 IP 的静态资源列表，并更新本地缓存。
 */
const fetchImageUrls = async () => {
  const response = await getStaticsUrlApi(props.belong)

  if (!response.names) {
    names.value = []
    standUrls.value = []
    avatorUrls.value = []
    clearImageCache()
    return
  }

  const normalizedNames = response.names.map(normalizeCharacterName)
  localStorage.setItem(nameKey.value, normalizedNames.join(','))
  localStorage.setItem(standsKey.value, response.stands.join(','))
  localStorage.setItem(avatorKey.value, response.avators.join(','))
  names.value = normalizedNames
  standUrls.value = response.stands
  avatorUrls.value = response.avators
}

/**
 * 向后端提交文本和角色信息，请求生成语音。
 */
const handleGenerateBtn = async () => {
  if (!chooseCharacter.value.name) {
    ElMessage({
      message: `当前 ${props.belong} 还没有可生成的角色`,
      type: 'warning',
    })
    return
  }

  if (!textarea.value) {
    ElMessage({
      message: 'please input text.',
      type: 'warning',
    })
    return
  }

  isGeneratingVoice.value = true
  try {
    const response = await getGeneratedVoiceApi(
      textarea.value,
      chooseCharacter.value.name,
      props.belong,
      'zh',
    )

    latestVoiceUrl.value = response.audio_url
    audio_url.value = response.audio_url
    if (audioPlayer.value) {
      audioPlayer.value.src = audio_url.value
    }
    isDownloadAvilabel.value = true
    ElMessage({
      message: response.message || '语音生成成功',
      type: 'success',
    })
  } catch (error: unknown) {
    isDownloadAvilabel.value = false
    ElMessage({
      message: error instanceof Error ? error.message : '语音生成失败',
      type: 'error',
    })
  } finally {
    isGeneratingVoice.value = false
  }
}

/**
 * 读取当前音频资源的文件名，用于下载时优先沿用服务端命名。
 * @returns 服务端文件名；如果无法解析则返回 null。
 */
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

/**
 * 下载当前已经生成完成的语音文件。
 */
const handleDownloadBtn = async () => {
  if (!isDownloadAvilabel.value || !audio_url.value) {
    ElMessage({
      message: 'please generate a voice after downloading.',
      type: 'warning',
    })
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

/**
 * 切换到左侧相邻角色。
 */
const handleLeftClick = () => {
  const currIndex = chooseCharacter.value.index
  if (currIndex > 0 && currIndex - 1 < avatorUrls.value.length) {
    applySelectedCharacterByIndex(currIndex - 1)
  }
}

/**
 * 切换到右侧相邻角色。
 */
const handleRightClick = () => {
  const currIndex = chooseCharacter.value.index
  if (currIndex < names.value.length - 1 && currIndex + 1 < avatorUrls.value.length) {
    applySelectedCharacterByIndex(currIndex + 1)
  }
}

/**
 * 处理头像点击切换逻辑。
 * @param index 被点击角色在头像列表中的索引。
 */
const handleAvatorClick = (index: number) => {
  if (index >= 0 && index < names.value.length && index !== chooseCharacter.value.index) {
    applySelectedCharacterByIndex(index)
  }
}

/**
 * 将鼠标滚轮的纵向滚动转换为角色头像列表的横向滚动。
 * @param event 鼠标滚轮事件，优先使用 deltaY 作为横向滚动量。
 */
const handleCharacterWheel = (event: WheelEvent) => {
  if (!scrollbarRef.value) return

  const scrollContainer = scrollbarRef.value.$el.querySelector('.el-scrollbar__wrap') as HTMLElement | null
  if (!scrollContainer) return

  const scrollDelta = Math.abs(event.deltaY) > Math.abs(event.deltaX) ? event.deltaY : event.deltaX
  scrollContainer.scrollLeft += scrollDelta
}

onBeforeMount(async () => {
  if (!names.value.length) {
    await fetchImageUrls()
  }
  await restoreSelectedCharacter()
})

/**
 * 根据搜索词过滤角色名称，并返回给自动完成组件。
 * @param queryString 当前输入框中的查询字符串。
 * @param cb Element Plus 自动完成组件的结果回调。
 */
const querySearch = (queryString: string, cb: (results: Array<{ value: string }>) => void) => {
  const normalizedQuery = queryString.trim().toLowerCase()
  const results = names.value
    .filter((name) => name.toLowerCase().includes(normalizedQuery))
    .map((name) => ({
      value: name,
    }))

  cb(results)
}

/**
 * 处理自动完成面板中的搜索结果点击事件。
 * @param item 当前被选中的搜索项。
 */
const handleSelect = (item: { value: string }) => {
  const selectedName = normalizeCharacterName(item.value)
  const index = names.value.findIndex((name) => name === selectedName)
  if (index >= 0) {
    applySelectedCharacterByIndex(index)
  }
}
</script>

<style scoped>
.auto-complete-row {
  height: 20%;
}

.auto-complete-container {
  width: 100%;
  height: 100%;
}

.operation-container {
  margin-top: 18%;
  margin-right: 5%;
}

.stand-iamge__lazy {
  max-height: 900px;
  margin-left: 10%;
  position: relative;
  display: inline-block;
}

.main-stand-image {
  display: block;
}

.stand-iamge__lazy .el-image {
  display: block;
  min-height: 200px;
  margin-bottom: 10px;
}

.empty-stand {
  min-height: 420px;
  width: min(100%, 720px);
  display: flex;
  align-items: center;
  justify-content: center;
}

.overlay-button {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 10;
}

::v-deep(.overlay-button) {
  border: 0 !important;
  background-color: transparent !important;
  padding: 0 !important;
  min-width: auto !important;

  &:active {
    transform: none;
  }

  .el-icon {
    color: #409eff;
    font-size: 36px;
  }
}

.left-btn {
  left: 12%;
}

.right-btn {
  right: 12%;
}

.overlay-button:hover {
  transform: translateY(-50%) scale(1.1);
  transition: transform 0.2s;
}

.audio-container {
  width: 100%;
  margin-top: 40px;
}

.btn-container {
  margin-top: 5%;
  display: flex;
  justify-content: space-between;
  min-height: 40px;
}

.generate-btn {
  width: 100%;
  min-height: 40px;
}

.download-btn {
  width: 45%;
  min-height: 40px;
}

::v-deep(.el-image__inner) {
  height: 90%;
  max-height: 900px;
  display: flex;
  justify-content: center;
  align-items: center;
  justify-self: center;
  align-self: center;
  margin: auto 0;
  width: 90%;
}

::v-deep(.el-autocomplete) {
  width: 70%;
  display: flex;
  justify-self: center;
  justify-content: center;
  padding-top: 5%;
  padding-bottom: 5%;
  align-items: center;
}

::v-deep(.el-input) {
  width: 100%;
  height: 4rem;
  border-radius: 1.5rem;
  border: 1px solid #dcdfe6;
  padding: 0.5rem;
}

::v-deep(.el-input__inner) {
  height: 100%;
}

::v-deep(.el-input__wrapper) {
  box-shadow: 0 0 0 0;
  margin-top: 5%;
}

.anime-stand-container {
  display: flex;
  width: 100%;
  height: 100%;
}

.main-container {
  width: 100%;
  height: 100%;
}

.scrollbar-flex-content {
  display: flex;
}

.scrollbar-character-item {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100px;
  height: 100px;
  margin-top: 3%;
  text-align: center;
  border: #ffffff;
}

::v-deep(.el-scrollbar__wrap) {
  margin-top: 3%;
}
</style>
