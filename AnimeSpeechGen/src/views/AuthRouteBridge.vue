<template>
  <div class="auth-bridge"></div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { openAuthDialog, type AuthDialogMode } from '@/composables/useAuthDialog'

const props = defineProps<{
  mode: AuthDialogMode
}>()

const route = useRoute()
const router = useRouter()

const resolveBridgeTarget = () => {
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
  if (!redirect || redirect.startsWith('/login') || redirect.startsWith('/register') || redirect.startsWith('/forgot-password')) {
    return '/'
  }
  return redirect
}

onMounted(async () => {
  const redirectTo = resolveBridgeTarget()
  openAuthDialog(props.mode, { redirectTo })
  await router.replace(redirectTo)
})
</script>

<style scoped>
.auth-bridge {
  display: none;
}
</style>
