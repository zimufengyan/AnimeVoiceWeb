<script setup lang="ts">
import { RouterLink, RouterView, useRouter } from 'vue-router'
import {
  CloudDownloadOutlined,
  PlayCircleOutlined,
  DownloadOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue'
import { ElMessageBox } from 'element-plus'
import { onBeforeMount, ref, onUpdated } from 'vue'
import { useUserStore } from '@/stores/counter'
import { getAudioRecordsApi, deleteAudioRecordApi, deleteAudioRecordsApi } from './api'
import { de } from 'element-plus/es/locales.mjs'
const userStore = useUserStore()
const router = useRouter()
//初始音频地址
const audio_url = ref('')

// 音频播放处理
const handleAudioPlay = (audioRef, src) => {
  if (audioRef.value) {
    audioRef.value.pause() // 停止当前播放的音频
    audioRef.value.currentTime = 0 // 重置播放时间
    audioRef.value.src = src // 设置新的音频源
    audioRef.value.load() // 加载新音频
    audioRef.value.onloadedmetadata = () => {
      // 确保音频元数据加载完毕
      audioRef.value.play().catch((error) => {
        console.error('播放音频时出错:', error)
      })
    }
  }
}
//英标播放器
const audioElement = ref(null)
const clickAudio = (data) => {
  console.log('url', data)
  handleAudioPlay(audioElement, data)
}

const gotoLogin = () => {
  router.push('/login')
  open.value = false

  // 如果要新窗口打开（备选方案）
  // window.open('/login', '_blank');
}

const open = ref<boolean>(false)
const isLogin = ref<boolean>(userStore.token !== '')
const records = ref([])
const numRecords = ref(0)

const onClose = () => {
  open.value = false
}

const getAudioRecords = async () => {
  // 获取音频记录
  if (userStore.token === '') {
    isLogin.value = false
    return
  }
  await getAudioRecordsApi()
    .then((reponse) => {
      records.value = reponse.records
      numRecords.value = records.value.length
    })
    .catch((error) => {})
}

const deleteAudioRecord = async (audio_id: any) => {
  await deleteAudioRecordApi(audio_id)
    .then((response) => {
      records.value = response.records
      numRecords.value = records.value.length
    })
    .catch((error) => {})
}

const showDrawer = async () => {
  await getAudioRecords()
  open.value = true
}

const downAudio = async (audio_url: string, filename: string) => {
  console.log(`download audio ${filename} from ${audio_url}`)
  const x = new XMLHttpRequest()
  x.open('GET', audio_url, true)
  x.responseType = 'blob'
  x.onload = (e) => {
    // 会创建一个 DOMString，其中包含一个表示参数中给出的对象的URL。这个 URL 的生命周期和创建它的窗口中的 document 绑定。这个新的URL 对象表示指定的 File 对象或 Blob 对象。
    const url = window.URL.createObjectURL(x.response)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
  }
  x.send()
}

onBeforeMount(async () => {
  isLogin.value = userStore.token !== ''
})

onUpdated(async () => {
  isLogin.value = userStore.token !== ''
})
</script>

<template>
  <RouterView />
  <a-float-button-group shape="circle" :style="{ right: '100px' }">
    <a-float-button tooltip="语音生成记录" @click="showDrawer">
      <template #icon>
        <CloudDownloadOutlined />
      </template>
    </a-float-button>
    <a-back-top :visibility-height="0" />
  </a-float-button-group>

  <audio
    ref="audioElement"
    id="audio"
    :src="audio_url"
    preload="auto"
    style="display: block"
  ></audio>

  <a-drawer
    v-model:open="open"
    :size="400"
    :closable="false"
    class="custom-class"
    root-class-name="root-class-name"
    :root-style="{ color: 'blue' }"
    style="color: red"
    title="语音生成记录"
    placement="right"
    @close="onClose"
  >
    <div class="drawer-container" v-if="isLogin">
      <div class="record-container" v-if="numRecords != 0">
        <el-scrollbar>
          <a-card hoverable style="width: 100%" v-for="(record, index) in records">
            <template #actions>
              <PlayCircleOutlined key="play" @click="clickAudio(record['audio_path'])" />
              <download-outlined
                key="download"
                @click="downAudio(record['audio_path'], record['audio_filename'])"
              />
              <delete-outlined key="delete" @click="deleteAudioRecord(record['audio_id'])" />
            </template>
            <a-card-meta :title="record['audio_character']" :description="record['audio_text']">
              <template #avatar>
                <a-avatar :src="record['character_avator_path']" />
              </template>
            </a-card-meta>
          </a-card>
        </el-scrollbar>
      </div>
      <el-text v-else>未查询到任何记录</el-text>
    </div>
    <div v-else>
      <el-text
        >您未登录，点击<a-button type="link" @click="gotoLogin" class="goto-login-btn"
          ><span style="padding: 0 auto; margin: 0 auto">此处</span></a-button
        >登陆</el-text
      >
    </div>
  </a-drawer>
</template>

<style scoped>
.background-container {
  width: 100%;
  height: 100%;
}

el-header {
  line-height: 1.5;
  max-height: 100vh;
  width: 100%;
}

.goto-login-btn {
  /* width: 50px; */
  margin: 0 auto;
  padding: 0 auto;
}

/* .el-aside {
  display: flex;
  height: 100%;
} */
.el-main {
  display: flex;
  width: 100%;
  padding-top: 0.5rem;
  padding-bottom: 1rem;
}

.logo {
  width: 35px;
  height: 35;
  margin-right: 10px;
}
</style>
