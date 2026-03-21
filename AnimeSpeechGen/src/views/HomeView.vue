<template>
  <el-container class="background-container">
    <el-header class="el-header">
      <Header />
    </el-header>
    <el-main class="el-main app-scroll-container">
      <RouterView>
      </RouterView>

    </el-main>

  </el-container>
</template>

<script lang="ts" setup>
import Header from './Header.vue';


</script >

<style scoped>
.background-container {
  width: 100%;
  height: 100%;
}

.el-header {
  padding: 0;
}

.el-main.app-scroll-container {
  height: calc(100vh - 60px);
  overflow-y: auto;
  overflow-x: hidden;
  padding-top: 0.5rem;
  padding-bottom: 1rem;
}
</style>
