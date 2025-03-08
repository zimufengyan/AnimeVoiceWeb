<template>
  <div style="display: grid; place-items: center;">
    <el-carousel :autoplay="false" arrow="always" type="card" indicator-position="none">
      <el-carousel-item v-for="(url, name) in imageMap" :key="name">
        <img :src="url" no-repeat style="object-fit: fill;height:100%; width:100%;" />
      </el-carousel-item>
    </el-carousel>
  </div>
</template>



<script setup lang="ts">
import {defineProps } from 'vue'

const props = defineProps({
  imageMap: {
      type: Object,
      required: true,
    },
});

</script>
<style scoped>
.el-carousel {
  width: 100%;

  min-height: 750px;
  margin-left: 5%;
}

.el-carousel__item img {
  display: flex;
  min-width: 450px;
  min-height: 732px;
  opacity: 1;
  margin: 0;
  justify-self: center
}

::v-deep(.el-carousel__container) {
  height: 100%
}
</style>
