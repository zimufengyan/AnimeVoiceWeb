<template>
  <div class="profile-page">
    <div
      class="profile-hero"
      @click="triggerBannerUpload"
      :style="{
        backgroundImage: `linear-gradient(135deg, rgba(16, 24, 40, 0.2), rgba(44, 94, 146, 0.3)), url(${bannerPreview})`,
      }"
    >
      <el-button class="hero-back-btn" circle @click.stop="goHome">
        <el-icon><ArrowLeft /></el-icon>
      </el-button>
    </div>

    <div class="profile-shell">
      <div v-if="isLoggedIn" class="profile-card">
        <div class="profile-summary">
          <div class="avatar-panel">
            <button type="button" :class="['avatar-trigger', avatarRateClass]" @click="triggerAvatarUpload">
              <el-avatar :size="132" :src="avatarPreview" :class="['profile-avatar', avatarRateClass]">
                {{ userInitial }}
              </el-avatar>
              <span class="avatar-hover-mask">更换头像</span>
            </button>
            <el-button size="small" plain class="edit-profile-btn" @click="openProfileEditor">
              编辑资料
            </el-button>
          </div>

          <div class="profile-meta">
            <div class="meta-row">
              <h1 class="profile-name">{{ displayName }}</h1>
              <el-tag class="rate-tag" effect="dark" :type="rateTagType">{{ displayRate }}</el-tag>
            </div>
            <div class="signature-row">
              <button
                v-if="!isEditingSignature"
                type="button"
                class="signature-display"
                @click="startEditingSignature"
              >
                {{ displaySignature }}
              </button>
              <el-input
                v-else
                ref="signatureInputRef"
                v-model="draftSignature"
                class="signature-input"
                maxlength="120"
                @keydown.enter.prevent="saveInlineSignature"
                @blur="saveInlineSignature"
                @keydown.esc.prevent="cancelInlineSignature"
              />
            </div>
            <div class="meta-extra">
              <div class="meta-item">
                <span class="meta-label">UID</span>
                <span class="meta-value meta-value-mono">{{ displayUid }}</span>
              </div>
              <div class="meta-item">
                <el-icon class="meta-icon"><Calendar /></el-icon>
                <span class="meta-value">{{ displayBirthday }}</span>
              </div>
              <div class="meta-item">
                <el-icon class="meta-icon"><component :is="displayGenderIcon" /></el-icon>
                <span class="meta-value">{{ displayGender }}</span>
              </div>
              <div class="meta-item">
                <span class="meta-label">最近更新</span>
                <span class="meta-value">{{ latestRecordTime }}</span>
              </div>
            </div>
          </div>

          <div class="profile-stats">
            <div class="stat-card">
              <span class="stat-value">{{ records.length }}</span>
              <span class="stat-label">历史记录</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ belongSummary }}</span>
              <span class="stat-label">最近活跃 IP</span>
            </div>
          </div>
        </div>

        <div class="profile-content">
          <el-tabs v-model="activeTab" class="profile-tabs">
            <el-tab-pane label="历史记录" name="history">
              <div class="history-toolbar">
                <div class="history-toolbar-left">
                  <el-input
                    v-model="recordSearchQuery"
                    placeholder="搜索角色名或文本"
                    clearable
                    class="history-search"
                  />
                  <el-select v-model="belongFilter" clearable placeholder="筛选 IP" class="history-filter">
                    <el-option label="原神" value="GenShin" />
                    <el-option label="崩坏·星穹铁道" value="StarRail" />
                  </el-select>
                  <el-radio-group v-model="historyLayout" class="layout-switcher">
                    <el-radio-button label="card">卡片</el-radio-button>
                    <el-radio-button label="list">列表</el-radio-button>
                  </el-radio-group>
                </div>
                <div class="history-toolbar-right">
                  <el-checkbox
                    :model-value="allVisibleSelected"
                    :indeterminate="hasPartialVisibleSelection"
                    @change="toggleSelectAllVisible"
                  >
                    全选当前页
                  </el-checkbox>
                  <el-select v-model="pageSize" class="page-size-select">
                    <el-option
                      v-for="size in currentPageSizeOptions"
                      :key="size"
                      :label="`${size} / 页`"
                      :value="size"
                    />
                  </el-select>
                  <el-button @click="getAudioRecords">刷新</el-button>
                  <el-button :disabled="selectedAudioIds.length === 0" @click="downloadSelectedAudios">
                    批量下载
                  </el-button>
                  <el-button
                    type="danger"
                    :disabled="selectedAudioIds.length === 0"
                    @click="deleteSelectedAudioRecords"
                  >
                    批量删除
                  </el-button>
                </div>
              </div>

              <div class="history-summary">
                <span>共 {{ filteredRecords.length }} 条记录</span>
                <span>当前第 {{ currentPage }} / {{ totalPages }} 页</span>
                <span>已选择 {{ selectedAudioIds.length }} 条</span>
              </div>

              <el-empty
                v-if="filteredRecords.length === 0"
                description="还没有符合条件的历史记录"
              />

              <div
                v-else
                :class="historyLayout === 'card' ? 'history-grid' : 'history-list'"
              >
                <el-card
                  v-for="record in paginatedRecords"
                  :key="record.audio_id"
                  :class="historyLayout === 'card' ? 'history-card' : 'history-row'"
                  shadow="hover"
                >
                  <div :class="historyLayout === 'card' ? 'history-card-layout' : 'history-row-layout'">
                    <div class="history-record-main">
                      <div class="history-card-header">
                        <div class="history-card-title">
                          <el-checkbox
                            :model-value="isRecordSelected(record.audio_id)"
                            @change="(checked: string | number | boolean) => toggleRecordSelection(record.audio_id, checked)"
                          />
                          <el-avatar :src="record.character_avator_path" :size="historyLayout === 'card' ? 42 : 48">
                            {{ record.audio_character.slice(0, 1) }}
                          </el-avatar>
                          <div class="history-card-headline">
                            <strong>{{ record.audio_character }}</strong>
                            <div class="headline-meta">
                              <span>{{ formatTime(record.created_at) }}</span>
                              <span class="lang-pill">{{ formatTextLang(record.text_lang) }}</span>
                            </div>
                          </div>
                        </div>
                        <div class="history-card-side">
                          <el-tag size="small" class="belong-tag">{{ record.audio_belong }}</el-tag>
                          <DeleteOutlined class="history-delete-icon" @click="deleteAudioRecord(record.audio_id)" />
                        </div>
                      </div>

                      <div class="history-card-body">
                        <p class="history-text" :title="record.audio_text">
                          {{ formatAudioTextPreview(record.audio_text) }}
                        </p>
                        <audio class="record-audio" controls :src="record.audio_path"></audio>
                      </div>
                    </div>
                  </div>
                </el-card>
              </div>

              <div v-if="filteredRecords.length > 0" class="history-pagination">
                <el-pagination
                  v-model:current-page="currentPage"
                  :page-size="pageSize"
                  :total="filteredRecords.length"
                  background
                  layout="prev, pager, next"
                />
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>

      <el-empty
        v-else
        description="登录后即可查看和管理你的个人中心"
        class="profile-empty"
      >
        <el-button type="primary" @click="goToLogin">前往登录</el-button>
      </el-empty>
    </div>

    <audio ref="audioElement" preload="auto" class="hidden-audio"></audio>
    <input ref="avatarFileInput" type="file" accept="image/*" class="hidden-file-input" @change="handleAvatarFileChange" />
    <input ref="bannerFileInput" type="file" accept="image/*" class="hidden-file-input" @change="handleBannerFileChange" />

    <el-dialog
      v-model="editorVisible"
      title="编辑个人资料"
      width="720px"
      class="profile-editor-dialog"
    >
      <div class="profile-editor">
        <div class="editor-preview">
          <div class="preview-banner" :style="{ backgroundImage: `url(${editForm.profileBanner || bannerPreview})` }">
            <el-avatar :src="editForm.avatar || avatarPreview" :size="96" :class="['preview-avatar', avatarRateClass]">
              {{ userInitial }}
            </el-avatar>
          </div>
        </div>

        <el-form label-position="top" class="editor-form">
          <div class="editor-form-row">
            <el-form-item label="昵称" class="editor-form-item">
              <el-input v-model="editForm.username" maxlength="30" show-word-limit />
            </el-form-item>
            <el-form-item label="评级" class="editor-form-item compact">
              <el-input :model-value="editForm.rate" disabled />
            </el-form-item>
          </div>
          <div class="editor-form-row">
            <el-form-item label="性别" class="editor-form-item">
              <el-select v-model="editForm.gender" placeholder="请选择性别">
                <el-option label="未设置" value="" />
                <el-option label="男" value="male" />
                <el-option label="女" value="female" />
                <el-option label="保密" value="private" />
              </el-select>
            </el-form-item>
            <el-form-item label="生日" class="editor-form-item">
              <el-date-picker
                v-model="editForm.birthday"
                type="date"
                value-format="YYYY-MM-DD"
                format="YYYY/MM/DD"
                placeholder="请选择生日"
                class="full-width-field"
              />
            </el-form-item>
          </div>
          <el-form-item label="个性签名">
            <el-input
              v-model="editForm.signature"
              type="textarea"
              :rows="3"
              maxlength="120"
              show-word-limit
            />
          </el-form-item>
          <div class="editor-form-row editor-form-row-wide">
            <el-form-item label="头像地址" class="editor-form-item">
              <el-input v-model="editForm.avatar" placeholder="可粘贴图片 URL，或使用上传按钮" />
            </el-form-item>
            <el-form-item label="横幅地址" class="editor-form-item">
              <el-input
                v-model="editForm.profileBanner"
                placeholder="可粘贴图片 URL，或点击更换横幅上传本地图片"
              />
            </el-form-item>
          </div>
        </el-form>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="editorVisible = false">取消</el-button>
          <el-button type="primary" @click="saveProfile">保存修改</el-button>
        </div>
      </template>
    </el-dialog>

    <el-dialog
      v-model="cropperVisible"
      :title="cropperDialogTitle"
      width="760px"
      class="profile-cropper-dialog"
      @opened="initializeCropper"
      @closed="resetCropperState"
    >
      <div class="cropper-dialog-body">
        <div :class="['cropper-stage', `cropper-stage-${cropTarget}`]">
          <img ref="cropperImageRef" :src="cropperSource" class="cropper-image" alt="待裁剪图片" />
        </div>
        <div class="cropper-panel">
          <h3 class="cropper-panel-title">{{ cropperDialogTitle }}</h3>
          <p class="cropper-panel-tip">{{ cropperDialogTip }}</p>
          <div class="cropper-panel-meta">
            <span>当前比例</span>
            <strong>{{ cropperAspectLabel }}</strong>
          </div>
          <div class="cropper-slider-group">
            <div class="cropper-slider-head">
              <span>缩放</span>
              <strong>{{ cropperZoomPercent }}%</strong>
            </div>
            <el-slider
              v-model="cropperZoomPercent"
              :min="100"
              :max="220"
              :step="1"
              @input="handleCropperZoomChange"
            />
          </div>
          <div class="cropper-preview-group">
            <span class="cropper-preview-label">实时预览</span>
            <div
              v-if="cropTarget === 'avatar'"
              class="cropper-preview-avatar"
              :style="{ backgroundImage: cropperPreviewUrl ? `url(${cropperPreviewUrl})` : 'none' }"
            ></div>
            <div
              v-else
              class="cropper-preview-banner"
              :style="{ backgroundImage: cropperPreviewUrl ? `url(${cropperPreviewUrl})` : 'none' }"
            ></div>
          </div>
        </div>
      </div>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cropperVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmCropper">确认裁剪</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script lang="ts" setup>
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'
import { computed, nextTick, onBeforeMount, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, Calendar, Female, Male, User } from '@element-plus/icons-vue'
import { DeleteOutlined } from '@ant-design/icons-vue'
import {
  deleteAudioRecordApi,
  deleteAudioRecordsApi,
  getAudioRecordsApi,
  getProfileApi,
  updateProfileApi,
  uploadProfileAvatarApi,
  uploadProfileBannerApi,
} from '@/api'
import { useUserStore } from '@/stores/counter'
import { openAuthDialog } from '@/composables/useAuthDialog'
import DefaultBanner from '@/assets/slideImgs/slideImg3.png'
import DefaultAvatar from '@/assets/zmfy.jpg'
import type { AudioRecord, UpdateProfilePayload, UserGender, UserProfile } from '@/util/types'

