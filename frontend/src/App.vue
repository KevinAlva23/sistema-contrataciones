<script setup>
import { ref, computed, onMounted } from 'vue'

const candidatos = ref([])
const filtro = ref('todos')
// Texto escrito en el cuadro de búsqueda
const busqueda = ref('')
const form = ref({ nombre: '', email: '', puesto: '', telefono: '' })
const editandoId = ref(null)
const error = ref('')

// Lista mostrada: primero filtra por estado, luego por el texto buscado
const filtrados = computed(() => {
  const texto = busqueda.value.trim().toLowerCase()
  return candidatos.value.filter(c => {
    const coincideEstado = filtro.value === 'todos' || c.estado === filtro.value
    const coincideTexto =
      !texto ||
      c.nombre.toLowerCase().includes(texto) ||
      c.email.toLowerCase().includes(texto) ||
      c.puesto.toLowerCase().includes(texto)
    return coincideEstado && coincideTexto
  })
})

async function cargar() {
  const r = await fetch('/api/candidatos')
  candidatos.value = await r.json()
}

async function guardar() {
  const editando = editandoId.value !== null
  const url = editando ? `/api/candidatos/${editandoId.value}` : '/api/candidatos'
  const r = await fetch(url, {
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
}

function editar(c) {
  form.value = {
    nombre: c.nombre,
    email: c.email,
    puesto: c.puesto,
    telefono: c.telefono
  }
  editandoId.value = c.id
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelar() {
  form.value = { nombre: '', email: '', puesto: '', telefono: '' }
  editandoId.value = null
}

async function estado(id, e) {
  await fetch(`/api/candidatos/${id}?estado=${e}`, { method: 'PATCH' })
  cargar()
}

// Pide confirmación antes de borrar; si el usuario cancela, no hace nada
async function borrar(c) {
  if (!confirm(`¿Eliminar a ${c.nombre}? Esta acción no se puede deshacer.`)) return
  await fetch(`/api/candidatos/${c.id}`, { method: 'DELETE' })
  cargar()
}

onMounted(cargar)
</script>

<template>
  <main class="contenedor">
    <h1>Sistema de Contrataciones</h1>

    <form class="tarjeta formulario" @submit.prevent="guardar">
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
            <th>Teléfono</th><th>Estado</th><th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!filtrados.length">
            <td colspan="6">Sin resultados</td>
          </tr>
          <tr v-for="c in filtrados" :key="c.id">
            <td>{{ c.nombre }}</td>
            <td>{{ c.email }}</td>
            <td>{{ c.puesto }}</td>
            <td>{{ c.telefono }}</td>
            <td><span class="estado" :class="c.estado">{{ c.estado }}</span></td>
            <td class="acciones">
              <button class="verde" @click="estado(c.id,'contratado')">Contratar</button>
              <button class="rojo" @click="estado(c.id,'rechazado')">Rechazar</button>
              <button class="gris" @click="editar(c)">Editar</button>
              <button @click="borrar(c)">Eliminar</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </main>
</template>
