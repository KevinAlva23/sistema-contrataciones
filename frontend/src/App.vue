<script setup>
import { ref, computed, onMounted } from 'vue'
import Usuarios from './Usuarios.vue'
import Bitacora from './Bitacora.vue'
import Estadisticas from './Estadisticas.vue'
import MiCuenta from './MiCuenta.vue'

const token = ref(localStorage.getItem('token') || '')
const usuario = ref(localStorage.getItem('usuario') || '')
const rol = ref(localStorage.getItem('rol') || '')
const loginForm = ref({ username: '', password: '' })
const errorLogin = ref('')
const vista = ref('candidatos')

const candidatos = ref([])
const filtro = ref('todos')
const busqueda = ref('')
const form = ref({ nombre: '', email: '', puesto: '', telefono: '' })
const editandoId = ref(null)
const error = ref('')

const puedeEditar = computed(() => ['admin', 'reclutador'].includes(rol.value))
const puedeBorrar = computed(() => rol.value === 'admin')
const puedeBitacora = computed(() => ['admin', 'auditor'].includes(rol.value))

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
  vista.value = 'candidatos'
  cargar()
}

function salir() {
  token.value = ''; usuario.value = ''; rol.value = ''
  candidatos.value = []
  vista.value = 'candidatos'
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

async function exportar() {
  try {
    const r = await api('/api/candidatos/exportar')
    if (!r.ok) { error.value = 'No se pudo exportar'; return }
    const blob = await r.blob()
    const a = document.createElement('a')
    a.href = URL.createObjectURL(blob)
    a.download = 'candidatos.csv'
    a.click()
    URL.revokeObjectURL(a.href)
  } catch (e) {}
}

onMounted(cargar)
</script>

<template>
  <a class="saltar" href="#contenido">Saltar al contenido</a>
  <header class="topbar">
    <div class="topbar-in">
      <div class="marca">
        Sistema de Contrataciones
        <small>Recursos Humanos</small>
      </div>
      <div v-if="token" class="sesion">
        <span class="usuario">{{ usuario }}</span>
        <span class="rol" :class="rol">{{ rol }}</span>
        <button class="borde" @click="salir">Cerrar sesión</button>
      </div>
    </div>
  </header>

  <main id="contenido" class="contenedor" tabindex="-1">

    <!-- Login -->
    <div v-if="!token" class="login-wrap">
      <form class="login" @submit.prevent="entrar">
        <h2>Iniciar sesión</h2>
        <p class="sub">Ingresa con tu cuenta asignada</p>
        <input aria-label="Usuario" v-model="loginForm.username" placeholder="Usuario" required />
        <input aria-label="Contraseña" v-model="loginForm.password" type="password" placeholder="Contraseña" required />
        <button>Entrar</button>
        <p v-if="errorLogin" class="error" role="alert">{{ errorLogin }}</p>
      </form>
    </div>

    <template v-else>
      <!-- Pestañas -->
      <nav class="nav" aria-label="Secciones">
        <button :class="{ activo: vista === 'candidatos' }" :aria-current="vista === 'candidatos' ? 'page' : undefined" @click="vista = 'candidatos'">Candidatos</button>
        <button v-if="rol === 'admin'" :class="{ activo: vista === 'usuarios' }" :aria-current="vista === 'usuarios' ? 'page' : undefined" @click="vista = 'usuarios'">Usuarios</button>
        <button v-if="puedeBitacora" :class="{ activo: vista === 'estadisticas' }" :aria-current="vista === 'estadisticas' ? 'page' : undefined" @click="vista = 'estadisticas'">Estadísticas</button>
        <button v-if="puedeBitacora" :class="{ activo: vista === 'bitacora' }" :aria-current="vista === 'bitacora' ? 'page' : undefined" @click="vista = 'bitacora'">Bitácora</button>
        <button :class="{ activo: vista === 'cuenta' }" :aria-current="vista === 'cuenta' ? 'page' : undefined" @click="vista = 'cuenta'">Mi cuenta</button>
      </nav>

      <!-- Vista: candidatos -->
      <template v-if="vista === 'candidatos'">
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

        <section v-if="puedeEditar" class="panel">
          <h2 class="panel-titulo">
            {{ editandoId !== null ? 'Editar candidato' : 'Nuevo candidato' }}
          </h2>
          <form class="panel-cuerpo" @submit.prevent="guardar">
            <div class="grid-form">
              <input aria-label="Nombre" v-model="form.nombre" placeholder="Nombre" required />
              <input aria-label="Email" v-model="form.email" type="email" placeholder="Email" required />
              <input aria-label="Puesto" v-model="form.puesto" placeholder="Puesto" required />
              <input aria-label="Teléfono (10 dígitos)" v-model="form.telefono" placeholder="Teléfono (10 dígitos)" required pattern="[0-9]{10}" title="Escribe 10 números" />
            </div>
            <div class="acciones-form">
              <button>{{ editandoId !== null ? 'Guardar cambios' : 'Agregar' }}</button>
              <button v-if="editandoId !== null" type="button" class="gris" @click="cancelar">Cancelar</button>
            </div>
            <p v-if="error" class="error" role="alert">{{ error }}</p>
          </form>
        </section>

        <section class="panel">
          <h2 class="panel-titulo">Candidatos</h2>
          <div class="toolbar">
            <input aria-label="Buscar por nombre, email o puesto" v-model="busqueda" class="buscador" placeholder="Buscar por nombre, email o puesto" />
            <select v-model="filtro" aria-label="Filtrar por estado">
              <option value="todos">Todos los estados</option>
              <option value="pendiente">Pendiente</option>
              <option value="contratado">Contratado</option>
              <option value="rechazado">Rechazado</option>
            </select>
            <span class="cuenta">{{ filtrados.length }} resultado(s)</span>
            <button v-if="puedeBitacora" class="gris" @click="exportar">Exportar CSV</button>
          </div>
          <div class="tabla-scroll">
            <table>
              <caption class="solo-lector">Lista de candidatos</caption>
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
                    <button class="verde" :aria-label="`Contratar a ${c.nombre}`" @click="estado(c.id,'contratado')">Contratar</button>
                    <button class="rojo" :aria-label="`Rechazar a ${c.nombre}`" @click="estado(c.id,'rechazado')">Rechazar</button>
                    <button class="gris" :aria-label="`Editar a ${c.nombre}`" @click="editar(c)">Editar</button>
                    <button v-if="puedeBorrar" class="rojo" :aria-label="`Eliminar a ${c.nombre}`" @click="borrar(c)">Eliminar</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>

      <!-- Vista: usuarios (admin) -->
      <Usuarios v-else-if="vista === 'usuarios' && rol === 'admin'" :token="token" :yo="usuario" @salir="salir" />

      <!-- Vista: bitácora (admin y auditor) -->
      <Estadisticas v-else-if="vista === 'estadisticas' && puedeBitacora" :token="token" @salir="salir" />

      <Bitacora v-else-if="vista === 'bitacora' && puedeBitacora" :token="token" @salir="salir" />

      <!-- Vista: mi cuenta (todos los roles) -->
      <MiCuenta v-else-if="vista === 'cuenta'" :token="token" :usuario="usuario" @salir="salir" />
    </template>
  </main>

  <footer class="pie">Sistema de Contrataciones · Recursos Humanos</footer>
</template>