type EditableProfileForm = {
  username: string
  avatar: string
  rate: string
  signature: string
  profileBanner: string
  birthday: string
  gender: string
}

type HistoryLayout = 'card' | 'list'
type CropTarget = 'avatar' | 'banner'

const HISTORY_LAYOUT_KEY = 'profile-history-layout'
const CARD_PAGE_SIZES = [4, 6, 8, 12]
const LIST_PAGE_SIZES = [5, 8, 10, 15]
const AVATAR_CROP_RATIO = 1
const BANNER_CROP_RATIO = 16 / 5

const router = useRouter()
const userStore = useUserStore()
const { token, user } = storeToRefs(userStore)

const activeTab = ref('history')
const editorVisible = ref(false)
const recordSearchQuery = ref('')
const belongFilter = ref('')
const historyLayout = ref<HistoryLayout>(
  (localStorage.getItem(HISTORY_LAYOUT_KEY) as HistoryLayout) || 'card',
)
const currentPage = ref(1)
const pageSize = ref(historyLayout.value === 'card' ? 6 : 8)
const records = ref<AudioRecord[]>([])
const selectedAudioIds = ref<number[]>([])
const audioElement = ref<HTMLAudioElement | null>(null)
const signatureInputRef = ref()
const cropperImageRef = ref<HTMLImageElement | null>(null)
const avatarFileInput = ref<HTMLInputElement | null>(null)
const bannerFileInput = ref<HTMLInputElement | null>(null)
const rateOptions = ['S', 'A', 'B', 'C', 'D']
const isEditingSignature = ref(false)
const draftSignature = ref('')
const cropperVisible = ref(false)
const cropTarget = ref<CropTarget>('avatar')
const cropperSource = ref('')
const cropperFileName = ref('cropped-image.png')
const cropperPreviewUrl = ref('')
const cropperZoomPercent = ref(100)
const cropperBaseRatio = ref(1)
let cropperInstance: Cropper | null = null

const editForm = reactive<EditableProfileForm>({
  username: '',
  avatar: '',
  rate: 'A',
  signature: '',
  profileBanner: '',
  birthday: '',
  gender: '',
})

