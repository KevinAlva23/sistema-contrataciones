<script setup>
import { ref, computed, onMounted } from 'vue'

const token = ref(localStorage.getItem('token') || '')
const usuario = ref(localStorage.getItem('usuario') || '')
const rol = ref(localStorage.getItem('rol') || '')
const loginForm = ref({ username: '', password: '' })
const errorLogin = ref('')

const candidatos = ref([])
const filtro = ref('todos')
const busqueda = ref('')
const form = ref({ nombre: '', email: '', puesto: '', telefono: '' })
const editandoId = ref(null)
const error = ref('')

const puedeEditar = computed(() => ['admin', 'reclutador'].includes(rol.value))
const puedeBorrar = computed(() => rol.value === 'admin')

// fetch que agrega el token; si expira, cierra la sesión
async function api(url, opciones = {}) {
  const r = await fetch(url, {
    ...opciones,
    headers: {
      ...(opciones.headers || {}),
      Authorization: `Bearer ${token.value}`
    }
  })
  if (r.status === 401) { salir(); throw new Error('sesion') }
  return r
}

async function entrar() {
  errorLogin.value = ''
  const r = await fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(loginForm.value)
  })
  if (!r.ok) {
    const d = await r.json()
    errorLogin.value = d.detail || 'No se pudo iniciar sesión'
    return
  }
  const d = await r.json()
  token.value = d.token
  usuario.value = d.username
  rol.value = d.rol
  localStorage.setItem('token', d.token)
  localStorage.setItem('usuario', d.username)
  localStorage.setItem('rol', d.rol)
  loginForm.value = { username: '', password: '' }
  cargar()
}

function salir() {
  token.value = ''; usuario.value = ''; rol.value = ''
  candidatos.value = []
  localStorage.clear()
}

const filtrados = computed(() => {
  const texto = busqueda.value.trim().toLowerCase()
  return candidatos.value.filter(c => {
    const okEstado = filtro.value === 'todos' || c.estado === filtro.value
    const okTexto = !texto ||
      c.nombre.toLowerCase().includes(texto) ||
      c.email.toLowerCase().includes(texto) ||
      c.puesto.toLowerCase().includes(texto)
    return okEstado && okTexto
  })
})

async function cargar() {
  if (!token.value) return
  try {
    const r = await api('/api/candidatos')
    candidatos.value = await r.json()
  } catch (e) {}
}

async function guardar() {
  const editando = editandoId.value !== null
  const url = editando ? `/api/candidatos/${editandoId.value}` : '/api/candidatos'
  try {
    const r = await api(url, {
      method: editando ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(form.value)
    })
    if (!r.ok) {
      const d = await r.json()
      error.value = typeof d.detail === 'string' ? d.detail : 'Datos inválidos'
      return
    }
    error.value = ''
    cancelar()
    cargar()
  } catch (e) {}
}

function editar(c) {
  form.value = { nombre: c.nombre, email: c.email, puesto: c.puesto, telefono: c.telefono }
  editandoId.value = c.id
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelar() {
  form.value = { nombre: '', email: '', puesto: '', telefono: '' }
  editandoId.value = null
}

async function estado(id, e) {
  try { await api(`/api/candidatos/${id}?estado=${e}`, { method: 'PATCH' }); cargar() } catch (x) {}
}

async function borrar(c) {
  if (!confirm(`¿Eliminar a ${c.nombre}? Esta acción no se puede deshacer.`)) return
  try { await api(`/api/candidatos/${c.id}`, { method: 'DELETE' }); cargar() } catch (x) {}
}

onMounted(cargar)
</script>

<template>
  <main class="contenedor">
    <h1>Sistema de Contrataciones</h1>

    <!-- Pantalla de login -->
    <form v-if="!token" class="tarjeta formulario" @submit.prevent="entrar">
      <input v-model="loginForm.username" placeholder="Usuario" required />
      <input v-model="loginForm.password" type="password" placeholder="Contraseña" required />
      <button>Entrar</button>
      <p v-if="errorLogin" class="error">{{ errorLogin }}</p>
    </form>

    <template v-else>
      <div class="filtro">
        <span>Sesión: <b>{{ usuario }}</b> ({{ rol }})</span>
        <button class="gris" @click="salir">Cerrar sesión</button>
      </div>

      <form v-if="puedeEditar" class="tarjeta formulario" @submit.prevent="guardar">
        <input v-model="form.nombre" placeholder="Nombre" required />
        <input v-model="form.email" type="email" placeholder="Email" required />
        <input v-model="form.puesto" placeholder="Puesto" required />
        <input v-model="form.telefono" placeholder="Teléfono (10 dígitos)" required pattern="[0-9]{10}" title="Escribe 10 números" />
        <button>{{ editandoId !== null ? 'Guardar cambios' : 'Agregar' }}</button>
        <button v-if="editandoId !== null" type="button" class="gris" @click="cancelar">Cancelar</button>
      </form>
      <p v-if="error" class="error">{{ error }}</p>

      <div class="filtro">
        <input v-model="busqueda" class="buscador" placeholder="Buscar por nombre, email o puesto" />
        <label>Estado:</label>
        <select v-model="filtro">
          <option value="todos">Todos</option>
          <option value="pendiente">Pendiente</option>
          <option value="contratado">Contratado</option>
          <option value="rechazado">Rechazado</option>
        </select>
        <span>{{ filtrados.length }} candidato(s)</span>
      </div>

      <div class="tarjeta tabla-scroll">
        <table>
          <thead>
            <tr>
              <th>Nombre</th><th>Email</th><th>Puesto</th>
              <th>Teléfono</th><th>Estado</th><th v-if="puedeEditar">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!filtrados.length"><td colspan="6">Sin resultados</td></tr>
            <tr v-for="c in filtrados" :key="c.id">
              <td>{{ c.nombre }}</td>
              <td>{{ c.email }}</td>
              <td>{{ c.puesto }}</td>
              <td>{{ c.telefono }}</td>
              <td><span class="estado" :class="c.estado">{{ c.estado }}</span></td>
              <td v-if="puedeEditar" class="acciones">
                <button class="verde" @click="estado(c.id,'contratado')">Contratar</button>
                <button class="rojo" @click="estado(c.id,'rechazado')">Rechazar</button>
                <button class="gris" @click="editar(c)">Editar</button>
                <button v-if="puedeBorrar" @click="borrar(c)">Eliminar</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>
  </main>
</template>
