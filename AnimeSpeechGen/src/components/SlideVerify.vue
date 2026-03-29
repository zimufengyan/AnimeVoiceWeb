<template>
  <div class="slide-verify-panel">
    <div class="panel-head">
      <div class="panel-copy">
        <h3>安全检验</h3>
      </div>

      <div class="panel-actions">
        <button
          v-if="showRefresh"
          type="button"
          class="panel-icon-btn"
          :class="{ spinning: isRefreshing }"
          @click="handleRefreshClick"
        >
          <RefreshRight class="panel-icon" />
        </button>
        <button type="button" class="panel-icon-btn close-btn" @click="handleClose">
          <CloseBold class="panel-icon" />
        </button>
      </div>
    </div>

    <div class="stage-shell">
      <div
        ref="stageWrapperRef"
        class="stage-wrapper"
        :style="{ height: `${stageHeight}px` }"
      >
        <img
          v-if="stageImageUrl"
          class="stage-image"
          :src="stageImageUrl"
          alt="验证拼图底图"
          draggable="false"
        />

        <svg
          v-if="slotPathD"
          class="slot-overlay"
          :viewBox="`0 0 ${stageWidth} ${stageHeight}`"
          :width="stageWidth"
          :height="stageHeight"
          aria-hidden="true"
        >
          <defs>
            <filter :id="slotGlowId" x="-40%" y="-40%" width="180%" height="180%">
              <feGaussianBlur stdDeviation="6" result="blurred" />
              <feColorMatrix
                in="blurred"
                type="matrix"
                values="1 0 0 0 0
                        0 1 0 0 0
                        0 0 1 0 0
                        0 0 0 0.28 0"
              />
            </filter>
          </defs>

          <path
            class="slot-halo"
            :class="{ active: isDragging, success: status === 'success' }"
            :d="slotPathD"
            :filter="`url(#${slotGlowId})`"
          />
          <path class="slot-cutout" :d="slotPathD" />
          <path class="slot-outline" :d="slotPathD" />
          <path class="slot-outline soft" :d="slotPathD" />
        </svg>

        <svg
          v-if="stageImageUrl && piecePathD && slotBounds"
          class="piece-svg"
          :style="pieceStyle"
          :viewBox="`0 0 ${pieceSize} ${pieceSize}`"
          :width="pieceSize"
          :height="pieceSize"
          aria-hidden="true"
        >
          <defs>
            <clipPath :id="pieceClipId">
              <path :d="piecePathD" />
            </clipPath>
          </defs>

          <image
            :href="stageImageUrl"
            :x="-slotBounds.left"
            :y="-slotBounds.top"
            :width="stageWidth"
            :height="stageHeight"
            preserveAspectRatio="none"
            :clip-path="`url(#${pieceClipId})`"
          />
          <path class="piece-stroke" :d="piecePathD" />
          <path class="piece-stroke soft" :d="piecePathD" />
        </svg>

        <div v-if="isLoading" class="stage-loading">
          <RefreshRight class="stage-loading-icon" />
          <span>载入验证拼图中</span>
        </div>
      </div>
    </div>

    <div class="slider-shell" :class="[`is-${status}`, { dragging: isDragging }]">
      <div ref="sliderTrackRef" class="slider-track">
        <div class="slider-progress" :style="{ width: `${progressWidth}px` }"></div>
        <span class="slider-track-text">{{ sliderTextDisplay }}</span>

        <button
          ref="sliderHandleRef"
          type="button"
          class="slider-handle"
          :class="{ dragging: isDragging }"
          :style="{ transform: `translateX(${handleOffset}px)` }"
          @mousedown.prevent="startDrag"
          @touchstart.prevent="startDrag"
        >
          <span class="slider-handle-core">
            <CircleCheckFilled v-if="status === 'success'" class="slider-handle-icon success" />
            <span v-else class="slider-handle-arrow-stack" aria-hidden="true">
              <DArrowRight class="slider-handle-icon" />
              <DArrowRight class="slider-handle-icon trailing" />
            </span>
          </span>
          <span class="slider-handle-grip" aria-hidden="true">
            <span></span>
            <span></span>
          </span>
        </button>
      </div>
    </div>

    <div class="status-row" :class="`status-${status}`">
      <CircleCheckFilled v-if="status === 'success'" class="status-icon" />
      <CircleCloseFilled v-else-if="status === 'fail'" class="status-icon" />
      <WarnTriangleFilled v-else-if="status === 'warning'" class="status-icon" />
      <Opportunity v-else class="status-icon" />
      <span>{{ statusMessage }}</span>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  CircleCheckFilled,
  CircleCloseFilled,
  CloseBold,
  DArrowRight,
  Opportunity,
  RefreshRight,
  WarnTriangleFilled,
} from '@element-plus/icons-vue'

