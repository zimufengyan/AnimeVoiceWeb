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
import { ref, onMounted, onBeforeMount, onUpdated } from 'vue'
import { getStaticsUrlApi, getGeneratedVoiceApi } from '@/api'
import { Icon } from '@iconify/vue'
import { fa, tr } from 'element-plus/es/locales.mjs'
import { ElMessage } from 'element-plus'
import { ArrowLeftBold, ArrowRightBold } from '@element-plus/icons-vue'
import type { ElScrollbar } from 'element-plus'

const belong = 'GenShin'
const nameKey = belong + '-Names'
const avatorKey = belong + '-Avators'
const standsKey = belong + '-Stands'
const searchQuery = ref('')
const chooseCharacter = ref({ name: '', url: '', avator: '', index: 0 })
const textarea = ref('')
const isDownloadAvilabel = ref(true)
const latestVoiceUrl = ref('')
const audio_url = ref()
const audioPlayer = ref(null) // 音频组件 ref
const isGeneratingVoice = ref(false)

// 定义滚动条引用
const scrollbarRef = ref<InstanceType<typeof ElScrollbar> | null>(null)

const getCharacterNamesFromLovalStorage = () => {
  const storeNames = localStorage.getItem(nameKey)?.split(',')
  return storeNames
}

const getImageUrlsFromLocalStorage = () => {
  const storedUrls = localStorage.getItem(standsKey)?.split(',')
  return storedUrls
}

const getCharacterAvatorsFromLocalStorage = () => {
  const storeAvators = localStorage.getItem(avatorKey)?.split(',')
  return storeAvators
}

var names = ref(getCharacterNamesFromLovalStorage())
var standUrls = ref(getImageUrlsFromLocalStorage()) // {}
var avatorUrls = ref(getCharacterAvatorsFromLocalStorage())
// var names = ref()
// var standUrls = ref() // {}
// var avatorUrls = ref()
console.log(names.value)
// console.log(standUrls.value)

// 从字典中随机获取一个元素
const getRandomImage = () => {
  const randomKey = Math.floor(Math.random() * names.value.length)
  const randomUrl = standUrls.value[randomKey] // 通过图片名称获取对应的立绘 URL
  const randomAvator = avatorUrls.value[randomKey] // 通过图片名称获取对应的头像 URL
  chooseCharacter.value.index = randomKey
  chooseCharacter.value.name = names.value[randomKey]
  chooseCharacter.value.url = randomUrl
  chooseCharacter.value.avator = randomAvator
}

// 从后端请求图片 URLs 并存储到 localStorage
const fetchImageUrls = async () => {
  await getStaticsUrlApi(belong)
    .then((response) => {
      if (response.names) {
        // 存储获取到的图片 URLs 到 localStorage
        localStorage.setItem(nameKey, response.names)
        localStorage.setItem(standsKey, response.stands)
        localStorage.setItem(avatorKey, response.avators)
        names.value = response.names
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

const handleGenerateBtn = async () => {
  if (!textarea || textarea.value == '') {
    ElMessage({
      message: 'please input text.',
      type: 'warning',
    })
    return
  }
  isGeneratingVoice.value = true // 显示加载
  console.log(`current chosen character: ${chooseCharacter.value['name']}, belong ${belong}`)
  var res = await getGeneratedVoiceApi(textarea.value, chooseCharacter.value.name, belong, 'zh')
    .then((response) => {
      console.log(response)
      isGeneratingVoice.value = false
      ElMessage({
        message: response.meta.message,
        type: 'success',
      })
      audio_url.value = response.audio_url
      audioPlayer.value.src = audio_url.value
      // $refs.audioPlayer.src = this.audioUrl;
      isDownloadAvilabel.value = true
    })
    .catch((error) => {
      console.log(error.message)
    })
}

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

const handleDownloadBtn = async () => {
  if (!isDownloadAvilabel.value) {
    ElMessage({
      message: 'please generate a voice after downloading.',
      type: 'warning',
    })
    return
  }
  // 优先获取服务器指定的文件名
  const serverName = await getServerFileName()
  // 备选方案：从URL提取
  const fallbackName = audio_url.value.split('/').pop().split('?')[0]

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

const handleLeftClick = () => {
  console.log('Left button clicked')
  // 左侧按钮点击逻辑
  const currIndex = chooseCharacter.value.index
  if (currIndex > 0) {
    chooseCharacter.value.index = currIndex - 1
    chooseCharacter.value.avator = avatorUrls.value[currIndex - 1]
    chooseCharacter.value.name = names.value[currIndex - 1]
    chooseCharacter.value.url = standUrls.value[currIndex - 1]
  }
}

const handleRightClick = () => {
  console.log('Right button clicked')
  // 右侧按钮点击逻辑
  const currIndex = chooseCharacter.value.index
  if (currIndex < names.value.length - 1) {
    const nextIndex = currIndex + 1
    chooseCharacter.value.index = nextIndex
    chooseCharacter.value.avator = avatorUrls.value[nextIndex]
    chooseCharacter.value.name = names.value[nextIndex]
    chooseCharacter.value.url = standUrls.value[nextIndex]
  }
}

const handleAvatorClick = (index: number) => {
  console.log('Clicked avator index:', index)
  // 更换立绘
  if (0 <= index < names.value.length && index != chooseCharacter.value.index) {
    chooseCharacter.value.index = index
    chooseCharacter.value.name = names.value[index]
    chooseCharacter.value.url = standUrls.value[index]
    chooseCharacter.value.avator = avatorUrls.value[index]

    if (!scrollbarRef.value) return

    const scrollContainer = scrollbarRef.value.$el.querySelector('.el-scrollbar__wrap')
    const buttons = scrollContainer.querySelectorAll('.scrollbar-character-item')

    if (buttons.length > index) {
      const targetButton = buttons[index]

      // 计算容器和按钮尺寸
      const containerWidth = scrollContainer.clientWidth
      const buttonWidth = targetButton.offsetWidth

      // 计算目标滚动位置
      const buttonOffset = targetButton.offsetLeft
      const scrollPosition = buttonOffset - containerWidth / 2 + buttonWidth / 2

      // 平滑滚动到目标位置
      scrollContainer.scrollTo({
        left: scrollPosition,
        behavior: 'smooth',
      })
    }
  }
}

onBeforeMount(async () => {
  if (!names.value || names.value.length === 0) {
    // 如果 standUrls 为空，从后端获取数据
    console.log('get stands from backend.')
    await fetchImageUrls() // 等待数据获取完成
  }
  getRandomImage() // 在确保 standUrls, names, avators 有数据后调用
  console.log(chooseCharacter.value)
})

onUpdated(async () => {
  if (!names.value || names.value.length === 0) {
    // 如果 standUrls 为空，从后端获取数据
    console.log('get stands from backend.')
    await fetchImageUrls() // 等待数据获取完成
  }
  getRandomImage() // 在确保 standUrls, names, avators 有数据后调用
  console.log(chooseCharacter.value)
})

// 搜索建议
const querySearch = (queryString, cb) => {
  // 根据用户输入的 queryString 搜索 standUrls 中的键（即图片名称）
  const results = Object.keys(standUrls.value)
    .filter((imageName) => imageName.toLowerCase().includes(queryString.toLowerCase()))
    .map((imageName) => ({
      value: imageName, // 这里返回图片名称，作为搜索建议
    }))

  // 返回搜索结果，通过回调函数 cb
  cb(results)
}

// 处理选择搜索结果
const handleSelect = (item: any) => {
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