const isLoggedIn = computed(() => token.value !== '')
const displayName = computed(() => user.value.username || '未命名旅行者')
const displayRate = computed(() => user.value.rate || 'A')
const displaySignature = computed(
  () => user.value.signature || '还没有留下个性签名，先写一句介绍自己吧。',
)
const displayUidValue = computed(() => `${user.value.uid || ''}`)
const displayUid = computed(() => formatDisplayUid(displayUidValue.value))
const displayBirthday = computed(() => formatBirthday(user.value.birthday))
const displayGender = computed(() => formatGenderLabel(user.value.gender))
const cropperDialogTitle = computed(() =>
  cropTarget.value === 'avatar' ? '裁剪头像' : '裁剪横幅',
)
const cropperDialogTip = computed(() =>
  cropTarget.value === 'avatar'
    ? '保持固定头像框，直接拖动图片调整显示区域，滚轮可轻微缩放。'
    : '保持固定横幅框，直接拖动图片调整显示区域，滚轮可轻微缩放。',
)
const cropperAspectLabel = computed(() =>
  cropTarget.value === 'avatar' ? '1 : 1' : '16 : 5',
)
const displayGenderIcon = computed(() => {
  if (user.value.gender === 'male') return Male
  if (user.value.gender === 'female') return Female
  return User
})
const avatarPreview = computed(() => user.value.avatar || DefaultAvatar)
const bannerPreview = computed(() => user.value.profileBanner || DefaultBanner)
const userInitial = computed(() => displayName.value.slice(0, 1).toUpperCase())
const latestRecordTime = computed(() => {
  if (records.value.length === 0) return '暂无'
  return formatTime(records.value[0].created_at) || '暂无'
})
const belongSummary = computed(() => {
  if (records.value.length === 0) return '--'
  return records.value[0].audio_belong
})
const rateTagType = computed(() => {
  const rate = displayRate.value
  if (rate === 'S') return 'warning'
  if (rate === 'A') return 'success'
  if (rate === 'B') return 'primary'
  if (rate === 'C') return 'info'
  return 'danger'
})
const avatarRateClass = computed(() => getAvatarRateClass(displayRate.value))
const currentPageSizeOptions = computed(() =>
  historyLayout.value === 'card' ? CARD_PAGE_SIZES : LIST_PAGE_SIZES,
)

/**
 * 将任意字符串归一化为前端资料里约定的性别枚举。
 * @param gender 原始性别字段值。
 * @returns 安全的性别枚举值。
 */
const normalizeGender = (gender?: string): UserGender => {
  if (gender === 'male' || gender === 'female' || gender === 'private') {
    return gender
  }
  return ''
}

/**
 * 将当前页面需要维护的资料字段统一写回用户 store。
 * @param profilePatch 需要覆盖到当前资料里的字段。
 */
const applyProfilePatch = (
  profilePatch: Partial<
    Pick<
      UserProfile,
      'username' | 'avatar' | 'uid' | 'rate' | 'signature' | 'profileBanner' | 'birthday' | 'gender'
    >
  >,
) => {
  userStore.updateProfile({
    username: profilePatch.username,
    avatar: profilePatch.avatar,
    uid: profilePatch.uid,
    rate: profilePatch.rate,
    signature: profilePatch.signature,
    profileBanner: profilePatch.profileBanner,
    birthday: profilePatch.birthday,
    gender: profilePatch.gender,
  })
}

/**
 * 将后端返回的完整资料对象同步到本地 store，确保界面以后端为准。
 * @param profile 后端返回的用户资料对象。
 */
const applyBackendProfile = (profile: UserProfile) => {
  applyProfilePatch({
    username: profile.username,
    avatar: profile.avatar,
    uid: `${profile.uid || ''}`,
    rate: profile.rate,
    signature: profile.signature,
    profileBanner: profile.profileBanner,
    birthday: profile.birthday,
    gender: profile.gender,
  })
}

/**
 * 将编辑弹窗中的资料表单转成后端更新接口需要的负载。
 * @returns 可直接提交给资料更新接口的对象。
 */
const buildProfilePayloadFromForm = (): UpdateProfilePayload => {
  return {
    username: editForm.username.trim(),
    avatar: editForm.avatar.trim(),
    signature: editForm.signature.trim(),
    profileBanner: editForm.profileBanner.trim(),
    birthday: editForm.birthday,
    gender: normalizeGender(editForm.gender),
  }
}

/**
 * 拉取当前登录用户的个人资料，成功时以后端返回值为准。
 */
const loadProfile = async () => {
  if (!isLoggedIn.value) {
    syncEditForm()
    return
  }

  try {
    const response = await getProfileApi()
    applyBackendProfile(response.profile)
  } catch {
    // 接口异常时回退到本地缓存，避免个人中心无法使用。
  } finally {
    syncEditForm()
  }
}

const filteredRecords = computed(() => {
  const searchValue = recordSearchQuery.value.trim().toLowerCase()
  return records.value.filter((record) => {
    const matchesBelong = !belongFilter.value || record.audio_belong === belongFilter.value
    const matchesKeyword =
      !searchValue ||
      record.audio_character.toLowerCase().includes(searchValue) ||
      record.audio_text.toLowerCase().includes(searchValue)
    return matchesBelong && matchesKeyword
  })
})

const totalPages = computed(() => Math.max(Math.ceil(filteredRecords.value.length / pageSize.value), 1))
const paginatedRecords = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRecords.value.slice(start, start + pageSize.value)
})

const allVisibleSelected = computed(
  () =>
    paginatedRecords.value.length > 0 &&
    paginatedRecords.value.every((record) => selectedAudioIds.value.includes(record.audio_id)),
)

const hasPartialVisibleSelection = computed(() => {
  if (paginatedRecords.value.length === 0) return false
  const selectedVisibleCount = paginatedRecords.value.filter((record) =>
    selectedAudioIds.value.includes(record.audio_id),
  ).length
  return selectedVisibleCount > 0 && selectedVisibleCount < paginatedRecords.value.length
})

/**
 * 按当前 store 用户信息重置资料编辑表单，确保弹窗里展示的是最新状态。
 */
const syncEditForm = () => {
  editForm.username = user.value.username || ''
  editForm.avatar = user.value.avatar || ''
  editForm.rate = user.value.rate || 'A'
  editForm.signature = user.value.signature || ''
  editForm.profileBanner = user.value.profileBanner || ''
  editForm.birthday = user.value.birthday || ''
  editForm.gender = user.value.gender || ''
}

/**
 * 打开资料编辑弹窗，并提前同步当前资料值。
 */
const openProfileEditor = () => {
  syncEditForm()
  editorVisible.value = true
}

/**
 * 进入个性签名的内联编辑状态，并自动聚焦输入框。
 */
const startEditingSignature = async () => {
  draftSignature.value = user.value.signature || ''
  isEditingSignature.value = true
  await nextTick()
  signatureInputRef.value?.focus?.()
}

/**
 * 跳转到登录页，供未登录状态的个人中心使用。
 */
const goToLogin = () => {
  openAuthDialog('login', {
    redirectTo: router.currentRoute.value.fullPath,
  })
}

/**
 * 从个人中心返回首页。
 */
const goHome = () => {
  router.push('/')
}

/**
 * 获取当前用户的语音历史记录，并同步清理失效的选中项。
 */
const getAudioRecords = async () => {
  if (!isLoggedIn.value) {
    records.value = []
    selectedAudioIds.value = []
    return
  }

  try {
    const response = await getAudioRecordsApi()
    records.value = response.records || []
    selectedAudioIds.value = selectedAudioIds.value.filter((audioId) =>
      records.value.some((record) => record.audio_id === audioId),
    )
  } catch (error: unknown) {
    ElMessage({
      type: 'error',
      message: error instanceof Error ? error.message : '加载历史记录失败',
    })
  }
}

/**
 * 判断指定记录当前是否处于选中状态。
 * @param audioId 音频记录主键。
 * @returns 如果已选中则返回 true。
 */
const isRecordSelected = (audioId: number) => {
  return selectedAudioIds.value.includes(audioId)
}

/**
 * 切换单条记录的选择状态。
 * @param audioId 音频记录主键。
 * @param checked 来自复选框的选中状态。
 */
const toggleRecordSelection = (audioId: number, checked: string | number | boolean) => {
  if (checked) {
    if (!selectedAudioIds.value.includes(audioId)) {
      selectedAudioIds.value = [...selectedAudioIds.value, audioId]
    }
    return
  }

  selectedAudioIds.value = selectedAudioIds.value.filter((id) => id !== audioId)
}

