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
              :key="chooseCharacter.name"
              :src="chooseCharacter.url"
              fit="scale-down"
              lazy
              class="main-stand-image"
            />

            <!-- 左侧按钮 -->
            <el-button
              size="large"
              class="overlay-button left-btn"
              type="primary"
              :icon="ArrowLeftBold"
              @click="handleLeftClick"
            />

            <!-- 右侧按钮 -->
            <el-button
              size="large"
              class="overlay-button right-btn"
              type="primary"
              :icon="ArrowRightBold"
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
              >生成
            </a-button>
            <!-- <el-button
              class="generate-btn"
              v-loading="isGeneratingVoice"
              @click="handleGenerateBtn"
              type="primary"
              >生成</el-button
            > -->
            <!-- <el-button class="download-btn" @click="handleDownloadBtn" type="primary"
              >下载</el-button
            > -->
          </div>
          <div class="audio-container">
            <!-- <mini-audio :audio-source="audio_url"></mini-audio> -->
            <audio
              ref="audioPlayer"
              controls
              style="width: 100%; display: flex; justify-content: center"
            >
              <source :src="audio_url" />
            </audio>
          </div>
          <div class="characters-container">
            <el-scrollbar ref="scrollbarRef">
              <div class="scrollbar-flex-content">
                <el-button
                  v-for="(avator, index) in avatorUrls"
                  :key="index"
                  class="scrollbar-character-item"
                  @click="handleAvatorClick(index)"
                >
                  <!-- {{ character }} -->
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
import { nextTick, ref, onBeforeMount, watch } from 'vue'
import { getStaticsUrlApi, getGeneratedVoiceApi } from '@/api'
import { Icon } from '@iconify/vue'
import { ElMessage } from 'element-plus'
import { ArrowLeftBold, ArrowRightBold } from '@element-plus/icons-vue'
import type { ElScrollbar } from 'element-plus'
import type { BelongStaticsResponseData } from '@/util/types'

type CharacterState = {
  name: string
  url: string
  avator: string
  index: number
}

const characterNameAliasMap: Record<string, string> = {
  'Kamizato Ayaka': 'Ayaka',
  'Kamisato Ayaka': 'Ayaka',
  'Yae Miko': 'YaeMiko',
}

/**
 * 将前端展示名归一化为后端使用的标准角色键名。
 * @param name 页面展示、缓存或静态资源中出现的角色名称。
 */
const normalizeCharacterName = (name: string) => {
  const normalizedName = name.trim()
  if (!normalizedName) return normalizedName
  return characterNameAliasMap[normalizedName] || normalizedName
}

const belong = 'GenShin'
const nameKey = belong + '-Names'
const avatorKey = belong + '-Avators'
const standsKey = belong + '-Stands'
const textareaKey = belong + '-Textarea'
const selectedCharacterKey = belong + '-SelectedCharacter'
const apiOrigin = (import.meta.env.VITE_API_ORIGIN as string | undefined)?.replace(/\/$/, '')
const searchQuery = ref('')
const chooseCharacter = ref<CharacterState>({ name: '', url: '', avator: '', index: 0 })
const textarea = ref(localStorage.getItem(textareaKey) || '')
const isDownloadAvilabel = ref(true)
const latestVoiceUrl = ref('')
const audio_url = ref('')
const audioPlayer = ref<HTMLAudioElement | null>(null) // 音频组件 ref
const isGeneratingVoice = ref(false)

watch(textarea, (value) => {
  localStorage.setItem(textareaKey, value || '')
})

watch(
  () => chooseCharacter.value.name,
  (value) => {
    if (value) {
      localStorage.setItem(selectedCharacterKey, value)
    }
  },
)

// 定义滚动条引用
const scrollbarRef = ref<InstanceType<typeof ElScrollbar> | null>(null)

const getCharacterNamesFromLovalStorage = () => {
  return (localStorage.getItem(nameKey)?.split(',') || []).map(normalizeCharacterName)
}

const getImageUrlsFromLocalStorage = () => {
  return localStorage.getItem(standsKey)?.split(',') || []
}

const getCharacterAvatorsFromLocalStorage = () => {
  return localStorage.getItem(avatorKey)?.split(',') || []
}

const clearImageCache = () => {
  localStorage.removeItem(nameKey)
  localStorage.removeItem(standsKey)
  localStorage.removeItem(avatorKey)
}