import {
  slideVerifyImageGroups,
  type SlideVerifyImageGroup,
} from '@/config/slideVerifyImages'

type DragPoint = {
  x: number
  y: number
  time: number
}

type VerifyStatus = 'idle' | 'dragging' | 'fail' | 'warning' | 'success'

type SlotBounds = {
  left: number
  top: number
  size: number
  protrusion: number
  innerSize: number
}

const props = withDefaults(
  defineProps<{
    w?: number
    h?: number
    accuracy?: number
    sliderText?: string
    imgs?: string[]
    imageGroup?: SlideVerifyImageGroup
    showRefresh?: boolean
  }>(),
  {
    w: 600,
    h: 300,
    accuracy: 6,
    sliderText: '向右拖动拼图完成验证',
    imageGroup: 'default',
    showRefresh: true,
  },
)

const emit = defineEmits<{
  success: [times: number]
  again: []
  fail: []
  refresh: []
  close: []
}>()

const stageWrapperRef = ref<HTMLDivElement | null>(null)
const sliderTrackRef = ref<HTMLDivElement | null>(null)
const sliderHandleRef = ref<HTMLButtonElement | null>(null)

const stageWidth = ref(props.w)
const stageHeight = ref(props.h)
const stageImageUrl = ref('')
const currentImage = ref<HTMLImageElement | null>(null)
const slotBounds = ref<SlotBounds | null>(null)

const handleOffset = ref(0)
const pieceX = ref(0)
const isDragging = ref(false)
const isLoading = ref(true)
const isRefreshing = ref(false)
const status = ref<VerifyStatus>('idle')
const statusMessage = ref('拖动下方滑块，让拼图回到缺口处。')

const sliderStartX = ref(0)
const handleStartOffset = ref(0)
const dragStartTime = ref(0)
const dragTrail = ref<DragPoint[]>([])

const instanceKey = Math.random().toString(36).slice(2, 10)
const slotGlowId = `slide-slot-glow-${instanceKey}`
const pieceClipId = `slide-piece-clip-${instanceKey}`

let resizeObserver: ResizeObserver | null = null
let refreshSpinTimer: ReturnType<typeof setTimeout> | null = null
let resetTimer: ReturnType<typeof setTimeout> | null = null

const imagePool = computed(() => {
  if (props.imgs?.length) return props.imgs
  return slideVerifyImageGroups[props.imageGroup] || slideVerifyImageGroups.default
})

const normalizedAccuracy = computed(() => {
  const nextAccuracy = Number(props.accuracy || 6)
  return Number.isFinite(nextAccuracy) ? Math.min(10, Math.max(2, nextAccuracy)) : 6
})

const pieceStartX = computed(() => {
  return Math.max(12, Math.min(18, Math.round(stageWidth.value * 0.03)))
})

const pieceSize = computed(() => slotBounds.value?.size || 0)

const pieceTravel = computed(() => {
  if (!slotBounds.value) return 0
  return Math.max(slotBounds.value.left - pieceStartX.value, 0)
})