/**
 * 针对当前页记录执行全选或取消全选。
 * @param checked 全选框的勾选状态。
 */
const toggleSelectAllVisible = (checked: string | number | boolean) => {
  const visibleIds = paginatedRecords.value.map((record) => record.audio_id)
  if (checked) {
    selectedAudioIds.value = Array.from(new Set([...selectedAudioIds.value, ...visibleIds]))
    return
  }

  selectedAudioIds.value = selectedAudioIds.value.filter((audioId) => !visibleIds.includes(audioId))
}

/**
 * 统一处理页面内音频播放，避免多个音频同时发声。
 * @param src 需要播放的音频地址。
 */
const playAudio = (src: string) => {
  if (!audioElement.value) return

  audioElement.value.pause()
  audioElement.value.currentTime = 0
  audioElement.value.src = src
  audioElement.value.load()
  audioElement.value.onloadedmetadata = () => {
    audioElement.value?.play().catch(() => undefined)
  }
}

/**
 * 下载指定音频文件，供单条下载和批量下载复用。
 * @param audioUrl 资源下载地址。
 * @param filename 下载时使用的文件名。
 */
const downAudio = async (audioUrl: string, filename: string) => {
  return await new Promise<void>((resolve, reject) => {
    const request = new XMLHttpRequest()
    request.open('GET', audioUrl, true)
    request.responseType = 'blob'
    request.onload = () => {
      const url = window.URL.createObjectURL(request.response)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = filename
      anchor.click()
      window.URL.revokeObjectURL(url)
      resolve()
    }
    request.onerror = () => reject(new Error(`下载失败: ${filename}`))
    request.send()
  })
}

/**
 * 批量下载当前选中的音频记录。
 */
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

/**
 * 删除单条音频记录，并刷新本地列表。
 * @param audioId 需要删除的音频记录主键。
 */
const deleteAudioRecord = async (audioId: number) => {
  try {
    const response = await deleteAudioRecordApi(audioId)
    records.value = response.records || []
    selectedAudioIds.value = selectedAudioIds.value.filter((id) => id !== audioId)
    ElMessage({
      type: 'success',
      message: '删除成功',
    })
  } catch (error: unknown) {
    ElMessage({
      type: 'error',
      message: error instanceof Error ? error.message : '删除失败',
    })
  }
}

/**
 * 批量删除当前选中的音频记录。
 */
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
    records.value = response.records || []
    selectedAudioIds.value = []
    ElMessage({
      type: 'success',
      message: '批量删除成功',
    })
  } catch {
    return
  }
}

/**
 * 将上传的本地图片文件读取为 Data URL，便于前端本地持久化展示。
 * @param file 用户选择的图片文件。
 * @returns 图片的 base64 Data URL。
 */
const readFileAsDataUrl = async (file: File) => {
  return await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(`${reader.result || ''}`)
    reader.onerror = () => reject(new Error('图片读取失败'))
    reader.readAsDataURL(file)
  })
}

/**
 * 销毁当前裁剪实例，避免重复初始化和对象泄漏。
 */
const destroyCropper = () => {
  cropperInstance?.destroy()
  cropperInstance = null
}

/**
 * 获取当前真正可用的裁剪实例，兼容 Cropper 在图片元素上挂载的实例引用。
 * @returns 当前可用的 Cropper 实例。
 */
const getActiveCropper = () => {
  const imageCropper = (cropperImageRef.value as (HTMLImageElement & { cropper?: Cropper }) | null)?.cropper
  return imageCropper || cropperInstance
}

/**
 * 清理裁剪弹窗状态，并释放临时图片 URL。
 */
const resetCropperState = () => {
  destroyCropper()
  if (cropperSource.value.startsWith('blob:')) {
    URL.revokeObjectURL(cropperSource.value)
  }
  cropperSource.value = ''
  cropperFileName.value = 'cropped-image.png'
  cropperPreviewUrl.value = ''
  cropperZoomPercent.value = 100
  cropperBaseRatio.value = 1
}

/**
 * 根据裁剪目标返回对应的宽高比例。
 * @param target 当前裁剪目标，头像或横幅。
 * @returns 裁剪器应使用的宽高比。
 */
const getCropAspectRatio = (target: CropTarget) => {
  return target === 'avatar' ? AVATAR_CROP_RATIO : BANNER_CROP_RATIO
}

/**
 * 将用户选中的图片载入裁剪弹窗，等待确认后再上传。
 * @param file 用户本次选择的原始图片文件。
 * @param target 当前图片要应用到头像还是横幅。
 */
const openCropperForFile = async (file: File, target: CropTarget) => {
  if (!file.type.startsWith('image/')) {
    throw new Error('请选择图片文件')
  }

  resetCropperState()
  cropTarget.value = target
  cropperFileName.value = file.name || `cropped-${target}.png`
  cropperSource.value = URL.createObjectURL(file)
  cropperVisible.value = true
}

/**
 * 将当前裁剪结果同步成实时预览图，方便确认最终展示区域。
 */
const syncCropperPreview = () => {
  const activeCropper = getActiveCropper()
  if (!activeCropper || typeof activeCropper.getCroppedCanvas !== 'function') return

  const previewWidth = cropTarget.value === 'avatar' ? 160 : 320
  const previewHeight = cropTarget.value === 'avatar' ? 160 : 100
  const previewCanvas = activeCropper.getCroppedCanvas({
    width: previewWidth,
    height: previewHeight,
    imageSmoothingEnabled: true,
    imageSmoothingQuality: 'high',
  })
  cropperPreviewUrl.value = previewCanvas.toDataURL('image/png')
}

/**
 * 根据滑杆值调整当前图片缩放比例，保持“拖图片选显示区域”的交互方式。
 * @param nextPercent 当前滑杆百分比。
 */
const handleCropperZoomChange = (nextPercent: number | number[]) => {
  const activeCropper = getActiveCropper()
  if (!activeCropper) return

  const normalizedPercent = Array.isArray(nextPercent) ? nextPercent[0] : nextPercent
  if (!Number.isFinite(normalizedPercent)) return

  activeCropper.zoomTo(cropperBaseRatio.value * (normalizedPercent / 100))
  syncCropperPreview()
}

/**
 * 在裁剪弹窗打开后初始化 Cropper，接管图片缩放和裁切交互。
 */
const initializeCropper = async () => {
  destroyCropper()
  await nextTick()
  if (!cropperImageRef.value || !cropperSource.value) return

  cropperInstance = new Cropper(cropperImageRef.value, {
    aspectRatio: getCropAspectRatio(cropTarget.value),
    viewMode: 1,
    dragMode: 'move',
    autoCropArea: 1,
    background: false,
    guides: false,
    center: false,
    highlight: false,
    movable: true,
    zoomable: true,
    cropBoxMovable: false,
    cropBoxResizable: false,
    zoomOnWheel: true,
    wheelZoomRatio: 0.08,
    responsive: true,
    scalable: false,
    toggleDragModeOnDblclick: false,
    crop: () => {
      syncCropperPreview()
    },
    ready: () => {
      const activeCropper = getActiveCropper()
      if (!activeCropper) return

      const containerData = activeCropper.getContainerData()
      const aspectRatio = getCropAspectRatio(cropTarget.value)
      const maxWidth = Math.max(containerData.width - 48, 160)
      const maxHeight = Math.max(containerData.height - 48, 120)
      let cropBoxWidth = maxWidth
      let cropBoxHeight = cropBoxWidth / aspectRatio

      if (cropBoxHeight > maxHeight) {
        cropBoxHeight = maxHeight
        cropBoxWidth = cropBoxHeight * aspectRatio
      }

      activeCropper.setCropBoxData({
        left: (containerData.width - cropBoxWidth) / 2,
        top: (containerData.height - cropBoxHeight) / 2,
        width: cropBoxWidth,
        height: cropBoxHeight,
      })
      activeCropper.setDragMode('move')

      const imageData = activeCropper.getImageData()
      cropperBaseRatio.value =
        imageData.naturalWidth > 0 ? imageData.width / imageData.naturalWidth : 1
      cropperZoomPercent.value = 100
      syncCropperPreview()
    },
  })
}

