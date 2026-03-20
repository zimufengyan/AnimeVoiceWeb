<template>
  <div class="home-div">
    <!-- 搜索框 -->
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

    <!-- 功能按钮列表 -->
    <div class="feature-grid">
      <div
        v-for="feature in features"
        :key="feature.name"
        class="feature-item"
        @click="navigateTo(feature.route)"
      >
        <div class="icon-container">
          <img :src="feature.icon" alt="feature-icon" class="feature-image" />
        </div>
        <span>{{ feature.name }}</span>
      </div>
    </div>

    <!-- 一言 -->
    <p id="hitokoto">
      <a :href="hitokitoHref" id="hitokoto_text">{{ hitokitoText }}</a>
    </p>
  </div>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { Icon } from '@iconify/vue'
import GenShinLogo from '@/assets/genshin_logo.jpg'
import StarRailLogo from '@/assets/starrail_logo.jpg'
import { getHiToKiToApi } from '@/api'

const hitokitoHref = ref('')
const hitokitoText = ref('')
const hitokitoCategories = ['a', 'b', 'c', 'd', 'h', 'i', 'k']
const timerId = ref<ReturnType<typeof setInterval> | null>(null)
const interval = 30 * 60 * 1000 // 1800000毫秒
const immediateExecution = true // 设为false则首次不立即执行

// import Icons from 'unplugin-icons/vite'
const handleOpen = (key: string, keyPath: string[]) => {
  console.log(key, keyPath)
}
const handleClose = (key: string, keyPath: string[]) => {
  console.log(key, keyPath)
}

const router = useRouter()
const searchQuery = ref('')

const getHiToKiTo = async () => {
  const randomKey = Math.floor(Math.random() * hitokitoCategories.length)
  var res = await getHiToKiToApi(hitokitoCategories[randomKey])
  hitokitoHref.value = res.href
  hitokitoText.value = res.text
}

// 启动定时器
const startTimer = () => {
  if (timerId.value) clearInterval(timerId.value)
  if (immediateExecution) getHiToKiTo()

  timerId.value = setInterval(() => {
    getHiToKiTo()
  }, interval)
}

// // 组件挂载时启动
// onMounted(startTimer)

// // 组件卸载时清理
// onUnmounted(() => {
//   if (timerId.value) {
//     clearInterval(timerId.value)
//     timerId.value = null
//   }
// })

// 功能列表数组
const features = ref([
  { name: '原神', icon: GenShinLogo, route: '/genshin' },
  { name: '崩坏·星穹铁道', icon: StarRailLogo, route: '/starrail' },
])

// 导航到指定页面
const navigateTo = (route: string) => {
  console.log(`navigate to route: ${route}`)
  router.push(route)
}

// 搜索建议
const querySearch = (
  queryString: string,
  cb: (results: Array<{ value: string; route: string }>) => void,
) => {
  const results = features.value
    .filter((feature) => feature.name.includes(queryString)) // 匹配输入内容
    .map((feature) => ({ value: feature.name, route: feature.route })) // 返回 name 和 route
  cb(results)
}

// 处理选择搜索结果
const handleSelect = (item: { route: string }) => {
  navigateTo(item.route)
}

// // 定义当前选中的背景类型
// const selectedMenu = ref('')
// // 根据选中的菜单项计算背景样式
// const backgroundStyle = computed(() => {
//   let backgroundUrl = ''
//   if (selectedMenu.value === 'genshin') {
//     backgroundUrl = 'url(/path/to/genshin-background.jpg)'
//   } else if (selectedMenu.value === 'starRail') {
//     backgroundUrl = 'url(/path/to/star-rail-background.jpg)'
//   }
//   return {
//     backgroundImage: backgroundUrl,
//     backgroundSize: 'cover',
//     backgroundPosition: 'center',
//     minHeight: '100vh',
//   }
// })

// // 设置选中的背景
// const setBackground = (menu) => {
//   selectedMenu.value = menu
// }
</script>

<style scoped>
.home-div {
  width: 100%;
  height: 100%;
  margin-top: 10%;
  /* margin-left: 20%; */
  /* margin-right: 20%; */
  margin-bottom: 5%;
}

::v-deep(.el-autocomplete) {
  width: 70%;
  display: flex;
  justify-self: center;
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
}

.feature-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  margin-top: 50px;
  gap: 20px;
}

.feature-item {
  width: calc(20% - 20px); /* 5 个按钮均分行宽，减去间隙 */
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  text-align: center;
}

.icon-container {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #3a86ff;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 10px;
}

.feature-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* @media (min-width: 1024px) {
  el-header {
    display: flex;
    place-items: center;
    padding-right: calc(var(--section-gap) / 2);
  }

  el-header .wrapper {
    display: flex;
    place-items: flex-start;
    flex-wrap: wrap;
  }
} */
</style>