const maxHandleTravel = computed(() => {
  const sliderWidth = sliderTrackRef.value?.clientWidth || stageWidth.value
  const handleWidth = sliderHandleRef.value?.offsetWidth || 86
  const trackLimit = Math.max(sliderWidth - handleWidth - 4, 0)
  return Math.min(trackLimit, pieceTravel.value)
})

const progressWidth = computed(() => {
  const handleWidth = sliderHandleRef.value?.offsetWidth || 86
  return Math.min(handleOffset.value + handleWidth * 0.66, sliderTrackRef.value?.clientWidth || 0)
})

const pieceStyle = computed(() => {
  if (!slotBounds.value) return {}
  return {
    width: `${slotBounds.value.size}px`,
    height: `${slotBounds.value.size}px`,
    transform: `translate(${pieceX.value}px, ${slotBounds.value.top}px)`,
    opacity: '1',
  }
})

const sliderTextDisplay = computed(() => {
  if (status.value === 'success') return '验证完成'
  if (status.value === 'fail') return '位置偏差过大，请重试'
  if (status.value === 'warning') return '请自然拖动后重试'
  return props.sliderText
})

const buildPuzzlePathD = (left: number, top: number, innerSize: number, protrusion: number) => {
  const x = left + protrusion
  const y = top + protrusion
  const size = innerSize

  return [
    `M ${x} ${y}`,
    `L ${x + size * 0.32} ${y}`,
    `Q ${x + size * 0.38} ${y - protrusion} ${x + size * 0.5} ${y - protrusion * 0.9}`,
    `Q ${x + size * 0.62} ${y - protrusion} ${x + size * 0.68} ${y}`,
    `L ${x + size} ${y}`,
    `L ${x + size} ${y + size * 0.32}`,
    `Q ${x + size + protrusion} ${y + size * 0.38} ${x + size + protrusion * 0.9} ${y + size * 0.5}`,
    `Q ${x + size + protrusion} ${y + size * 0.62} ${x + size} ${y + size * 0.68}`,
    `L ${x + size} ${y + size}`,
    `L ${x + size * 0.68} ${y + size}`,
    `Q ${x + size * 0.62} ${y + size + protrusion} ${x + size * 0.5} ${y + size + protrusion * 0.9}`,
    `Q ${x + size * 0.38} ${y + size + protrusion} ${x + size * 0.32} ${y + size}`,
    `L ${x} ${y + size}`,
    `L ${x} ${y + size * 0.68}`,
    `Q ${x - protrusion} ${y + size * 0.62} ${x - protrusion * 0.9} ${y + size * 0.5}`,
    `Q ${x - protrusion} ${y + size * 0.38} ${x} ${y + size * 0.32}`,
    'Z',
  ].join(' ')
}

const slotPathD = computed(() => {
  if (!slotBounds.value) return ''
  return buildPuzzlePathD(
    slotBounds.value.left,
    slotBounds.value.top,
    slotBounds.value.innerSize,
    slotBounds.value.protrusion,
  )
})

const piecePathD = computed(() => {
  if (!slotBounds.value) return ''
  return buildPuzzlePathD(0, 0, slotBounds.value.innerSize, slotBounds.value.protrusion)
})

const clearResetTimer = () => {
  if (resetTimer) {
    clearTimeout(resetTimer)
    resetTimer = null
  }
}

const stopRefreshSpin = () => {
  if (refreshSpinTimer) {
    clearTimeout(refreshSpinTimer)
    refreshSpinTimer = null
  }
  isRefreshing.value = false
}

const getClientPoint = (event: MouseEvent | TouchEvent) => {
  if ('touches' in event) {
    const touch = event.touches[0] || event.changedTouches[0]
    return { x: touch?.clientX || 0, y: touch?.clientY || 0 }
  }

  return { x: event.clientX, y: event.clientY }
}