/**
 * 将当前裁剪区域导出为新的图片文件，供后续上传或本地预览复用。
 * @returns 已裁剪好的图片文件对象。
 */
const exportCroppedFile = async () => {
  const activeCropper = getActiveCropper()
  if (!activeCropper || typeof activeCropper.getCroppedCanvas !== 'function') {
    throw new Error('裁剪器尚未准备好')
  }

  const outputWidth = cropTarget.value === 'avatar' ? 512 : 1600
  const outputHeight = cropTarget.value === 'avatar' ? 512 : 500
  const fileType = cropTarget.value === 'avatar' ? 'image/png' : 'image/jpeg'
  const normalizedName = cropperFileName.value.replace(/\.[^.]+$/, '')
  const outputName =
    cropTarget.value === 'avatar' ? `${normalizedName}-avatar.png` : `${normalizedName}-banner.jpg`

  const canvas = activeCropper.getCroppedCanvas({
    width: outputWidth,
    height: outputHeight,
    imageSmoothingEnabled: true,
    imageSmoothingQuality: 'high',
  })

  const blob = await new Promise<Blob | null>((resolve) => {
    canvas.toBlob(resolve, fileType, 0.92)
  })

  if (!blob) {
    throw new Error('裁剪后的图片导出失败')
  }

  return new File([blob], outputName, { type: fileType })
}

/**
 * 触发头像文件选择器，供用户上传本地头像。
 */
const triggerAvatarUpload = () => {
  avatarFileInput.value?.click()
}

/**
 * 触发横幅文件选择器，供用户上传本地横幅。
 */
const triggerBannerUpload = () => {
  bannerFileInput.value?.click()
}

/**
 * 优先调用后端资料更新接口，失败时回退到本地 store，保证个人中心始终可编辑。
 * @param payload 需要保存的资料字段。
 * @param successMessage 成功后的提示文案。
 */
const persistProfileWithFallback = async (
  payload: UpdateProfilePayload,
  successMessage: string,
) => {
  try {
    const response = await updateProfileApi(payload)
    applyBackendProfile(response.profile)
    ElMessage({
      type: 'success',
      message: successMessage,
    })
  } catch {
    applyProfilePatch({
      username: payload.username,
      avatar: payload.avatar,
      signature: payload.signature,
      profileBanner: payload.profileBanner,
      birthday: payload.birthday,
      gender: payload.gender,
    })
    ElMessage({
      type: 'warning',
      message: '后端资料接口暂不可用，已先保存到本地',
    })
  } finally {
    syncEditForm()
  }
}

/**
 * 保存个人信息区内联编辑的个性签名。
 */
const saveInlineSignature = async () => {
  if (!isEditingSignature.value) return
  await persistProfileWithFallback(
    {
      signature: draftSignature.value.trim(),
    },
    '个性签名已更新',
  )
  isEditingSignature.value = false
}

/**
 * 取消个性签名内联编辑，恢复到保存前的展示状态。
 */
const cancelInlineSignature = () => {
  if (!isEditingSignature.value) return
  draftSignature.value = user.value.signature || ''
  isEditingSignature.value = false
}

/**
 * 将裁剪后的头像文件同步到后端，失败时回退到本地 Data URL 预览。
 * @param file 已裁剪好的头像图片文件。
 */
const applyAvatarFile = async (file: File) => {
  try {
    try {
      const response = await uploadProfileAvatarApi(file)
      const nextAvatar =
        response.assetUrl || response.profile?.avatar || editForm.avatar || user.value.avatar || ''
      editForm.avatar = nextAvatar
      if (response.profile) {
        applyBackendProfile(response.profile)
      } else {
        applyProfilePatch({ avatar: nextAvatar })
      }
    } catch {
      const imageDataUrl = await readFileAsDataUrl(file)
      editForm.avatar = imageDataUrl
      applyProfilePatch({ avatar: imageDataUrl })
    }
    ElMessage({
      type: 'success',
      message: '头像已更新',
    })
  } catch (error: unknown) {
    ElMessage({
      type: 'error',
      message: error instanceof Error ? error.message : '头像上传失败',
    })
  }
}

/**
 * 将裁剪后的横幅文件同步到后端，失败时回退到本地 Data URL 预览。
 * @param file 已裁剪好的横幅图片文件。
 */
const applyBannerFile = async (file: File) => {
  try {
    try {
      const response = await uploadProfileBannerApi(file)
      const nextBanner =
        response.assetUrl ||
        response.profile?.profileBanner ||
        editForm.profileBanner ||
        user.value.profileBanner ||
        ''
      editForm.profileBanner = nextBanner
      if (response.profile) {
        applyBackendProfile(response.profile)
      } else {
        applyProfilePatch({
          profileBanner: nextBanner,
        })
      }
    } catch {
      const imageDataUrl = await readFileAsDataUrl(file)
      editForm.profileBanner = imageDataUrl
      applyProfilePatch({ profileBanner: imageDataUrl })
    }
    ElMessage({
      type: 'success',
      message: '横幅已更新',
    })
  } catch (error: unknown) {
    ElMessage({
      type: 'error',
      message: error instanceof Error ? error.message : '横幅上传失败',
    })
  }
}

/**
 * 处理头像文件选择，先打开裁剪弹窗，再决定最终上传内容。
 * @param event input[type=file] 的 change 事件。
 */
const handleAvatarFileChange = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  try {
    await openCropperForFile(file, 'avatar')
  } catch (error: unknown) {
    ElMessage({
      type: 'error',
      message: error instanceof Error ? error.message : '头像读取失败',
    })
  } finally {
    input.value = ''
  }
}

/**
 * 处理横幅文件选择，先打开裁剪弹窗，再决定最终上传内容。
 * @param event input[type=file] 的 change 事件。
 */
const handleBannerFileChange = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  try {
    await openCropperForFile(file, 'banner')
  } catch (error: unknown) {
    ElMessage({
      type: 'error',
      message: error instanceof Error ? error.message : '横幅读取失败',
    })
  } finally {
    input.value = ''
  }
}

/**
 * 确认当前裁剪结果，并按照目标类型更新头像或横幅。
 */
const confirmCropper = async () => {
  try {
    const croppedFile = await exportCroppedFile()
    if (cropTarget.value === 'avatar') {
      await applyAvatarFile(croppedFile)
    } else {
      await applyBannerFile(croppedFile)
    }
    cropperVisible.value = false
  } catch (error: unknown) {
    ElMessage({
      type: 'error',
      message: error instanceof Error ? error.message : '图片裁剪失败',
    })
  }
}

/**
 * 保存资料编辑弹窗中的修改，优先同步到后端，再回写到本地 store。
 */
const saveProfile = async () => {
  if (!editForm.username.trim()) {
    ElMessage({
      type: 'warning',
      message: '昵称不能为空',
    })
    return
  }

  await persistProfileWithFallback(buildProfilePayloadFromForm(), '个人资料已更新')
  editorVisible.value = false
}

/**
 * 将后端返回的文本语言码压缩为更突出的短标记。
 * @param textLang 语言码，例如 zh / en。
 * @returns 标准化后的展示值。
 */
const formatTextLang = (textLang?: string) => {
  return (textLang || '--').trim().toUpperCase()
}

/**
 * 将较长的语音文本压缩为单行预览，保留首尾语义并省略中间部分。
 * @param text 原始语音文本。
 * @returns 适合卡片/列表单行展示的文本预览。
 */
