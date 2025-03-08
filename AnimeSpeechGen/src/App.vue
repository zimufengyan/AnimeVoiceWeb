<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { Icon } from '@iconify/vue'
import Header from '@/views/Header.vue'
import { CloudDownloadOutlined } from '@ant-design/icons-vue';
import type { DrawerProps } from 'element-plus'
import { ElMessageBox } from 'element-plus'
import { ref } from 'vue';

const open = ref<boolean>(false);
const showDrawer = () => {
  open.value = true;
};

const onClose = () => {
  open.value = false;
};

const drawer = ref(false)
const direction = ref<DrawerProps['direction']>('rtl')
const radio1 = ref('Option 1')


function cancelClick() {
  drawer.value = false
}

function confirmClick() {
  ElMessageBox.confirm(`Are you confirm to chose ${radio1.value} ?`)
    .then(() => {
      drawer.value = false
    })
    .catch(() => {
      // catch error
    })
}

const handleClose = (done: () => void) => {
  ElMessageBox.confirm('Are you sure you want to close this?')
    .then(() => {
      done()
    })
    .catch(() => {
      // catch error
    })
}
</script>

<template>

  <RouterView />
  <a-float-button-group shape="circle" :style="{ right: '100px' }">
    <a-float-button tooltip="语音生成记录"  @click="showDrawer">
      <template #icon>
        <CloudDownloadOutlined />
      </template>
    </a-float-button>
    <a-back-top :visibility-height="0" />
  </a-float-button-group>

  <!-- <el-drawer
    v-model="drawer"
    :direction="direction"
    :before-close="handleClose"
  >
    <template #header>
      <h4>set title by slot</h4>
    </template>
    <template #default>
      <div>
        <el-radio v-model="radio1" value="Option 1" size="large"> Option 1 </el-radio>
        <el-radio v-model="radio1" value="Option 2" size="large"> Option 2 </el-radio>
      </div>
    </template>
    <template #footer>
      <div style="flex: auto">
        <el-button @click="cancelClick">cancel</el-button>
        <el-button type="primary" @click="confirmClick">confirm</el-button>
      </div>
    </template>
  </el-drawer> -->
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
    <p>Some contents...</p>
    <p>Some contents...</p>
    <p>Some contents...</p>
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