const getRandomNumberByRange = (start: number, end: number) => {
  if (end <= start) return start
  return Math.round(Math.random() * (end - start) + start)
}

const loadImage = (src: string) =>
  new Promise<HTMLImageElement>((resolve, reject) => {
    const image = new Image()
    image.crossOrigin = 'anonymous'
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error('拼图背景加载失败'))
    image.src = src
  })

const renderStageImage = (image: HTMLImageElement) => {
  const canvas = document.createElement('canvas')
  canvas.width = stageWidth.value
  canvas.height = stageHeight.value
  const context = canvas.getContext('2d')
  if (!context) return ''

  const canvasAspectRatio = stageWidth.value / stageHeight.value
  const imageAspectRatio = image.width / image.height

  let drawWidth = stageWidth.value
  let drawHeight = stageHeight.value
  let offsetX = 0
  let offsetY = 0

  if (imageAspectRatio > canvasAspectRatio) {
    drawHeight = stageHeight.value
    drawWidth = drawHeight * imageAspectRatio
    offsetX = (stageWidth.value - drawWidth) / 2
  } else {
    drawWidth = stageWidth.value
    drawHeight = drawWidth / imageAspectRatio
    offsetY = (stageHeight.value - drawHeight) / 2
  }

  context.drawImage(image, offsetX, offsetY, drawWidth, drawHeight)
  return canvas.toDataURL('image/png')
}

const resetPositionState = () => {
  handleOffset.value = 0
  pieceX.value = pieceStartX.value
  isDragging.value = false
  dragTrail.value = []
  sliderStartX.value = 0
  handleStartOffset.value = 0
}

const syncStatus = (nextStatus: VerifyStatus, nextMessage: string) => {
  status.value = nextStatus
  statusMessage.value = nextMessage
}

const buildChallenge = async (image?: HTMLImageElement | null) => {
  if (!imagePool.value.length) {
    throw new Error('未配置任何拼图图片')
  }

  const imageSource =
    image ||
    (await loadImage(imagePool.value[getRandomNumberByRange(0, imagePool.value.length - 1)]))
  currentImage.value = imageSource
  stageImageUrl.value = renderStageImage(imageSource)

  const size = Math.round(Math.min(Math.max(stageWidth.value * 0.14, 54), 66))
  const protrusion = Math.round(size * 0.14)
  const innerSize = size - protrusion * 2
  const safePadding = size + protrusion + 18
  const minSlotLeft = Math.max(pieceStartX.value + size + 34, safePadding)
  const maxSlotLeft = stageWidth.value - safePadding - size
  const slotLeft = getRandomNumberByRange(minSlotLeft, maxSlotLeft)
  const slotTop = getRandomNumberByRange(
    Math.round(safePadding * 0.35),
    stageHeight.value - Math.round(safePadding * 0.9) - size,
  )

  slotBounds.value = {
    left: slotLeft,
    top: slotTop,
    size,
    protrusion,
    innerSize,
  }

  resetPositionState()
  syncStatus('idle', '拖动下方滑块，让拼图回到缺口处。')
}

const refresh = async (shouldEmit = true) => {
  clearResetTimer()
  stopRefreshSpin()
  isRefreshing.value = true
  isLoading.value = true

  try {
    await buildChallenge()
    if (shouldEmit) {
      emit('refresh')
    }
  } catch (error: unknown) {
    syncStatus('fail', error instanceof Error ? error.message : '拼图加载失败，请刷新重试。')
  } finally {
    isLoading.value = false
    refreshSpinTimer = setTimeout(() => {
      stopRefreshSpin()
    }, 320)
  }
}

