<script setup>
import { toasts } from './toast.js'
</script>

<template>
  <div class="toasts" aria-live="polite" role="status">
    <div v-for="t in toasts" :key="t.id" class="toast" :class="t.tipo">{{ t.texto }}</div>
  </div>
</template>
