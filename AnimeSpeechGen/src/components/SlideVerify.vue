<template>
  <div class="slide_box1">
    <el-button :icon="Close" size="default" class="slider-close-btn" circle @click="handleClose" />
    <div class="slide_innerbox">
      <slide-verify
        :w="600"
	      :h="300"
        class="slide_box"
        ref="block"
        slider-text="向右滑动"
        :accuracy="1"
        @again="onAgain"
        @success="onSuccess"
        @fail="onFail"
        @refresh="onRefresh"
        :imgs="img"
      ></slide-verify>
      <div class="msgbox" :style="'color:' + fontColor">{{ msg }}</div>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import SlideVerify from 'vue3-slide-verify' //引入滑动验证组件
import type { SlideVerifyInstance } from 'vue3-slide-verify'
import 'vue3-slide-verify/dist/style.css' //引入滑动验证组件样式

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
import { Close } from '@element-plus/icons-vue'

const msg = ref('')
//自定义图片
const img = ref([
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
])
const block = ref<SlideVerifyInstance>()
const emit = defineEmits(['again', 'success', 'fail', 'refresh', 'close'])

const fontColor = ref('')

const onAgain = () => {
  msg.value = '检测到非人为操作！'
  fontColor.value = 'red'
  // 刷新
  block.value?.refresh()
}
//成功的回调
const onSuccess = (times: number) => {
  msg.value = '验证通过，耗时' + (times / 1000).toFixed(1) + '秒'
  fontColor.value = 'green'
  emit('success')
}
const handleClose = () => {
  msg.value = ''
  emit('close')
}
//失败的回调
const onFail = () => {
  msg.value = '验证不通过'
  fontColor.value = 'red'

  setTimeout(() => {
    msg.value = ''
  }, 1000)
}
//点击刷新回调
const onRefresh = () => {
  msg.value = ''
}
</script>

<style scoped>
.slide_box1 {
  background: #fff;
  padding: 10px;
  position: absolute;
  z-index: 10000;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 600px;
  height: auto;
  min-height: 300px;
  max-height: 555px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  box-shadow: rgba(192, 196, 204, 0.6) 2px 2px 5px;
}
.slider-close-btn {
  z-index: 100;
  position: absolute;
  right: -10px;
  top: -10px;
}
.slide_innerbox {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.msgbox {
  font-size: 14px;
}
</style>