const verifyHumanTrail = () => {
  if (dragTrail.value.length < 2) return false
  const duration = performance.now() - dragStartTime.value
  const deltas = dragTrail.value
    .slice(1)
    .map((point, index) => point.x - dragTrail.value[index].x)
    .filter((delta) => Number.isFinite(delta))

  const uniqueXSteps = new Set(dragTrail.value.map((point) => Math.round(point.x))).size
  const averageDelta = deltas.reduce((sum, delta) => sum + delta, 0) / Math.max(deltas.length, 1)
  const variance =
    deltas.reduce((sum, delta) => sum + (delta - averageDelta) ** 2, 0) /
    Math.max(deltas.length, 1)

  if (duration < 140 && uniqueXSteps <= 2) return true
  if (duration < 220 && variance < 0.4 && deltas.length >= 2) return true
  return false
}

const pieceXFromHandle = (offset: number) => {
  if (pieceTravel.value === 0) return pieceStartX.value
  return pieceStartX.value + Math.min(offset, pieceTravel.value)
}

const handleOffsetFromPiece = (x: number) => {
  if (pieceTravel.value === 0) return 0
  return Math.max(0, Math.min(x - pieceStartX.value, maxHandleTravel.value))
}

const queueReset = (message: string, nextStatus: VerifyStatus, emitType: 'fail' | 'again') => {
  syncStatus(nextStatus, message)
  clearResetTimer()
  resetTimer = setTimeout(() => {
    resetPositionState()
    syncStatus('idle', '拖动下方滑块，让拼图回到缺口处。')
  }, 820)

  if (emitType === 'fail') {
    emit('fail')
  } else {
    emit('again')
  }
}

const completeVerification = () => {
  if (!slotBounds.value) return
  const elapsed = performance.now() - dragStartTime.value
  pieceX.value = slotBounds.value.left
  handleOffset.value = handleOffsetFromPiece(slotBounds.value.left)
  syncStatus('success', `验证通过，用时 ${(elapsed / 1000).toFixed(1)} 秒。`)
  emit('success', elapsed)
}

const finishDrag = () => {
  if (!isDragging.value || !slotBounds.value) return

  isDragging.value = false
  const offsetDiff = Math.abs(pieceX.value - slotBounds.value.left)
  const suspicious = verifyHumanTrail()

  if (offsetDiff <= normalizedAccuracy.value) {
    if (suspicious) {
      queueReset('轨迹异常，请自然拖动后重试。', 'warning', 'again')
      return
    }

    completeVerification()
    return
  }

  queueReset('差一点点，再对准缺口试一次。', 'fail', 'fail')
}

const updateDragOffset = (clientX: number, clientY: number) => {
  if (!isDragging.value) return
  const nextOffset = Math.min(
    Math.max(handleStartOffset.value + clientX - sliderStartX.value, 0),
    maxHandleTravel.value,
  )
  handleOffset.value = nextOffset
  pieceX.value = pieceXFromHandle(nextOffset)
  dragTrail.value.push({
    x: nextOffset,
    y: clientY,
    time: performance.now(),
  })
}

const handleWindowMove = (event: MouseEvent | TouchEvent) => {
  const point = getClientPoint(event)
  updateDragOffset(point.x, point.y)
}

const handleWindowEnd = () => {
  finishDrag()
  removeDragListeners()
}

const removeDragListeners = () => {
  window.removeEventListener('mousemove', handleWindowMove)
  window.removeEventListener('mouseup', handleWindowEnd)
  window.removeEventListener('touchmove', handleWindowMove)
  window.removeEventListener('touchend', handleWindowEnd)
}

const addDragListeners = () => {
  window.addEventListener('mousemove', handleWindowMove, { passive: true })
  window.addEventListener('mouseup', handleWindowEnd, { passive: true })
  window.addEventListener('touchmove', handleWindowMove, { passive: false })
  window.addEventListener('touchend', handleWindowEnd, { passive: true })
}