const hasStaleImageCache = () => {
  const cachedStandUrls = getImageUrlsFromLocalStorage()
  const cachedAvatorUrls = getCharacterAvatorsFromLocalStorage()
  const cachedUrls = [...(cachedStandUrls || []), ...(cachedAvatorUrls || [])].filter(Boolean)

  if (cachedUrls.length === 0 || !apiOrigin) {
    return false
  }

  return cachedUrls.some((url) => !url.startsWith(apiOrigin))
}

if (hasStaleImageCache()) {
  clearImageCache()
}

const names = ref<string[]>(getCharacterNamesFromLovalStorage())
const standUrls = ref<string[]>(getImageUrlsFromLocalStorage())
const avatorUrls = ref<string[]>(getCharacterAvatorsFromLocalStorage())
// var names = ref()
// var standUrls = ref() // {}
// var avatorUrls = ref()
console.log(names.value)
// console.log(standUrls.value)

/**
 * 将角色头像列表滚动到指定角色所在位置，并尽量让其显示在中间。
 * @param index 当前角色在头像列表中的索引。
 */
const centerCharacterInScroller = async (index: number) => {
  await nextTick()

  if (!scrollbarRef.value) return

  const scrollContainer = scrollbarRef.value.$el.querySelector('.el-scrollbar__wrap')
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

  chooseCharacter.value.index = index
  chooseCharacter.value.name = names.value[index]
  chooseCharacter.value.url = standUrls.value[index]
  chooseCharacter.value.avator = avatorUrls.value[index]
  await centerCharacterInScroller(index)
}

/**
 * 从本地缓存中读取上次选中的角色名。
 * @returns 归一化后的角色键名。
 */
const getSavedCharacterName = () => {
  return normalizeCharacterName(localStorage.getItem(selectedCharacterKey) || '')
}

/**
 * 恢复刷新前最后一次选中的角色；如果没有缓存，则回退为随机角色。
 */
