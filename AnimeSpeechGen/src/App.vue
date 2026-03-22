<script setup lang="ts">
import { RouterView, useRouter } from 'vue-router'
import {
  CloudDownloadOutlined,
  PlayCircleOutlined,
  DownloadOutlined,
  DeleteOutlined,
  VerticalAlignTopOutlined,
} from '@ant-design/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onBeforeMount, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useUserStore } from '@/stores/counter'
import { getAudioRecordsApi, deleteAudioRecordApi, deleteAudioRecordsApi } from './api'
import type { AudioRecord } from '@/util/types'
import AuthDialog from '@/components/auth/AuthDialog.vue'
import { openAuthDialog } from '@/composables/useAuthDialog'

const userStore = useUserStore()
const router = useRouter()
//初始音频地址
const audio_url = ref('')

// 音频播放处理
const handleAudioPlay = (audioRef: { value: HTMLAudioElement | null }, src: string) => {
  if (audioRef.value) {
    audioRef.value.pause() // 停止当前播放的音频
    audioRef.value.currentTime = 0 // 重置播放时间
    audioRef.value.src = src // 设置新的音频源
    audioRef.value.load() // 加载新音频
    audioRef.value.onloadedmetadata = () => {
      // 确保音频元数据加载完毕
      audioRef.value?.play().catch((error: unknown) => {
        console.error('播放音频时出错:', error)
      })
    }
  }
}
//英标播放器
const audioElement = ref<HTMLAudioElement | null>(null)
const clickAudio = (data: string) => {
  console.log('url', data)
  handleAudioPlay(audioElement, data)
}

const gotoLogin = () => {
  openAuthDialog('login', {
    redirectTo: router.currentRoute.value.fullPath,
  })
  open.value = false
}

const open = ref<boolean>(false)
const isLogin = ref<boolean>(userStore.token !== '')
const records = ref<AudioRecord[]>([])
const numRecords = ref(0)
const selectedAudioIds = ref<number[]>([])
const showBackTop = ref(false)
let scrollTarget: HTMLElement | null = null

const updateRecords = (nextRecords: AudioRecord[] = []) => {
  records.value = nextRecords
  numRecords.value = records.value.length
  selectedAudioIds.value = selectedAudioIds.value.filter((audioId) =>
    records.value.some((record) => record.audio_id === audioId),
  )
}

const isRecordSelected = (audioId: number) => selectedAudioIds.value.includes(audioId)

const toggleRecordSelection = (audioId: number, checked: string | number | boolean) => {
  if (checked) {
    if (!selectedAudioIds.value.includes(audioId)) {
      selectedAudioIds.value = [...selectedAudioIds.value, audioId]
    }
    return
  }

  selectedAudioIds.value = selectedAudioIds.value.filter((id) => id !== audioId)
}

const toggleSelectAll = (checked: string | number | boolean) => {
  selectedAudioIds.value = checked ? records.value.map((record) => record.audio_id) : []
}

const clearSelection = () => {
  selectedAudioIds.value = []
}

const allSelected =
  () => records.value.length > 0 && selectedAudioIds.value.length === records.value.length

const hasPartialSelection =
  () => selectedAudioIds.value.length > 0 && selectedAudioIds.value.length < records.value.length

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
      updateRecords(reponse.records || [])
    })
    .catch((error) => {})
}

const deleteAudioRecord = async (audio_id: any) => {
  await deleteAudioRecordApi(audio_id)
    .then((response) => {
      updateRecords(response.records || [])
    })
    .catch((error) => {})
}

