<script setup>
import { ref } from 'vue'

const props = defineProps({ token: String, usuario: String })
const emit = defineEmits(['salir'])

const f = ref({ actual: '', nueva: '', repetir: '' })
const error = ref('')
const ok = ref('')

async function cambiar() {
  error.value = ''
  ok.value = ''
  if (f.value.nueva !== f.value.repetir) {
    error.value = 'Las contraseñas nuevas no coinciden'
    return
  }
  const r = await fetch('/api/cambiar-clave', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${props.token}`
    },
    body: JSON.stringify({ actual: f.value.actual, nueva: f.value.nueva })
  })
  if (r.status === 401) { emit('salir'); return }
  const d = await r.json()
  if (!r.ok) {
    error.value = typeof d.detail === 'string' ? d.detail : 'Datos inválidos'
    return
  }
  ok.value = 'Contraseña actualizada correctamente'
  f.value = { actual: '', nueva: '', repetir: '' }
}
</script>

<template>
  <section class="panel" style="max-width: 460px">
    <h2 class="panel-titulo">Mi cuenta: {{ usuario }}</h2>
    <form class="panel-cuerpo" @submit.prevent="cambiar">
      <div style="display: flex; flex-direction: column; gap: 10px">
        <input v-model="f.actual" type="password" placeholder="Contraseña actual" required autocomplete="current-password" />
        <input v-model="f.nueva" type="password" placeholder="Contraseña nueva" required minlength="10" autocomplete="new-password" />
        <input v-model="f.repetir" type="password" placeholder="Repetir contraseña nueva" required minlength="10" autocomplete="new-password" />
        <small style="color: var(--suave)">
          Mínimo 10 caracteres, con mayúscula, minúscula y número.
        </small>
        <button>Cambiar contraseña</button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="ok" style="color: var(--verde); font-weight: 600">{{ ok }}</p>
    </form>
  </section>
</template>