const restoreSelectedCharacter = async () => {
  if (names.value.length === 0 || standUrls.value.length === 0 || avatorUrls.value.length === 0) {
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

// 从后端请求图片 URLs 并存储到 localStorage
/**
 * 拉取当前 IP 的静态资源列表，并更新本地缓存。
 */
const fetchImageUrls = async () => {
  await getStaticsUrlApi(belong)
    .then((response: BelongStaticsResponseData) => {
      if (response.names) {
        const normalizedNames = response.names.map(normalizeCharacterName)
        // 存储获取到的图片 URLs 到 localStorage
        localStorage.setItem(nameKey, normalizedNames.join(','))
        localStorage.setItem(standsKey, response.stands.join(','))
        localStorage.setItem(avatorKey, response.avators.join(','))
        names.value = normalizedNames
        standUrls.value = response.stands
        avatorUrls.value = response.avators
        console.log(names.value)
      }
    })
    .catch((error) => {
      console.error(error.message)
      throw error
    })
}

/**
 * 向后端提交文本和角色信息，请求生成语音。
 */
const handleGenerateBtn = async () => {
  if (!textarea || textarea.value == '') {
    ElMessage({
      message: 'please input text.',
      type: 'warning',
    })
    return
  }
  isGeneratingVoice.value = true
  try {
    console.log(`current chosen character: ${chooseCharacter.value['name']}, belong ${belong}`)
    const response = await getGeneratedVoiceApi(
      textarea.value,
      chooseCharacter.value.name,
      belong,
      'zh',
    )
    console.log(response)
    ElMessage({
      message: response.message || '语音生成成功',
      type: 'success',
    })
      audio_url.value = response.audio_url
      if (audioPlayer.value) {
        audioPlayer.value.src = audio_url.value
      }
      isDownloadAvilabel.value = true
  } catch (error: unknown) {
    isDownloadAvilabel.value = false
    console.log(error instanceof Error ? error.message : error)
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
 */
const getServerFileName = async () => {
  try {
    const response = await fetch(audio_url.value, { method: 'HEAD' })
    const disposition = response.headers.get('Content-Disposition')

    // 从header解析：Content-Disposition: attachment; filename="sample.wav"
    const fileNameMatch = disposition?.match(/filename="?(.+?)"?$/)
    return fileNameMatch ? fileNameMatch[1] : null
  } catch (e) {
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
  // 优先获取服务器指定的文件名
  const serverName = await getServerFileName()
  // 备选方案：从URL提取
  const fallbackName = audio_url.value.split('/').pop()?.split('?')[0] || 'generated.wav'

  // const link = document.createElement('a');
  // link.href = audio_url.value;
  // link.download = serverName || fallbackName;

  // document.body.appendChild(link);
  // link.click();
  // document.body.removeChild(link);
  // 直接跳转至文件地址
  //  window.location.href = audio_url.value;
  // 主方案
  const newTab = window.open(audio_url.value, '_blank')

  // 备用方案（1秒后检测是否被拦截）
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
  console.log('Left button clicked')
  // 左侧按钮点击逻辑
  const currIndex = chooseCharacter.value.index
  if (currIndex > 0 && currIndex - 1 < avatorUrls.value.length) {
    applySelectedCharacterByIndex(currIndex - 1)
  }
}

/**
 * 切换到右侧相邻角色。
 */
const handleRightClick = () => {
  console.log('Right button clicked')
  // 右侧按钮点击逻辑
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
  console.log('Clicked avator index:', index)
  // 更换立绘
  if (index >= 0 && index < names.value.length && index !== chooseCharacter.value.index) {
    applySelectedCharacterByIndex(index)
  }
}

onBeforeMount(async () => {
  if (!names.value || names.value.length === 0) {
    // 如果 standUrls 为空，从后端获取数据
    console.log('get stands from backend.')
    await fetchImageUrls() // 等待数据获取完成
  }
  await restoreSelectedCharacter()
  console.log(chooseCharacter.value)
})

// 搜索建议
/**
 * 根据搜索词过滤角色名称，并返回给自动完成组件。
 * @param queryString 当前输入框中的查询字符串。
 * @param cb Element Plus 自动完成组件的结果回调。
 */
const querySearch = (
  queryString: string,
  cb: (results: Array<{ value: string }>) => void,
) => {
  // 根据用户输入的 queryString 搜索 standUrls 中的键（即图片名称）
  const results = standUrls.value
    .filter((imageName) => imageName.toLowerCase().includes(queryString.toLowerCase()))
    .map((imageName) => ({
      value: imageName, // 这里返回图片名称，作为搜索建议
    }))

  // 返回搜索结果，通过回调函数 cb
  cb(results)
}

// 处理选择搜索结果
/**
 * 处理自动完成面板中的搜索结果点击事件。
 * @param item 当前被选中的搜索项。
 */
const handleSelect = (item: { value: string }) => {
  console.log(item)
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
  /* margin-left: 5%; */
}

.stand-iamge__lazy {
  max-height: 900px;
  margin-left: 10%;
  position: relative; /* 关键：为绝对定位子元素提供参照 */
  display: inline-block; /* 根据内容调整容器大小 */
  /* overflow-y: auto; */
}

.main-stand-image {
  display: block; /* 消除图片下方空隙 */
}

.stand-iamge__lazy .el-image {
  display: block;
  min-height: 200px;
  margin-bottom: 10px;
}

.overlay-button {
  position: absolute;
  top: 50%; /* 垂直居中 */
  transform: translateY(-50%);
  z-index: 10; /* 确保按钮在图片上方 */
}

::v-deep(.overlay-button) {
  /* 移除边框 */
  border: 0 !important;
  /* 透明背景 */
  background-color: transparent !important;
  /* 移除内边距 */
  padding: 0 !important;
  /* 移除最小宽度限制 */
  min-width: auto !important;
  /* 移除点击效果 */
  &:active {
    transform: none;
  }

  /* 移除hover效果
  &:hover,
  &:focus {
    background-color: transparent !important;
    box-shadow: none !important;
  } */

  /* 调整图标颜色 */
  .el-icon {
    color: #409eff; /* 根据需求调整颜色 */
    font-size: 36px; /* 调整图标尺寸 */
  }
}

.left-btn {
  left: 12%; /* 左侧间距 */
}

.right-btn {
  right: 12%; /* 右侧间距 */
}

/* 可选：按钮悬停效果 */
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
  /* position: absolute;
  left: 50%;
  transform: translateX(-50%); */
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
  /* width: 80%; */
  height: 100%;
  /* border-radius: 3rem; */
  /* border: 1px solid #DCDFE6; */
  /* padding: .5rem; */
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
  /* border-radius: 4px; */
  /* background: var(--el-color-danger-light-9);
  color: var(--el-color-danger); */
}

::v-deep(.el-scrollbar__wrap) {
  margin-top: 3%;
}
</style>
