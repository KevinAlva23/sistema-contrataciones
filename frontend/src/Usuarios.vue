<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({ token: String, yo: String })
const emit = defineEmits(['salir'])

const usuarios = ref([])
const nuevo = ref({ username: '', password: '', rol: 'reclutador' })
const error = ref('')

async function api(url, opciones = {}) {
  const r = await fetch(url, {
    ...opciones,
    headers: { ...(opciones.headers || {}), Authorization: `Bearer ${props.token}` }
  })
  if (r.status === 401) { emit('salir'); throw new Error('sesion') }
  return r
}

// Devuelve true si la respuesta fue correcta; si no, muestra el error
async function revisar(r) {
  if (r.ok) { error.value = ''; return true }
  const d = await r.json()
  error.value = typeof d.detail === 'string' ? d.detail : 'Datos inválidos'
  return false
}

async function cargar() {
  try {
    const r = await api('/api/usuarios')
    usuarios.value = await r.json()
  } catch (e) {}
}

async function crear() {
  try {
    const r = await api('/api/usuarios', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(nuevo.value)
    })
    if (await revisar(r)) {
      nuevo.value = { username: '', password: '', rol: 'reclutador' }
    }
    cargar()
  } catch (e) {}
}

async function cambiar(u, datos) {
  try {
    const r = await api(`/api/usuarios/${u.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datos)
    })
    await revisar(r)
    cargar()
  } catch (e) {}
}

const alternar = (u) => cambiar(u, { activo: !u.activo })
const cambiarRol = (u, e) => cambiar(u, { rol: e.target.value })

function restablecer(u) {
  const p = prompt(`Nueva contraseña para ${u.username} (mínimo 8 caracteres):`)
  if (p) cambiar(u, { password: p })
}

async function borrar(u) {
  if (!confirm(`¿Eliminar la cuenta de ${u.username}?`)) return
  try {
    const r = await api(`/api/usuarios/${u.id}`, { method: 'DELETE' })
    await revisar(r)
    cargar()
  } catch (e) {}
}

onMounted(cargar)
</script>

<template>
  <section class="panel">
    <h2 class="panel-titulo">Nuevo usuario</h2>
    <form class="panel-cuerpo" @submit.prevent="crear">
      <div class="grid-form">
        <input v-model="nuevo.username" placeholder="Usuario" required />
        <input v-model="nuevo.password" type="password" placeholder="Contraseña (mín. 8)" required minlength="8" />
        <select v-model="nuevo.rol">
          <option value="admin">admin</option>
          <option value="reclutador">reclutador</option>
          <option value="auditor">auditor</option>
        </select>
        <button>Crear usuario</button>
      </div>
    </form>
  </section>

  <p v-if="error" class="error">{{ error }}</p>

  <section class="panel">
    <h2 class="panel-titulo">Usuarios ({{ usuarios.length }})</h2>
    <div class="tabla-scroll">
      <table>
        <thead>
          <tr><th>Usuario</th><th>Rol</th><th>Estado</th><th>Acciones</th></tr>
        </thead>
        <tbody>
          <tr v-for="u in usuarios" :key="u.id">
            <td>{{ u.username }} <small v-if="u.username === yo">(tú)</small></td>
            <td>
              <select :value="u.rol" :disabled="u.username === yo" @change="cambiarRol(u, $event)">
                <option value="admin">admin</option>
                <option value="reclutador">reclutador</option>
                <option value="auditor">auditor</option>
              </select>
            </td>
            <td>
              <span class="estado" :class="u.activo ? 'contratado' : 'rechazado'">
                {{ u.activo ? 'activo' : 'inactivo' }}
              </span>
            </td>
            <td class="acciones">
              <button class="gris" :disabled="u.username === yo" @click="alternar(u)">
                {{ u.activo ? 'Desactivar' : 'Activar' }}
              </button>
              <button class="gris" @click="restablecer(u)">Restablecer clave</button>
              <button class="rojo" :disabled="u.username === yo" @click="borrar(u)">Eliminar</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
