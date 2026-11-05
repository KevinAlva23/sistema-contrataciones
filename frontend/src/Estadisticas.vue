<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({ token: String })
const emit = defineEmits(['salir'])
const d = ref(null)

async function cargar() {
  const r = await fetch('/api/estadisticas', {
    headers: { Authorization: `Bearer ${props.token}` }
  })
  if (r.status === 401) { emit('salir'); return }
  if (r.ok) d.value = await r.json()
}

// Convierte un objeto {clave: n} en filas con porcentaje de ancho
function barras(obj) {
  const max = Math.max(1, ...Object.values(obj))
  return Object.entries(obj).map(([k, v]) => ({ k, v, w: (100 * v) / max }))
}

const estados = computed(() => d.value ? barras(d.value.por_estado) : [])
const puestos = computed(() => d.value ? barras(d.value.por_puesto) : [])
const meses = computed(() => d.value ? barras(d.value.por_mes) : [])

onMounted(cargar)
</script>

<template>
  <div v-if="d">
    <section class="stats">
      <div class="stat">
        <div class="num">{{ d.total }}</div>
        <div class="lbl">Total de candidatos</div>
      </div>
      <div class="stat cont">
        <div class="num">{{ d.tasa_contratacion === null ? '—' : d.tasa_contratacion + '%' }}</div>
        <div class="lbl">Tasa de contratación</div>
      </div>
    </section>

    <section class="panel">
      <h2 class="panel-titulo">Por estado</h2>
      <div class="panel-cuerpo">
        <div v-for="b in estados" :key="b.k" class="barra-fila">
          <span class="barra-et">{{ b.k }}</span>
          <div class="barra-pista"><div class="barra" :class="b.k" :style="{ width: b.w + '%' }"></div></div>
          <span class="barra-num">{{ b.v }}</span>
        </div>
      </div>
    </section>

    <section class="panel">
      <h2 class="panel-titulo">Por puesto (top 10)</h2>
      <div class="panel-cuerpo">
        <div v-for="b in puestos" :key="b.k" class="barra-fila">
          <span class="barra-et">{{ b.k }}</span>
          <div class="barra-pista"><div class="barra" :style="{ width: b.w + '%' }"></div></div>
          <span class="barra-num">{{ b.v }}</span>
        </div>
      </div>
    </section>

    <section class="panel">
      <h2 class="panel-titulo">Registrados por mes</h2>
      <div class="panel-cuerpo">
        <div v-for="b in meses" :key="b.k" class="barra-fila">
          <span class="barra-et">{{ b.k }}</span>
          <div class="barra-pista"><div class="barra" :style="{ width: b.w + '%' }"></div></div>
          <span class="barra-num">{{ b.v }}</span>
        </div>
      </div>
    </section>
  </div>
  <p v-else class="vacio">Cargando...</p>
</template>