const deleteSelectedAudioRecords = async () => {
  if (selectedAudioIds.value.length === 0) {
    ElMessage({
      type: 'warning',
      message: '请先选择需要删除的记录',
    })
    return
  }

  try {
    await ElMessageBox.confirm(
      `确定删除已选中的 ${selectedAudioIds.value.length} 条历史记录吗？`,
      '批量删除确认',
      {
        confirmButtonText: '删除',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )

    const response = await deleteAudioRecordsApi(selectedAudioIds.value)
    updateRecords(response.records || [])
    ElMessage({
      type: 'success',
      message: '批量删除成功',
    })
  } catch {
    return
  }
}

const showDrawer = async () => {
  await getAudioRecords()
  open.value = true
}

const downAudio = async (audio_url: string, filename: string) => {
  console.log(`download audio ${filename} from ${audio_url}`)
  return await new Promise<void>((resolve, reject) => {
    const x = new XMLHttpRequest()
    x.open('GET', audio_url, true)
    x.responseType = 'blob'
    x.onload = () => {
      const url = window.URL.createObjectURL(x.response)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      a.click()
      window.URL.revokeObjectURL(url)
      resolve()
    }
    x.onerror = () => reject(new Error(`下载失败: ${filename}`))
    x.send()
  })
}

const downloadSelectedAudios = async () => {
  if (selectedAudioIds.value.length === 0) {
    ElMessage({
      type: 'warning',
      message: '请先选择需要下载的记录',
    })
    return
  }

  const selectedRecords = records.value.filter((record) =>
    selectedAudioIds.value.includes(record.audio_id),
  )

  try {
    for (const record of selectedRecords) {
      await downAudio(record.audio_path, record.audio_filename)
      await new Promise((resolve) => setTimeout(resolve, 150))
    }

    ElMessage({
      type: 'success',
      message: `已开始下载 ${selectedRecords.length} 条记录`,
    })
  } catch (error: unknown) {
    ElMessage({
      type: 'error',
      message: error instanceof Error ? error.message : '批量下载失败',
    })
  }
}

onBeforeMount(async () => {
  isLogin.value = userStore.token !== ''
})

watch(
  () => userStore.token,
  (token) => {
    isLogin.value = token !== ''
    if (!isLogin.value) {
      updateRecords([])
      clearSelection()
    }
  },
)

watch(
  () => open.value,
  (value) => {
    if (!value) {
      clearSelection()
    }
  },
)

const formatTime = (time?: string) => {
  if (!time) return ''
  const date = new Date(time)
  if (Number.isNaN(date.getTime())) return time
  return date.toLocaleString('zh-CN', { hour12: false })
}

/**
 * 获取当前页面实际负责滚动的主内容容器，供返回顶部按钮绑定目标。
 * @returns 主内容滚动元素；如果尚未挂载则回退到文档根节点。
 */
const getBackTopTarget = () => {
  return (
    (document.querySelector('.app-scroll-container') as HTMLElement | null) ||
    document.documentElement
  )
}

/**
 * 根据主滚动容器的滚动距离决定是否显示返回顶部按钮。
 */
const syncBackTopVisibility = () => {
  const target = getBackTopTarget()
  showBackTop.value = target.scrollTop > 80
}

/**
 * 将主滚动容器平滑滚动到顶部。
 */
const scrollToTop = () => {
  getBackTopTarget().scrollTo({
    top: 0,
    behavior: 'smooth',
  })
}

onMounted(() => {
  scrollTarget = getBackTopTarget()
  scrollTarget.addEventListener('scroll', syncBackTopVisibility, { passive: true })
  syncBackTopVisibility()
})

onBeforeUnmount(() => {
  scrollTarget?.removeEventListener('scroll', syncBackTopVisibility)
})
</script>

<template>
  <RouterView />
  <AuthDialog />
  <a-float-button-group class="app-float-actions" shape="circle" :style="{ right: '100px' }">
    <a-float-button class="app-float-action" v-if="showBackTop" tooltip="返回顶部" @click="scrollToTop">
      <template #icon>
        <VerticalAlignTopOutlined />
      </template>
    </a-float-button>
    <a-float-button class="app-float-action" tooltip="语音生成记录" @click="showDrawer">
      <template #icon>
        <CloudDownloadOutlined />
      </template>
    </a-float-button>
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
        <div class="batch-toolbar">
          <el-checkbox
            :model-value="allSelected()"
            :indeterminate="hasPartialSelection()"
            @change="toggleSelectAll"
          >
            全选
          </el-checkbox>
          <span class="selected-count">已选 {{ selectedAudioIds.length }} 项</span>
          <div class="batch-actions">
            <a-button size="small" :disabled="selectedAudioIds.length === 0" @click="downloadSelectedAudios">
              批量下载
            </a-button>
            <a-button
              size="small"
              danger
              :disabled="selectedAudioIds.length === 0"
              @click="deleteSelectedAudioRecords"
            >
              批量删除
            </a-button>
          </div>
        </div>
        <el-scrollbar>
          <a-card hoverable class="record-card" style="width: 100%" v-for="(record, index) in records">
            <template #actions>
              <PlayCircleOutlined key="play" @click="clickAudio(record['audio_path'])" />
              <download-outlined
                key="download"
                @click="downAudio(record['audio_path'], record['audio_filename'])"
              />
              <delete-outlined key="delete" @click="deleteAudioRecord(record['audio_id'])" />
            </template>
            <div class="record-card-header">
              <el-checkbox
                :model-value="isRecordSelected(record['audio_id'])"
                @change="(checked: string | number | boolean) => toggleRecordSelection(record['audio_id'], checked)"
              >
                选择
              </el-checkbox>
              <span class="record-created-at">{{ formatTime(record['created_at']) }}</span>
            </div>
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

.drawer-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.batch-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.selected-count {
  color: #606266;
  font-size: 13px;
}

.batch-actions {
  display: flex;
  gap: 8px;
}

.record-card {
  margin-bottom: 12px;
}

.record-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.record-created-at {
  color: #909399;
  font-size: 12px;
}

:deep(.app-float-actions .ant-float-btn-body) {
  color: #eff9fb;
  background:
    linear-gradient(180deg, rgba(17, 40, 58, 0.94), rgba(23, 58, 77, 0.94)),
    linear-gradient(135deg, rgba(108, 195, 185, 0.28), rgba(255, 209, 149, 0.18));
  border: 1px solid rgba(162, 220, 214, 0.3);
  box-shadow:
    0 18px 38px rgba(15, 42, 57, 0.28),
    inset 0 0 0 1px rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(14px);
}

:deep(.app-float-actions .ant-float-btn:hover .ant-float-btn-body) {
  color: #ffffff;
  background:
    linear-gradient(180deg, rgba(21, 51, 73, 0.98), rgba(31, 69, 91, 0.96)),
    linear-gradient(135deg, rgba(108, 195, 185, 0.34), rgba(255, 209, 149, 0.22));
  transform: translateY(-1px);
}

:deep(.app-float-actions .ant-float-btn-icon) {
  font-size: 18px;
}
</style>