const formatAudioTextPreview = (text?: string) => {
  const normalizedText = (text || '').replace(/\s+/g, ' ').trim()
  if (!normalizedText) return ''

  const maxLength = historyLayout.value === 'card' ? 16 : 24
  if (normalizedText.length <= maxLength) {
    return normalizedText
  }

  const prefixLength = Math.max(4, Math.ceil((maxLength - 1) / 3))
  const suffixLength = Math.max(6, maxLength - prefixLength - 1)
  return `${normalizedText.slice(0, prefixLength)}…${normalizedText.slice(-suffixLength)}`
}

/**
 * 将后端返回的 UID 规范化为九位展示值。
 * @param uid 当前用户 UID 字段。
 * @returns 适合界面展示的九位 UID。
 */
const formatDisplayUid = (uid?: string) => {
  const normalizedUid = `${uid || ''}`.trim()
  if (!normalizedUid) {
    return '100000000'
  }
  return normalizedUid
}

/**
 * 将生日字段格式化为适合个人信息展示的文本。
 * @param birthday 生日字符串，期望格式为 YYYY-MM-DD。
 * @returns 格式化后的生日文本。
 */
const formatBirthday = (birthday?: string) => {
  if (!birthday) return '未设置生日'
  return birthday.replace(/-/g, '/')
}

/**
 * 将性别字段转换为界面展示文本。
 * @param gender 性别字段值。
 * @returns 用于界面显示的中文文本。
 */
const formatGenderLabel = (gender?: string) => {
  if (gender === 'male') return '男'
  if (gender === 'female') return '女'
  if (gender === 'private') return '保密'
  return '未设置'
}

/**
 * 将后端时间字段格式化为适合中文界面展示的时间字符串。
 * @param time 后端返回的 ISO 时间字符串。
 * @returns 本地化后的时间文本。
 */
const formatTime = (time?: string) => {
  if (!time) return '未知时间'
  const date = new Date(time)
  if (Number.isNaN(date.getTime())) return time
  return date.toLocaleString('zh-CN', { hour12: false })
}

/**
 * 将评级映射为头像外框主题类，供个人中心头像装饰复用。
 * @param rate 当前用户评级。
 * @returns 对应的头像主题类名。
 */
const getAvatarRateClass = (rate?: string) => {
  const normalizedRate = (rate || '').trim().toUpperCase()
  if (normalizedRate === 'S') return 'avatar-rate-s'
  if (normalizedRate === 'A') return 'avatar-rate-a'
  if (normalizedRate === 'B') return 'avatar-rate-b'
  if (normalizedRate === 'C') return 'avatar-rate-c'
  return 'avatar-rate-d'
}

onBeforeMount(async () => {
  await loadProfile()
  await getAudioRecords()
})

onBeforeUnmount(() => {
  resetCropperState()
})

watch(
  () => token.value,
  async (nextToken) => {
    if (!nextToken) {
      records.value = []
      selectedAudioIds.value = []
      syncEditForm()
      return
    }

    await loadProfile()
    await getAudioRecords()
  },
)

watch([recordSearchQuery, belongFilter], () => {
  currentPage.value = 1
})

watch(historyLayout, (layout) => {
  localStorage.setItem(HISTORY_LAYOUT_KEY, layout)
  pageSize.value = layout === 'card' ? 6 : 8
  currentPage.value = 1
})

watch(pageSize, () => {
  currentPage.value = 1
})

watch(filteredRecords, (nextRecords) => {
  const nextTotalPages = Math.max(Math.ceil(nextRecords.length / pageSize.value), 1)
  if (currentPage.value > nextTotalPages) {
    currentPage.value = nextTotalPages
  }
})
</script>

<style scoped>
.profile-page {
  width: 100%;
  min-height: calc(100vh - 60px);
  padding-bottom: 48px;
  background:
    radial-gradient(circle at top right, rgba(64, 158, 255, 0.12), transparent 22%),
    linear-gradient(180deg, #eef4fb 0%, #f8fafc 30%, #ffffff 100%);
}

.profile-hero {
  height: 380px;
  background-position: center;
  background-size: cover;
  border-radius: 0 0 28px 28px;
  overflow: hidden;
  cursor: pointer;
  position: relative;
}

.profile-hero::after {
  content: '更换横幅';
  position: absolute;
  right: 28px;
  top: 28px;
  padding: 10px 16px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.52);
  color: #fff;
  font-size: 14px;
  letter-spacing: 0.04em;
  opacity: 0;
  transform: translateY(-6px);
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.profile-hero:hover::after {
  opacity: 1;
  transform: translateY(0);
}

.hero-back-btn {
  position: absolute;
  left: 28px;
  top: 28px;
  z-index: 1;
  width: 42px;
  height: 42px;
  min-width: 42px;
  padding: 0 !important;
  border-radius: 50% !important;
  border: 1px solid rgba(15, 23, 42, 0.12);
  color: #0f172a;
  background: rgba(255, 255, 255, 0.96);
  box-shadow:
    0 10px 30px rgba(15, 23, 42, 0.16),
    0 0 0 1px rgba(255, 255, 255, 0.42);
}

.hero-back-btn:hover {
  color: #0f172a;
  background: #ffffff;
  border-color: rgba(59, 130, 246, 0.24);
  box-shadow:
    0 14px 32px rgba(15, 23, 42, 0.22),
    0 0 0 1px rgba(255, 255, 255, 0.56);
}

.profile-shell {
  width: min(1200px, calc(100% - 64px));
  margin: -140px auto 0;
}

.profile-card {
  position: relative;
}

.profile-summary {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr) 240px;
  gap: 24px;
  align-items: center;
  padding: 22px 28px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 20px 60px rgba(15, 23, 42, 0.1);
  backdrop-filter: blur(20px);
}

.avatar-panel {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
}

.avatar-trigger {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  padding: 0;
  border-radius: 50%;
  background: transparent;
  cursor: pointer;
  --avatar-frame-start: #7c8aa5;
  --avatar-frame-end: #53627c;
  --avatar-frame-glow: rgba(83, 98, 124, 0.28);
  --avatar-frame-highlight: rgba(255, 255, 255, 0.72);
}

.avatar-trigger::before {
  content: '';
  position: absolute;
  inset: -10px;
  z-index: 0;
  border-radius: 50%;
  background:
    radial-gradient(circle at 28% 24%, var(--avatar-frame-highlight), transparent 34%),
    linear-gradient(145deg, var(--avatar-frame-start), var(--avatar-frame-end));
  box-shadow:
    0 18px 34px var(--avatar-frame-glow),
    0 0 0 1px rgba(255, 255, 255, 0.42);
  transition: transform 0.22s ease, box-shadow 0.22s ease;
}

.profile-avatar {
  position: relative;
  z-index: 1;
  border: 5px solid rgba(255, 255, 255, 0.95);
  box-shadow:
    0 16px 30px rgba(15, 23, 42, 0.18),
    0 0 0 3px rgba(255, 255, 255, 0.3);
}

.avatar-trigger:hover::before {
  transform: scale(1.02);
  box-shadow:
    0 22px 38px var(--avatar-frame-glow),
    0 0 0 1px rgba(255, 255, 255, 0.5);
}

.avatar-rate-s {
  --avatar-frame-start: #fff3a3;
  --avatar-frame-end: #d99416;
  --avatar-frame-glow: rgba(232, 178, 43, 0.38);
  --avatar-frame-highlight: rgba(255, 251, 230, 0.95);
}

.avatar-rate-a {
  --avatar-frame-start: #d9d0ff;
  --avatar-frame-end: #6f63ff;
  --avatar-frame-glow: rgba(111, 99, 255, 0.28);
  --avatar-frame-highlight: rgba(243, 239, 255, 0.88);
}

