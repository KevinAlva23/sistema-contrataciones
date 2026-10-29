<script setup>
import { ref, computed, onMounted } from 'vue'
import Usuarios from './Usuarios.vue'

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
const vista = ref('candidatos')

const puedeEditar = computed(() => ['admin', 'reclutador'].includes(rol.value))
const puedeBorrar = computed(() => rol.value === 'admin')

// Contadores para las tarjetas de resumen
const total = computed(() => candidatos.value.length)
const cuenta = (e) => candidatos.value.filter(c => c.estado === e).length

async function api(url, opciones = {}) {
  const r = await fetch(url, {
    ...opciones,
    headers: { ...(opciones.headers || {}), Authorization: `Bearer ${token.value}` }
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
  localStorage.clear(); vista.value = 'candidatos'; vista.value = 'candidatos'
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
  <!-- Barra superior -->
  <header class="topbar">
    <div class="topbar-in">
      <div class="marca">
        Sistema de Contrataciones
        <small>Recursos Humanos</small>
      </div>
      <div v-if="token" class="sesion">
        <span class="usuario">{{ usuario }}</span>
        <span class="rol" :class="rol">{{ rol }}</span>
        <button v-if="rol === 'admin'" class="borde" @click="vista = vista === 'candidatos' ? 'usuarios' : 'candidatos'">{{ vista === 'candidatos' ? 'Usuarios' : 'Candidatos' }}</button>
        <button class="borde" @click="salir">Cerrar sesión</button>
      </div>
    </div>
  </header>

  <main class="contenedor">

    <!-- Login centrado -->
    <div v-if="!token" class="login-wrap">
      <form class="login" @submit.prevent="entrar">
        <h2>Iniciar sesión</h2>
        <p class="sub">Ingresa con tu cuenta asignada</p>
        <input v-model="loginForm.username" placeholder="Usuario" required />
        <input v-model="loginForm.password" type="password" placeholder="Contraseña" required />
        <button>Entrar</button>
        <p v-if="errorLogin" class="error">{{ errorLogin }}</p>
      </form>
    </div>

    <template v-else-if="vista === 'candidatos'">
      <!-- Tarjetas de resumen -->
      <section class="stats">
        <div class="stat">
          <div class="num">{{ total }}</div>
          <div class="lbl">Total de candidatos</div>
        </div>
        <div class="stat pend">
          <div class="num">{{ cuenta('pendiente') }}</div>
          <div class="lbl">Pendientes</div>
        </div>
        <div class="stat cont">
          <div class="num">{{ cuenta('contratado') }}</div>
          <div class="lbl">Contratados</div>
        </div>
        <div class="stat rech">
          <div class="num">{{ cuenta('rechazado') }}</div>
          <div class="lbl">Rechazados</div>
        </div>
      </section>

      <!-- Formulario (solo admin y reclutador) -->
      <section v-if="puedeEditar" class="panel">
        <h2 class="panel-titulo">
          {{ editandoId !== null ? 'Editar candidato' : 'Nuevo candidato' }}
        </h2>
        <form class="panel-cuerpo" @submit.prevent="guardar">
          <div class="grid-form">
            <input v-model="form.nombre" placeholder="Nombre" required />
            <input v-model="form.email" type="email" placeholder="Email" required />
            <input v-model="form.puesto" placeholder="Puesto" required />
            <input v-model="form.telefono" placeholder="Teléfono (10 dígitos)" required pattern="[0-9]{10}" title="Escribe 10 números" />
          </div>
          <div class="acciones-form">
            <button>{{ editandoId !== null ? 'Guardar cambios' : 'Agregar' }}</button>
            <button v-if="editandoId !== null" type="button" class="gris" @click="cancelar">Cancelar</button>
          </div>
          <p v-if="error" class="error">{{ error }}</p>
        </form>
      </section>

      <!-- Tabla con filtros -->
      <section class="panel">
        <h2 class="panel-titulo">Candidatos</h2>
        <div class="toolbar">
          <input v-model="busqueda" class="buscador" placeholder="Buscar por nombre, email o puesto" />
          <select v-model="filtro">
            <option value="todos">Todos los estados</option>
            <option value="pendiente">Pendiente</option>
            <option value="contratado">Contratado</option>
            <option value="rechazado">Rechazado</option>
          </select>
          <span class="cuenta">{{ filtrados.length }} resultado(s)</span>
        </div>

        <div class="tabla-scroll">
          <table>
            <thead>
              <tr>
                <th>Nombre</th><th>Email</th><th>Puesto</th>
                <th>Teléfono</th><th>Estado</th><th v-if="puedeEditar">Acciones</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!filtrados.length">
                <td colspan="6" class="vacio">Sin resultados</td>
              </tr>
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
                  <button v-if="puedeBorrar" class="rojo" @click="borrar(c)">Eliminar</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
    <Usuarios v-else :token="token" :yo="usuario" @salir="salir" />
  </main>

  <footer class="pie">Sistema de Contrataciones · Recursos Humanos</footer>
</template>
