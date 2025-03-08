<template>
  <el-container class="background-container">
    <el-header class="el-header">
      <Header />
    </el-header>
    <el-main class="el-main">
      <RouterView>
      </RouterView>

    </el-main>

  </el-container>
</template>

<script lang="ts" setup>
import Header from './Header.vue';


</script >