.avatar-rate-b {
  --avatar-frame-start: #cde7ff;
  --avatar-frame-end: #2f7ff5;
  --avatar-frame-glow: rgba(47, 127, 245, 0.26);
  --avatar-frame-highlight: rgba(236, 246, 255, 0.86);
}

.avatar-rate-c {
  --avatar-frame-start: #c8f2df;
  --avatar-frame-end: #1f9b68;
  --avatar-frame-glow: rgba(31, 155, 104, 0.24);
  --avatar-frame-highlight: rgba(239, 255, 248, 0.84);
}

.avatar-rate-d {
  --avatar-frame-start: #ffd8dd;
  --avatar-frame-end: #d85a67;
  --avatar-frame-glow: rgba(216, 90, 103, 0.24);
  --avatar-frame-highlight: rgba(255, 241, 243, 0.86);
}

.avatar-hover-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: rgba(15, 23, 42, 0.48);
  color: #fff;
  font-size: 14px;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.avatar-trigger:hover .avatar-hover-mask {
  opacity: 1;
}

.edit-profile-btn {
  min-width: 108px;
}

.profile-meta {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  text-align: left;
  align-self: center;
  padding-top: 10px;
}

.meta-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 12px;
}

.profile-name {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.25;
}

.rate-tag {
  height: 28px;
  padding: 0 12px;
  border-radius: 999px;
  font-weight: 600;
}

.profile-signature {
  margin: 0 0 14px;
  font-size: 15px;
  line-height: 1.8;
  color: #475569;
}

.signature-row {
  width: 100%;
  max-width: 460px;
  margin-bottom: 14px;
}

.signature-display {
  width: 100%;
  border: none;
  min-height: 38px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(59, 130, 246, 0.06);
  color: #475569;
  font-size: 13px;
  line-height: 1.7;
  cursor: text;
  text-align: left;
  display: flex;
  align-items: center;
}

.signature-input :deep(.el-input__wrapper) {
  min-height: 38px;
  padding: 0 10px;
  border-radius: 10px;
  background: rgba(59, 130, 246, 0.06);
  box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.16);
}

.signature-input :deep(.el-input__inner) {
  font-size: 13px;
  line-height: 1.7;
}

.meta-extra {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-start;
  gap: 10px 12px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 12px;
  background: rgba(148, 163, 184, 0.08);
}

.meta-icon {
  color: #64748b;
  font-size: 14px;
}

.meta-label {
  color: #94a3b8;
  font-size: 12px;
  letter-spacing: 0.02em;
}

.meta-value {
  color: #334155;
  font-size: 13px;
  font-weight: 600;
}

.meta-value-mono {
  font-variant-numeric: tabular-nums;
}

.profile-stats {
  display: grid;
  gap: 10px;
}

.stat-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 4px;
  padding: 14px 16px;
  border-radius: 18px;
  background: linear-gradient(145deg, #f8fbff, #eef5fb);
}

.stat-value {
  color: #1d4ed8;
  font-size: 22px;
  font-weight: 700;
  line-height: 1;
}

.stat-label {
  color: #64748b;
  font-size: 13px;
}

.profile-content {
  margin-top: 24px;
  padding: 24px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 18px 54px rgba(15, 23, 42, 0.08);
}

.history-toolbar {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}

.history-toolbar-left,
.history-toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.history-search {
  width: 280px;
}

.history-filter {
  width: 180px;
}

.layout-switcher :deep(.el-radio-button__inner) {
  min-width: 68px;
}

.page-size-select {
  width: 108px;
}

.history-summary {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 18px;
  color: #64748b;
  font-size: 13px;
  flex-wrap: wrap;
}

.history-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 18px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.history-card,
.history-row {
  border: none;
  border-radius: 24px;
  background: linear-gradient(180deg, #ffffff 0%, #f8fbff 100%);
}

.history-card-layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-row-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 20px;
  align-items: center;
}

.history-record-main {
  min-width: 0;
}

.history-card-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.history-card-title {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.history-card-headline {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.history-card-headline strong {
  color: #0f172a;
  font-size: 16px;
}

.history-card-side {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 10px;
}

.headline-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  color: #64748b;
  font-size: 12px;
}

.lang-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 38px;
  padding: 2px 10px;
  border-radius: 999px;
  background: rgba(59, 130, 246, 0.12);
  color: #2563eb;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.belong-tag {
  align-self: auto;
}

.history-card-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.history-text {
  margin: 0;
  color: #334155;
  line-height: 1.6;
  white-space: nowrap;
  overflow: hidden;
}

.record-audio {
  width: 100%;
}

.history-delete-icon {
  color: #ef4444;
  font-size: 18px;
  cursor: pointer;
  transition: transform 0.18s ease, color 0.18s ease;
}

.history-delete-icon:hover {
  color: #dc2626;
  transform: scale(1.08);
}

.history-pagination {
  display: flex;
  justify-content: center;
  margin-top: 22px;
}

.profile-empty {
  margin-top: 96px;
  padding: 48px 0;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 18px 54px rgba(15, 23, 42, 0.08);
}

.hidden-audio,
.hidden-file-input {
  display: none;
}

.profile-editor {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.editor-preview {
  border-radius: 24px;
  overflow: hidden;
}

.preview-banner {
  position: relative;
  display: flex;
  align-items: flex-end;
  height: 180px;
  padding: 18px 22px;
  background-position: center;
  background-size: cover;
}

.preview-banner::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, rgba(15, 23, 42, 0.08), rgba(15, 23, 42, 0.26));
}

.preview-avatar {
  position: relative;
  z-index: 1;
  border: 4px solid rgba(255, 255, 255, 0.92);
  box-shadow:
    0 14px 28px var(--avatar-frame-glow, rgba(15, 23, 42, 0.14)),
    0 0 0 4px var(--avatar-frame-start, #7c8aa5);
}

.editor-form-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.editor-form-row-wide {
  align-items: start;
}

.editor-form-item {
  width: 100%;
}

.editor-form-item.compact :deep(.el-select) {
  width: 100%;
}

.editor-form-item.compact :deep(.el-input.is-disabled .el-input__wrapper) {
  background: rgba(148, 163, 184, 0.08);
}

.full-width-field {
  width: 100%;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.cropper-dialog-body {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220px;
  gap: 20px;
  align-items: start;
}

.cropper-stage {
  min-height: 420px;
  border-radius: 24px;
  overflow: hidden;
  background:
    linear-gradient(135deg, rgba(148, 163, 184, 0.08), rgba(59, 130, 246, 0.08)),
    #f8fafc;
}

.cropper-image {
  display: block;
  max-width: 100%;
}

.cropper-stage-avatar :deep(.cropper-view-box),
.cropper-stage-avatar :deep(.cropper-face) {
  border-radius: 50%;
}

.cropper-stage :deep(.cropper-modal) {
  background: rgba(15, 23, 42, 0.38);
}

.cropper-stage :deep(.cropper-dashed) {
  border-color: rgba(255, 255, 255, 0.4);
}

.cropper-stage :deep(.cropper-line),
.cropper-stage :deep(.cropper-point) {
  opacity: 0;
  pointer-events: none;
}

.cropper-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 18px;
  border-radius: 22px;
  background: linear-gradient(180deg, #f8fbff 0%, #eef5fb 100%);
}

.cropper-panel-title {
  margin: 0;
  font-size: 18px;
  color: #0f172a;
}

.cropper-panel-tip {
  margin: 0;
  color: #64748b;
  font-size: 13px;
  line-height: 1.7;
}

.cropper-panel-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.78);
  color: #475569;
  font-size: 13px;
}

.cropper-panel-meta strong {
  color: #1d4ed8;
  font-size: 15px;
}

.cropper-slider-group,
.cropper-preview-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cropper-slider-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #475569;
  font-size: 13px;
}

