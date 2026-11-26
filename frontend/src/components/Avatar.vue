<script setup>
import { computed } from "vue";
const props = defineProps({ nombre: { type: String, default: "" }, grande: Boolean });
const ini = computed(() =>
  props.nombre.split(" ").slice(0, 2).map((p) => p[0]).join("").toUpperCase(),
);
const tono = computed(() => [...props.nombre].reduce((a, c) => a + c.charCodeAt(0), 0) % 360);
</script>

<template>
  <span class="avatar" :class="{ grande }" :style="{ '--h': tono }" aria-hidden="true">{{ ini }}</span>
</template>
