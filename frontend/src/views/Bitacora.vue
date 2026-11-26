<script setup>
import { onMounted, ref } from "vue";
import { api, aviso, fecha } from "../store";

const filas = ref([]);
onMounted(async () => {
  try {
    filas.value = await api("/bitacora?limite=500");
  } catch (e) {
    aviso(e.message);
  }
});
</script>

<template>
  <h1 class="titulo">Bitácora de auditoría</h1>
  <div class="tabla-caja">
    <table class="tabla">
      <thead><tr><th>Fecha</th><th>Usuario</th><th>Acción</th></tr></thead>
      <tbody>
        <tr v-for="f in filas" :key="f.id"><td>{{ fecha(f.fecha) }}</td><td>{{ f.usuario }}</td><td>{{ f.accion }}</td></tr>
        <tr v-if="!filas.length"><td colspan="3" class="tenue">Sin movimientos todavía.</td></tr>
      </tbody>
    </table>
  </div>
</template>
