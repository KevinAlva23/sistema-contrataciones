<script setup>
import { computed, onMounted, ref } from "vue";
import { api, aviso, NOMBRES } from "../store";

const d = ref(null);
onMounted(async () => {
  try {
    d.value = await api("/estadisticas");
  } catch (e) {
    aviso(e.message);
  }
});
const max = (o) => Math.max(1, ...Object.values(o));
const embudo = computed(() => (d.value ? Object.entries(d.value.por_estado) : []));
</script>

<template>
  <h1 class="titulo">Reportes</h1>
  <template v-if="d">
    <div class="kpis">
      <div class="kpi"><b>{{ d.total }}</b><span>Candidatos</span></div>
      <div class="kpi"><b>{{ d.por_estado.contratado }}</b><span>Contratados</span></div>
      <div class="kpi"><b>{{ d.conversion }}%</b><span>Conversión</span></div>
      <div class="kpi alerta"><b>{{ d.sin_avance }}</b><span>Sin avance</span></div>
    </div>
    <div class="rejilla dos">
      <section class="tarjeta">
        <h3>Embudo por etapa</h3>
        <div v-for="[k, n] in embudo" :key="k" class="barra-h">
          <span>{{ NOMBRES[k] }}</span>
          <i :style="{ width: (n / max(d.por_estado)) * 100 + '%', background: `var(--e-${k})` }" />
          <b>{{ n }}</b>
        </div>
      </section>
      <section class="tarjeta">
        <h3>Por vacante</h3>
        <div v-for="(n, k) in d.por_vacante" :key="k" class="barra-h">
          <span>{{ k }}</span><i :style="{ width: (n / max(d.por_vacante)) * 100 + '%' }" /><b>{{ n }}</b>
        </div>
        <h3 style="margin-top: 20px">Registros por mes</h3>
        <div v-for="(n, k) in d.por_mes" :key="k" class="barra-h">
          <span>{{ k }}</span><i :style="{ width: (n / max(d.por_mes)) * 100 + '%' }" /><b>{{ n }}</b>
        </div>
      </section>
    </div>
  </template>
</template>
