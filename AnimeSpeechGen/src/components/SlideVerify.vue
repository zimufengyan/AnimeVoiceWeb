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
      <div ref="stageWrapperRef" class="stage-wrapper">
        <canvas
          ref="backgroundCanvasRef"
          class="stage-canvas"
          :width="stageWidth"
          :height="stageHeight"
        ></canvas>

        <div
          v-if="targetBounds"
          class="target-highlight"
          :class="{ active: isDragging, success: status === 'success' }"
          :style="targetHighlightStyle"
        ></div>

        <canvas
          ref="pieceCanvasRef"
          class="piece-canvas"
          :width="pieceCanvasSize"
          :height="pieceCanvasSize"
          :style="pieceCanvasStyle"
        ></canvas>

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
          <CircleCheckFilled v-if="status === 'success'" class="slider-handle-icon success" />
          <DArrowRight v-else class="slider-handle-icon" />
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
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import {
  CircleCheckFilled,
  CircleCloseFilled,
  CloseBold,
  DArrowRight,
  Opportunity,
  RefreshRight,
  WarnTriangleFilled,
} from '@element-plus/icons-vue'

import slideImg from '@/assets/slideImgs/slideimg.png'
import slideImg1 from '@/assets/slideImgs/slideimg1.png'
import slideImg2 from '@/assets/slideImgs/slideimg2.png'
import slideImg3 from '@/assets/slideImgs/slideimg3.png'
import slideImg4 from '@/assets/slideImgs/slideimg4.png'
import slideImg5 from '@/assets/slideImgs/slideimg5.png'
import slideImg6 from '@/assets/slideImgs/slideimg6.png'
import slideImg7 from '@/assets/slideImgs/slideimg7.png'
import slideImg8 from '@/assets/slideImgs/slideimg8.png'
import slideImg9 from '@/assets/slideImgs/slideimg9.png'

type DragPoint = {
  x: number
  y: number
  time: number
}

type VerifyStatus = 'idle' | 'dragging' | 'fail' | 'warning' | 'success'

type PuzzleBounds = {
  left: number
  top: number
  size: number
}

type StageShape = {
  x: number
  y: number
  size: number
  protrusion: number
}