const startDrag = (event: MouseEvent | TouchEvent) => {
  if (status.value === 'success' || isLoading.value) return

  clearResetTimer()
  const point = getClientPoint(event)
  isDragging.value = true
  sliderStartX.value = point.x
  handleStartOffset.value = handleOffset.value
  dragStartTime.value = performance.now()
  dragTrail.value = [
    {
      x: handleOffset.value,
      y: point.y,
      time: dragStartTime.value,
    },
  ]
  syncStatus('dragging', '保持匀速拖动，让拼图靠近缺口。')
  addDragListeners()
}

const handleRefreshClick = async () => {
  await refresh(true)
}

const handleClose = () => {
  removeDragListeners()
  clearResetTimer()
  stopRefreshSpin()
  syncStatus('idle', '')
  emit('close')
}

const syncStageSize = async () => {
  const wrapperWidth = stageWrapperRef.value?.clientWidth || props.w
  const nextWidth = Math.max(320, Math.min(props.w, Math.round(wrapperWidth)))
  const nextHeight = Math.round((nextWidth / props.w) * props.h)

  const widthChanged = nextWidth !== stageWidth.value || nextHeight !== stageHeight.value
  stageWidth.value = nextWidth
  stageHeight.value = nextHeight

  if (!widthChanged || !currentImage.value) return
  await nextTick()
  await buildChallenge(currentImage.value)
}

onMounted(async () => {
  await nextTick()
  resizeObserver = new ResizeObserver(() => {
    void syncStageSize()
  })
  if (stageWrapperRef.value) {
    resizeObserver.observe(stageWrapperRef.value)
  }
  await syncStageSize()
  await refresh(false)
})

onBeforeUnmount(() => {
  removeDragListeners()
  resizeObserver?.disconnect()
  stopRefreshSpin()
  clearResetTimer()
})

defineExpose({
  refresh,
})
</script>

<style scoped>
.slide-verify-panel {
  position: absolute;
  inset: 50% auto auto 50%;
  transform: translate(-50%, -50%);
  z-index: 10000;
  width: min(640px, calc(100vw - 28px));
  padding: 22px 22px 20px;
  border-radius: 30px;
  border: 1px solid rgba(171, 215, 216, 0.56);
  background:
    radial-gradient(circle at top left, rgba(206, 241, 241, 0.86), transparent 32%),
    linear-gradient(180deg, rgba(249, 252, 253, 0.96), rgba(239, 247, 248, 0.98));
  box-shadow:
    0 30px 70px rgba(28, 61, 79, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.82);
  backdrop-filter: blur(24px);
}

.slide-verify-panel::before {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background:
    linear-gradient(135deg, rgba(109, 196, 188, 0.12), transparent 38%),
    radial-gradient(circle at bottom right, rgba(247, 206, 148, 0.16), transparent 24%);
  pointer-events: none;
}

.panel-head,
.stage-shell,
.slider-shell,
.status-row {
  position: relative;
  z-index: 1;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.panel-copy h3 {
  margin: 0;
  color: #17384b;
  font-size: 24px;
  font-weight: 800;
  line-height: 1.15;
}

.panel-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-icon-btn {
  width: 42px;
  height: 42px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  border: none;
  border-radius: 15px;
  color: #447280;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.82), rgba(243, 249, 250, 0.74));
  box-shadow:
    0 10px 20px rgba(44, 86, 106, 0.08),
    inset 0 0 0 1px rgba(173, 216, 218, 0.52);
  cursor: pointer;
  transition:
    transform 0.2s ease,
    color 0.2s ease,
    box-shadow 0.2s ease;
  appearance: none;
  -webkit-appearance: none;
}

.panel-icon-btn:hover {
  color: #1e4c62;
  transform: translateY(-1px);
  box-shadow:
    0 14px 24px rgba(44, 86, 106, 0.12),
    inset 0 0 0 1px rgba(173, 216, 218, 0.64);
}

.panel-icon-btn:focus,
.panel-icon-btn:focus-visible,
.panel-icon-btn:active,
.slider-handle:focus,
.slider-handle:focus-visible,
.slider-handle:active {
  outline: none;
}

.panel-icon {
  display: block;
  width: 1.15rem;
  height: 1.15rem;
  color: currentColor;
}

.panel-icon-btn.spinning .panel-icon {
  animation: spinRefresh 0.36s ease-in-out;
}

.close-btn {
  color: #5f7b88;
}

.stage-shell {
  padding: 14px;
  border-radius: 26px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.74), rgba(243, 250, 251, 0.76));
  box-shadow: inset 0 0 0 1px rgba(183, 221, 222, 0.44);
}