.cropper-slider-head strong {
  color: #1d4ed8;
  font-size: 15px;
}

.cropper-preview-label {
  color: #475569;
  font-size: 13px;
  font-weight: 600;
}

.cropper-preview-avatar,
.cropper-preview-banner {
  background-position: center;
  background-size: cover;
  background-repeat: no-repeat;
  border: 1px solid rgba(148, 163, 184, 0.16);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.32);
}

.cropper-preview-avatar {
  width: 148px;
  height: 148px;
  align-self: center;
  border-radius: 50%;
  background-color: rgba(148, 163, 184, 0.12);
}

.cropper-preview-banner {
  width: 100%;
  min-height: 116px;
  border-radius: 18px;
  background-color: rgba(148, 163, 184, 0.12);
}

.cropper-stage :deep(.cropper-view-box) {
  outline: 2px solid rgba(255, 255, 255, 0.92);
  box-shadow: 0 0 0 9999px rgba(15, 23, 42, 0.22);
}

.profile-page {
  background:
    radial-gradient(circle at top left, rgba(111, 210, 202, 0.14), transparent 24%),
    radial-gradient(circle at top right, rgba(255, 216, 163, 0.14), transparent 22%),
    linear-gradient(180deg, #edf7f8 0%, #f8fbfd 26%, #ffffff 100%);
}

.profile-hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(7, 20, 31, 0.08), rgba(7, 20, 31, 0.42)),
    radial-gradient(circle at top right, rgba(158, 229, 224, 0.22), transparent 26%);
}

.profile-shell {
  width: min(1220px, calc(100% - 56px));
}

.profile-summary {
  border: 1px solid rgba(177, 220, 220, 0.56);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(243, 250, 250, 0.86));
  box-shadow:
    0 28px 64px rgba(35, 74, 92, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.82);
}

.edit-profile-btn {
  border-radius: 14px;
  border-color: rgba(166, 210, 212, 0.72);
  color: #21475b;
  background: rgba(255, 255, 255, 0.7);
}

.meta-item {
  background: rgba(255, 255, 255, 0.62);
  box-shadow: inset 0 0 0 1px rgba(179, 220, 222, 0.46);
}

.stat-card {
  border: 1px solid rgba(177, 218, 220, 0.48);
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.9), rgba(236, 246, 247, 0.92));
  box-shadow:
    0 16px 24px rgba(48, 88, 104, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.72);
}

.stat-value {
  color: #1e6179;
}

.profile-content {
  border: 1px solid rgba(180, 220, 221, 0.5);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.84), rgba(245, 251, 251, 0.92));
  box-shadow:
    0 24px 54px rgba(35, 74, 92, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.84);
}

.profile-tabs :deep(.el-tabs__header) {
  margin-bottom: 18px;
}

.profile-tabs :deep(.el-tabs__nav-wrap::after) {
  background: rgba(182, 219, 221, 0.46);
}

.profile-tabs :deep(.el-tabs__item) {
  color: #678391;
  font-weight: 600;
}

.profile-tabs :deep(.el-tabs__item.is-active) {
  color: #18465a;
}

.profile-tabs :deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 999px;
  background: linear-gradient(135deg, #66beb7, #ecb16f);
}

.history-toolbar {
  padding: 14px 16px;
  border-radius: 22px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.74), rgba(241, 249, 249, 0.82));
  box-shadow: inset 0 0 0 1px rgba(181, 219, 221, 0.46);
}

.history-search :deep(.el-input__wrapper),
.history-filter :deep(.el-select__wrapper),
.page-size-select :deep(.el-select__wrapper) {
  min-height: 42px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.84);
  box-shadow:
    0 10px 18px rgba(48, 88, 104, 0.06),
    inset 0 0 0 1px rgba(176, 214, 216, 0.56);
}

.layout-switcher :deep(.el-radio-button__inner) {
  border-radius: 14px;
  border-color: rgba(176, 214, 216, 0.56);
  background: rgba(255, 255, 255, 0.84);
  color: #5d7988;
  box-shadow: none;
}

.layout-switcher :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  color: #163e52;
  border-color: transparent;
  background: linear-gradient(135deg, rgba(128, 212, 204, 0.92), rgba(248, 204, 153, 0.92));
  box-shadow: 0 12px 20px rgba(98, 156, 163, 0.16);
}

.history-toolbar-right :deep(.el-button),
.profile-empty :deep(.el-button),
.dialog-footer :deep(.el-button) {
  border-radius: 14px;
}

.history-toolbar-right :deep(.el-button--primary),
.profile-empty :deep(.el-button--primary),
.dialog-footer :deep(.el-button--primary) {
  border: none;
  color: #123246;
  background: linear-gradient(135deg, #72c7c0, #efbc83);
  box-shadow: 0 14px 24px rgba(98, 156, 163, 0.16);
}

.history-card,
.history-row {
  border: 1px solid rgba(183, 219, 221, 0.48);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.88) 0%, rgba(244, 250, 251, 0.94) 100%);
  box-shadow:
    0 18px 28px rgba(35, 74, 92, 0.08),
    inset 0 1px 0 rgba(255, 255, 255, 0.84);
}

.history-card:hover,
.history-row:hover {
  transform: translateY(-1px);
}

.belong-tag {
  border: none;
  color: #1e6078;
  background: rgba(123, 209, 203, 0.18);
}

.profile-empty {
  border: 1px solid rgba(181, 219, 221, 0.46);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(243, 250, 250, 0.9));
}

.profile-editor-dialog :deep(.el-dialog),
.profile-cropper-dialog :deep(.el-dialog) {
  border-radius: 28px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(242, 249, 249, 0.98));
  box-shadow:
    0 28px 64px rgba(35, 74, 92, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.9);
}

.profile-editor-dialog :deep(.el-dialog__header),
.profile-cropper-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 24px 24px 8px;
}

.profile-editor-dialog :deep(.el-dialog__body),
.profile-cropper-dialog :deep(.el-dialog__body) {
  padding-top: 12px;
}

.editor-form :deep(.el-input__wrapper),
.editor-form :deep(.el-textarea__inner),
.editor-form :deep(.el-select__wrapper),
.editor-form :deep(.el-date-editor.el-input__wrapper) {
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.86);
  box-shadow:
    0 10px 18px rgba(48, 88, 104, 0.06),
    inset 0 0 0 1px rgba(176, 214, 216, 0.58);
}

@media (max-width: 1100px) {
  .profile-summary {
    grid-template-columns: 1fr;
  }

  .profile-stats {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .history-row-layout {
    grid-template-columns: 1fr;
  }

  .history-card-actions {
    justify-content: flex-start;
  }
}

@media (max-width: 768px) {
  .profile-shell {
    width: calc(100% - 28px);
  }

  .profile-hero {
    height: 300px;
    border-radius: 0 0 20px 20px;
  }

  .hero-back-btn {
    left: 20px;
    top: 20px;
  }

  .profile-summary,
  .profile-content {
    padding: 18px;
    border-radius: 22px;
  }

  .profile-name {
    font-size: 28px;
  }

  .signature-row {
    max-width: 100%;
  }

  .history-toolbar,
  .history-toolbar-left,
  .history-toolbar-right,
  .history-summary {
    flex-direction: column;
    align-items: stretch;
  }

  .history-search,
  .history-filter,
  .page-size-select {
    width: 100%;
  }

  .history-grid {
    grid-template-columns: 1fr;
  }

  .history-card-actions {
    flex-wrap: wrap;
    justify-content: flex-start;
  }

  .editor-form-row {
    grid-template-columns: 1fr;
  }

  .profile-stats {
    grid-template-columns: 1fr;
  }

  .cropper-dialog-body {
    grid-template-columns: 1fr;
  }

  .cropper-stage {
    min-height: 320px;
  }
}
</style>
