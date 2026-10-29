<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({ token: String })
const emit = defineEmits(['salir'])

const registros = ref([])
const busqueda = ref('')
const tipo = ref('todas')

const etiquetas = {
  login: 'Inicio de sesión',
  login_fallido: 'Intento fallido',
  candidato_creado: 'Candidato creado',
  candidato_editado: 'Candidato editado',
  candidato_eliminado: 'Candidato eliminado',
  estado_cambiado: 'Cambio de estado',
  usuario_creado: 'Usuario creado',
  usuario_modificado: 'Usuario modificado',
  usuario_eliminado: 'Usuario eliminado'
}

// Color de la etiqueta según la gravedad de la acción
function clase(a) {
  if (a.includes('eliminado') || a === 'login_fallido') return 'rechazado'
  if (a.includes('creado') || a === 'login') return 'contratado'
  return 'pendiente'
}

const fecha = (f) => new Date(f).toLocaleString('es-MX')

async function cargar() {
  const r = await fetch('/api/bitacora', {
    headers: { Authorization: `Bearer ${props.token}` }
  })
  if (r.status === 401) { emit('salir'); return }
  if (r.ok) registros.value = await r.json()
}

const filtrados = computed(() => {
  const t = busqueda.value.trim().toLowerCase()
  return registros.value.filter(b =>
    (tipo.value === 'todas' || b.accion === tipo.value) &&
    (!t || b.usuario.toLowerCase().includes(t) || b.detalle.toLowerCase().includes(t))
  )
})

onMounted(cargar)
</script>

<template>
  <section class="panel">
    <h2 class="panel-titulo">Bitácora de auditoría</h2>
    <div class="toolbar">
      <input v-model="busqueda" class="buscador" placeholder="Buscar por usuario o detalle" />
      <select v-model="tipo">
        <option value="todas">Todas las acciones</option>
        <option v-for="(n, k) in etiquetas" :key="k" :value="k">{{ n }}</option>
      </select>
      <button class="gris" @click="cargar">Actualizar</button>
      <span class="cuenta">{{ filtrados.length }} registro(s)</span>
    </div>
    <div class="tabla-scroll">
      <table>
        <thead>
          <tr><th>Fecha</th><th>Usuario</th><th>Acción</th><th>Detalle</th></tr>
        </thead>
        <tbody>
          <tr v-if="!filtrados.length">
            <td colspan="4" class="vacio">Sin registros</td>
          </tr>
          <tr v-for="b in filtrados" :key="b.id">
            <td>{{ fecha(b.fecha) }}</td>
            <td>{{ b.usuario }}</td>
            <td><span class="estado" :class="clase(b.accion)">{{ etiquetas[b.accion] || b.accion }}</span></td>
            <td>{{ b.detalle }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