.stage-wrapper {
  position: relative;
  width: 100%;
  border-radius: 22px;
  overflow: hidden;
  background:
    linear-gradient(135deg, rgba(15, 31, 42, 0.06), rgba(33, 68, 90, 0.12)),
    #f6fbfc;
}

.stage-image,
.slot-overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.stage-image {
  display: block;
  object-fit: cover;
  user-select: none;
}

.slot-overlay {
  pointer-events: none;
}

.slot-halo {
  fill: rgba(143, 223, 214, 0.22);
  transition: fill 0.18s ease;
}

.slot-halo.active {
  fill: rgba(143, 223, 214, 0.28);
}

.slot-halo.success {
  fill: rgba(104, 205, 177, 0.26);
}

.slot-cutout {
  fill: rgba(7, 21, 34, 0.34);
}

.slot-outline {
  fill: none;
  stroke: rgba(255, 255, 255, 0.84);
  stroke-width: 2;
  stroke-linejoin: round;
}

.slot-outline.soft {
  stroke: rgba(103, 171, 178, 0.42);
  stroke-width: 1;
}

.piece-svg {
  position: absolute;
  left: 0;
  top: 0;
  z-index: 3;
  pointer-events: none;
  filter: drop-shadow(0 18px 28px rgba(18, 42, 58, 0.26));
  transition:
    opacity 0.2s ease,
    transform 0.06s linear;
}

.piece-stroke {
  fill: none;
  stroke: rgba(255, 255, 255, 0.92);
  stroke-width: 2;
  stroke-linejoin: round;
}

.piece-stroke.soft {
  stroke: rgba(103, 171, 178, 0.32);
  stroke-width: 1;
}

.stage-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #426a79;
  font-size: 14px;
  background: rgba(246, 251, 252, 0.78);
  backdrop-filter: blur(10px);
}

.stage-loading-icon {
  width: 1.08rem;
  height: 1.08rem;
  animation: spinRefresh 0.9s linear infinite;
}

.slider-shell {
  position: relative;
  z-index: 1;
  margin-top: 16px;
}

.slider-track {
  position: relative;
  display: flex;
  align-items: center;
  height: 62px;
  padding: 0 4px;
  border-radius: 22px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(235, 245, 247, 0.9));
  box-shadow:
    inset 0 0 0 1px rgba(162, 208, 210, 0.68),
    0 14px 24px rgba(44, 86, 106, 0.1);
  overflow: visible;
}

.slider-progress {
  position: absolute;
  inset: 4px auto 4px 4px;
  border-radius: 18px;
  background:
    linear-gradient(135deg, rgba(108, 196, 188, 0.24), rgba(247, 206, 148, 0.26));
  transition: width 0.08s linear;
}

.slider-track-text {
  position: relative;
  z-index: 1;
  width: 100%;
  padding: 0 112px 0 112px;
  color: #5c7c89;
  font-size: 14px;
  font-weight: 600;
  text-align: center;
  letter-spacing: 0.01em;
  user-select: none;
  pointer-events: none;
}

