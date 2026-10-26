<script setup>
import { ref, computed, onMounted } from 'vue'

const candidatos = ref([])
const filtro = ref('todos')
const form = ref({ nombre: '', email: '', puesto: '', telefono: '' })

// id del candidato que se está editando (null = estamos agregando uno nuevo)
const editandoId = ref(null)

const filtrados = computed(() =>
  filtro.value === 'todos'
    ? candidatos.value
    : candidatos.value.filter(c => c.estado === filtro.value)
)

async function cargar() {
  const r = await fetch('/api/candidatos')
  candidatos.value = await r.json()
}

// Se ejecuta al enviar el formulario: crea o edita según editandoId
async function guardar() {
  const editando = editandoId.value !== null
  const url = editando ? `/api/candidatos/${editandoId.value}` : '/api/candidatos'
  await fetch(url, {
    method: editando ? 'PUT' : 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(form.value)
  })
  cancelar()
  cargar()
}

// Copia los datos del candidato al formulario y activa el modo edición
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

// Limpia el formulario y sale del modo edición
function cancelar() {
  form.value = { nombre: '', email: '', puesto: '', telefono: '' }
  editandoId.value = null
}

async function estado(id, e) {
  await fetch(`/api/candidatos/${id}?estado=${e}`, { method: 'PATCH' })
  cargar()
}

async function borrar(id) {
  await fetch(`/api/candidatos/${id}`, { method: 'DELETE' })
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
      <!-- El texto del botón cambia según el modo -->
      <button>{{ editandoId !== null ? 'Guardar cambios' : 'Agregar' }}</button>
      <!-- Solo aparece cuando se está editando -->
      <button v-if="editandoId !== null" type="button" class="gris" @click="cancelar">Cancelar</button>
    </form>

    <div class="filtro">
      <label>Filtrar por estado:</label>
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
              <button @click="borrar(c.id)">Eliminar</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </main>
</template>
