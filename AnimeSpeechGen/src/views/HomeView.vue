<template>
  <div class="app-shell">
    <Header />
    <main class="app-main app-scroll-container">
      <RouterView />
    </main>
  </div>
</template>

<script lang="ts" setup>
import Header from './Header.vue';
</script >

<style scoped>
.app-shell {
  width: 100%;
  height: 100%;
}

.app-main.app-scroll-container {
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  padding-top: 92px;
  padding-bottom: 1.25rem;
}
</style>