.slider-handle {
  position: absolute;
  left: 4px;
  top: 4px;
  z-index: 2;
  width: 86px;
  height: 54px;
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 0 16px 0 18px;
  border: none;
  border-radius: 18px;
  color: #12394b;
  background:
    linear-gradient(145deg, rgba(245, 252, 252, 0.99), rgba(199, 233, 234, 0.99));
  box-shadow:
    0 16px 26px rgba(44, 86, 106, 0.2),
    inset 0 0 0 1px rgba(126, 194, 198, 0.98);
  cursor: grab;
  transition:
    transform 0.12s linear,
    box-shadow 0.2s ease,
    background 0.2s ease;
  touch-action: none;
  appearance: none;
  -webkit-appearance: none;
}

.slider-handle:hover,
.slider-handle.dragging {
  box-shadow:
    0 20px 32px rgba(44, 86, 106, 0.24),
    inset 0 0 0 1px rgba(106, 183, 188, 1);
}

.slider-handle.dragging {
  cursor: grabbing;
  background:
    linear-gradient(135deg, rgba(130, 214, 206, 0.94), rgba(248, 217, 171, 0.9));
}

.slider-handle-core {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
}

.slider-handle-arrow-stack {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.slider-handle-icon {
  display: block;
  width: 1.5rem;
  height: 1.5rem;
  color: currentColor;
  filter: drop-shadow(0 1px 0 rgba(255, 255, 255, 0.28));
}

.slider-handle-icon.success {
  width: 1.35rem;
  height: 1.35rem;
}

.slider-handle-icon.trailing {
  margin-left: -10px;
  opacity: 0.66;
}

.slider-handle-grip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding-left: 10px;
  border-left: 1px solid rgba(88, 151, 158, 0.28);
}

.slider-handle-grip span {
  display: block;
  width: 3px;
  height: 18px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(84, 142, 148, 0.66), rgba(123, 183, 188, 0.9));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.36);
}

.slider-shell.is-success .slider-progress {
  background: linear-gradient(135deg, rgba(104, 205, 177, 0.3), rgba(143, 235, 210, 0.22));
}

.slider-shell.is-success .slider-handle {
  color: #ffffff;
  background: linear-gradient(135deg, #58c6a5, #72d3bb);
}

.slider-shell.is-fail .slider-progress,
.slider-shell.is-warning .slider-progress {
  background: linear-gradient(135deg, rgba(248, 178, 164, 0.3), rgba(255, 220, 213, 0.22));
}

.slider-shell.is-fail .slider-handle,
.slider-shell.is-warning .slider-handle {
  color: #ffffff;
  background: linear-gradient(135deg, #ef9d8f, #f6b7a9);
}

.status-row {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  padding: 10px 14px;
  border-radius: 16px;
  color: #4f6f7d;
  font-size: 13px;
  font-weight: 600;
  background: rgba(255, 255, 255, 0.52);
  box-shadow: inset 0 0 0 1px rgba(183, 220, 222, 0.44);
}

.status-row.status-success {
  color: #228261;
  background: rgba(226, 248, 239, 0.88);
}

.status-row.status-fail {
  color: #b85f53;
  background: rgba(255, 239, 235, 0.9);
}

.status-row.status-warning {
  color: #9a6a4d;
  background: rgba(255, 246, 231, 0.9);
}

.status-row.status-dragging {
  color: #296778;
  background: rgba(235, 247, 248, 0.88);
}

.status-icon {
  width: 1rem;
  height: 1rem;
  flex-shrink: 0;
}

@keyframes spinRefresh {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(180deg);
  }
}

@media (max-width: 768px) {
  .slide-verify-panel {
    width: calc(100vw - 20px);
    padding: 18px 16px 16px;
    border-radius: 26px;
  }

  .panel-copy h3 {
    font-size: 22px;
  }

  .stage-shell {
    padding: 10px;
    border-radius: 22px;
  }

  .slider-track {
    height: 56px;
  }

  .slider-track-text {
    padding: 0 92px;
    font-size: 13px;
  }

  .slider-handle {
    width: 76px;
    height: 48px;
    padding: 0 12px 0 14px;
    border-radius: 16px;
  }

  .status-row {
    width: 100%;
    justify-content: center;
  }
}
</style>