const props = withDefaults(
  defineProps<{
    w?: number
    h?: number
    accuracy?: number
    sliderText?: string
    imgs?: string[]
    showRefresh?: boolean
  }>(),
  {
    w: 600,
    h: 300,
    accuracy: 6,
    sliderText: '向右拖动拼图完成验证',
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

const backgroundCanvasRef = ref<HTMLCanvasElement | null>(null)
const pieceCanvasRef = ref<HTMLCanvasElement | null>(null)
const stageWrapperRef = ref<HTMLDivElement | null>(null)
const sliderTrackRef = ref<HTMLDivElement | null>(null)
const sliderHandleRef = ref<HTMLButtonElement | null>(null)

const stageWidth = ref(props.w)
const stageHeight = ref(props.h)
const puzzleBounds = ref<PuzzleBounds | null>(null)
const puzzleShape = ref<StageShape | null>(null)
const pieceLeft = ref(0)
const handleOffset = ref(0)
const isDragging = ref(false)
const isLoading = ref(true)
const status = ref<VerifyStatus>('idle')
const statusMessage = ref('拖动下方滑块，让拼图回到缺口处。')
const isRefreshing = ref(false)
const pieceCanvasSize = ref(0)

const sliderStartX = ref(0)
const handleStartOffset = ref(0)
const dragStartTime = ref(0)
const dragTrail = ref<DragPoint[]>([])
const currentImage = ref<HTMLImageElement | null>(null)

let resizeObserver: ResizeObserver | null = null
let refreshSpinTimer: ReturnType<typeof setTimeout> | null = null
let resetTimer: ReturnType<typeof setTimeout> | null = null

const defaultImages = [
  slideImg,
  slideImg1,
  slideImg2,
  slideImg3,
  slideImg4,
  slideImg5,
  slideImg6,
  slideImg7,
  slideImg8,
  slideImg9,
]

const imagePool = computed(() => (props.imgs && props.imgs.length ? props.imgs : defaultImages))
const normalizedAccuracy = computed(() => {
  const nextAccuracy = Number(props.accuracy || 6)
  return Number.isFinite(nextAccuracy) ? Math.min(10, Math.max(2, nextAccuracy)) : 6
})

const maxPieceTravel = computed(() => {
  if (!puzzleBounds.value) return 0
  return Math.max(stageWidth.value - puzzleBounds.value.size, 0)
})

const maxHandleTravel = computed(() => {
  const sliderWidth = sliderTrackRef.value?.clientWidth || stageWidth.value
  const handleWidth = sliderHandleRef.value?.offsetWidth || 72
  return Math.max(sliderWidth - handleWidth - 4, 0)
})

const progressWidth = computed(() => {
  const handleWidth = sliderHandleRef.value?.offsetWidth || 72
  return Math.min(handleOffset.value + handleWidth * 0.66, (sliderTrackRef.value?.clientWidth || 0))
})

const pieceCanvasStyle = computed(() => {
  if (!puzzleBounds.value) return {}
  return {
    width: `${puzzleBounds.value.size}px`,
    height: `${puzzleBounds.value.size}px`,
    transform: `translate(${pieceLeft.value}px, ${puzzleBounds.value.top}px)`,
    opacity: `${status.value === 'success' || isDragging.value || status.value === 'fail' || status.value === 'warning' ? 1 : 0.98}`,
  }
})

const targetHighlightStyle = computed(() => {
  if (!puzzleBounds.value) return {}
  return {
    width: `${puzzleBounds.value.size}px`,
    height: `${puzzleBounds.value.size}px`,
    transform: `translate(${puzzleBounds.value.left}px, ${puzzleBounds.value.top}px)`,
  }
})

const sliderTextDisplay = computed(() => {
  if (status.value === 'success') return '验证完成'
  if (status.value === 'fail') return '位置偏差过大，请重试'
  if (status.value === 'warning') return '请自然拖动后重试'
  return props.sliderText
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

const createStageImageCanvas = (image: HTMLImageElement) => {
  const canvas = document.createElement('canvas')
  canvas.width = stageWidth.value
  canvas.height = stageHeight.value
  const context = canvas.getContext('2d')

  if (!context) return canvas

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
  return canvas
}

const drawPuzzlePath = (context: CanvasRenderingContext2D, shape: StageShape) => {
  const { x, y, size, protrusion } = shape
  context.beginPath()
  context.moveTo(x, y)
  context.lineTo(x + size * 0.32, y)
  context.quadraticCurveTo(
    x + size * 0.38,
    y - protrusion,
    x + size * 0.5,
    y - protrusion * 0.9,
  )
  context.quadraticCurveTo(x + size * 0.62, y - protrusion, x + size * 0.68, y)
  context.lineTo(x + size, y)
  context.lineTo(x + size, y + size * 0.32)
  context.quadraticCurveTo(
    x + size + protrusion,
    y + size * 0.38,
    x + size + protrusion * 0.9,
    y + size * 0.5,
  )
  context.quadraticCurveTo(
    x + size + protrusion,
    y + size * 0.62,
    x + size,
    y + size * 0.68,
  )
  context.lineTo(x + size, y + size)
  context.lineTo(x + size * 0.68, y + size)
  context.quadraticCurveTo(
    x + size * 0.62,
    y + size + protrusion,
    x + size * 0.5,
    y + size + protrusion * 0.9,
  )
  context.quadraticCurveTo(
    x + size * 0.38,
    y + size + protrusion,
    x + size * 0.32,
    y + size,
  )
  context.lineTo(x, y + size)
  context.lineTo(x, y + size * 0.68)
  context.quadraticCurveTo(
    x - protrusion,
    y + size * 0.62,
    x - protrusion * 0.9,
    y + size * 0.5,
  )
  context.quadraticCurveTo(x - protrusion, y + size * 0.38, x, y + size * 0.32)
  context.closePath()
}

const drawStage = () => {
  if (!backgroundCanvasRef.value || !pieceCanvasRef.value || !currentImage.value || !puzzleShape.value || !puzzleBounds.value) {
    return
  }

  const backgroundContext = backgroundCanvasRef.value.getContext('2d')
  const pieceContext = pieceCanvasRef.value.getContext('2d')
  if (!backgroundContext || !pieceContext) return

  const stageImageCanvas = createStageImageCanvas(currentImage.value)
  backgroundContext.clearRect(0, 0, stageWidth.value, stageHeight.value)
  backgroundContext.drawImage(stageImageCanvas, 0, 0)

  backgroundContext.save()
  backgroundContext.fillStyle = 'rgba(6, 18, 32, 0.12)'
  backgroundContext.fillRect(0, 0, stageWidth.value, stageHeight.value)
  backgroundContext.restore()

  backgroundContext.save()
  const haloGradient = backgroundContext.createRadialGradient(
    puzzleShape.value.x + puzzleShape.value.size / 2,
    puzzleShape.value.y + puzzleShape.value.size / 2,
    puzzleShape.value.size * 0.18,
    puzzleShape.value.x + puzzleShape.value.size / 2,
    puzzleShape.value.y + puzzleShape.value.size / 2,
    puzzleShape.value.size * 0.72,
  )
  haloGradient.addColorStop(0, 'rgba(143, 223, 214, 0.32)')
  haloGradient.addColorStop(0.65, 'rgba(143, 223, 214, 0.12)')
  haloGradient.addColorStop(1, 'rgba(143, 223, 214, 0)')
  backgroundContext.fillStyle = haloGradient
  backgroundContext.fillRect(
    puzzleBounds.value.left - 24,
    puzzleBounds.value.top - 24,
    puzzleBounds.value.size + 48,
    puzzleBounds.value.size + 48,
  )
  backgroundContext.restore()

  backgroundContext.save()
  drawPuzzlePath(backgroundContext, puzzleShape.value)
  backgroundContext.fillStyle = 'rgba(7, 21, 34, 0.34)'
  backgroundContext.shadowColor = 'rgba(6, 18, 32, 0.24)'
  backgroundContext.shadowBlur = 22
  backgroundContext.fill()
  backgroundContext.restore()

  backgroundContext.save()
  drawPuzzlePath(backgroundContext, puzzleShape.value)
  backgroundContext.lineWidth = 1.6
  backgroundContext.strokeStyle = 'rgba(255, 255, 255, 0.72)'
  backgroundContext.stroke()
  backgroundContext.restore()

  pieceContext.clearRect(0, 0, pieceCanvasSize.value, pieceCanvasSize.value)
  pieceContext.save()
  drawPuzzlePath(pieceContext, {
    x: puzzleShape.value.protrusion,
    y: puzzleShape.value.protrusion,
    size: puzzleShape.value.size,
    protrusion: puzzleShape.value.protrusion,
  })
  pieceContext.clip()
  pieceContext.drawImage(
    stageImageCanvas,
    puzzleBounds.value.left,
    puzzleBounds.value.top,
    puzzleBounds.value.size,
    puzzleBounds.value.size,
    0,
    0,
    pieceCanvasSize.value,
    pieceCanvasSize.value,
  )
  pieceContext.restore()

  pieceContext.save()
  drawPuzzlePath(pieceContext, {
    x: puzzleShape.value.protrusion,
    y: puzzleShape.value.protrusion,
    size: puzzleShape.value.size,
    protrusion: puzzleShape.value.protrusion,
  })
  pieceContext.lineWidth = 2
  pieceContext.strokeStyle = 'rgba(255, 255, 255, 0.94)'
  pieceContext.shadowColor = 'rgba(8, 24, 38, 0.28)'
  pieceContext.shadowBlur = 14
  pieceContext.stroke()
  pieceContext.restore()

  pieceContext.save()
  drawPuzzlePath(pieceContext, {
    x: puzzleShape.value.protrusion,
    y: puzzleShape.value.protrusion,
    size: puzzleShape.value.size,
    protrusion: puzzleShape.value.protrusion,
  })
  pieceContext.lineWidth = 1
  pieceContext.strokeStyle = 'rgba(103, 171, 178, 0.34)'
  pieceContext.stroke()
  pieceContext.restore()
}

const resetPositionState = () => {
  handleOffset.value = 0
  pieceLeft.value = 0
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
  const imageSource = image || (await loadImage(imagePool.value[getRandomNumberByRange(0, imagePool.value.length - 1)]))
  currentImage.value = imageSource

  const pieceSize = Math.round(Math.min(Math.max(stageWidth.value * 0.14, 52), 64))
  const protrusion = Math.round(pieceSize * 0.14)
  const safePadding = pieceSize + protrusion + 18
  const puzzleX = getRandomNumberByRange(safePadding, stageWidth.value - safePadding - pieceSize)
  const puzzleY = getRandomNumberByRange(safePadding * 0.35, stageHeight.value - safePadding * 0.9 - pieceSize)

  puzzleShape.value = {
    x: puzzleX + protrusion,
    y: puzzleY + protrusion,
    size: pieceSize - protrusion * 2,
    protrusion,
  }

  pieceCanvasSize.value = pieceSize
  puzzleBounds.value = {
    left: puzzleX,
    top: puzzleY,
    size: pieceSize,
  }

  resetPositionState()
  drawStage()
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
    deltas.reduce((sum, delta) => sum + (delta - averageDelta) ** 2, 0) / Math.max(deltas.length, 1)

  if (duration < 140 && uniqueXSteps <= 2) return true
  if (duration < 220 && variance < 0.4 && deltas.length >= 2) return true
  return false
}

const pieceLeftFromHandle = (offset: number) => {
  if (maxHandleTravel.value === 0) return 0
  const ratio = offset / maxHandleTravel.value
  return ratio * maxPieceTravel.value
}

const handleOffsetFromPiece = (left: number) => {
  if (maxPieceTravel.value === 0) return 0
  const ratio = left / maxPieceTravel.value
  return ratio * maxHandleTravel.value
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
  if (!puzzleBounds.value) return
  const elapsed = performance.now() - dragStartTime.value
  pieceLeft.value = puzzleBounds.value.left
  handleOffset.value = handleOffsetFromPiece(puzzleBounds.value.left)
  syncStatus('success', `验证通过，用时 ${(elapsed / 1000).toFixed(1)} 秒。`)
  emit('success', elapsed)
}

const finishDrag = () => {
  if (!isDragging.value || !puzzleBounds.value) return

  isDragging.value = false
  const offsetDiff = Math.abs(pieceLeft.value - puzzleBounds.value.left)
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
  pieceLeft.value = pieceLeftFromHandle(nextOffset)
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

watch(
  () => [stageWidth.value, stageHeight.value],
  () => {
    if (currentImage.value && puzzleBounds.value) {
      drawStage()
    }
  },
)

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

.panel-copy {
  display: flex;
  flex-direction: column;
  gap: 0;
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
.panel-icon-btn:active {
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

.stage-canvas,
.piece-canvas {
  display: block;
}

.stage-canvas {
  width: 100%;
  height: auto;
}

.piece-canvas {
  position: absolute;
  left: 0;
  top: 0;
  z-index: 3;
  border-radius: 18px;
  background: transparent;
  pointer-events: none;
  filter: drop-shadow(0 16px 24px rgba(18, 42, 58, 0.22));
  transition:
    opacity 0.2s ease,
    transform 0.06s linear;
}

.target-highlight {
  position: absolute;
  left: 0;
  top: 0;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.62);
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.16),
    0 0 0 1px rgba(108, 192, 184, 0.16);
  background:
    radial-gradient(circle at center, rgba(155, 231, 223, 0.1), rgba(155, 231, 223, 0) 72%);
  pointer-events: none;
  animation: targetPulse 2.2s ease-in-out infinite;
}

.target-highlight.active {
  animation-duration: 1.5s;
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.28),
    0 0 0 1px rgba(108, 192, 184, 0.24),
    0 0 20px rgba(108, 192, 184, 0.16);
}

.target-highlight.success {
  animation: none;
  box-shadow:
    inset 0 0 0 1px rgba(255, 255, 255, 0.28),
    0 0 0 1px rgba(96, 206, 176, 0.28),
    0 0 24px rgba(96, 206, 176, 0.2);
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
  padding: 0 96px 0 96px;
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
  width: 72px;
  height: 54px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 18px;
  color: #12394b;
  background:
    linear-gradient(145deg, rgba(241, 251, 252, 0.98), rgba(205, 236, 236, 0.98));
  box-shadow:
    0 14px 24px rgba(44, 86, 106, 0.16),
    inset 0 0 0 1px rgba(142, 201, 205, 0.88);
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
    0 18px 28px rgba(44, 86, 106, 0.2),
    inset 0 0 0 1px rgba(121, 190, 194, 0.94);
}

.slider-handle.dragging {
  cursor: grabbing;
  background:
    linear-gradient(135deg, rgba(130, 214, 206, 0.94), rgba(248, 217, 171, 0.9));
}

.slider-handle:focus,
.slider-handle:focus-visible,
.slider-handle:active {
  outline: none;
}

.slider-handle-icon {
  display: block;
  width: 1.45rem;
  height: 1.45rem;
  color: currentColor;
}

.slider-handle-icon.success {
  width: 1.35rem;
  height: 1.35rem;
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

@keyframes targetPulse {
  0%,
  100% {
    opacity: 0.74;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.018);
  }
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
    padding: 0 84px;
    font-size: 13px;
  }

  .slider-handle {
    width: 64px;
    height: 48px;
    border-radius: 16px;
  }

  .status-row {
    width: 100%;
    justify-content: center;
  }
}
</style>
