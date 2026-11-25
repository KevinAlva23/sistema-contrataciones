<script setup>
import { onMounted, ref } from "vue";
import { api, aviso, puede } from "../store";

const vacantes = ref([]);
const candidatos = ref([]);
const form = ref({ titulo: "", area: "" });

const cargar = async () => {
  [vacantes.value, candidatos.value] = await Promise.all([api("/vacantes"), api("/candidatos")]);
};
onMounted(cargar);
const cuenta = (v, estado) =>
  candidatos.value.filter((c) => c.vacante_id === v.id && (!estado || c.estado === estado)).length;

async function crear() {
  try {
    await api("/vacantes", { metodo: "POST", cuerpo: { titulo: form.value.titulo, area: form.value.area || "General" } });
    form.value = { titulo: "", area: "" };
    await cargar();
  } catch (e) {
    aviso(e.message);
  }
}
async function alternar(v) {
  await api(`/vacantes/${v.id}`, { metodo: "PATCH", cuerpo: { abierta: !v.abierta } });
  await cargar();
}
</script>

<template>
  <h1 class="titulo">Vacantes</h1>
  <form v-if="puede('edit')" class="barra" @submit.prevent="crear">
    <input v-model="form.titulo" placeholder="Puesto" aria-label="Puesto" required />
    <input v-model="form.area" placeholder="Área" aria-label="Área" />
    <button class="btn primario">Publicar vacante</button>
  </form>
  <div class="rejilla">
    <article v-for="v in vacantes" :key="v.id" class="tarjeta">
      <span class="chip" :class="v.abierta ? 'ok' : 'off'">{{ v.abierta ? "Abierta" : "Cerrada" }}</span>
      <h3>{{ v.titulo }}</h3>
      <p class="tenue">{{ v.area }}</p>
      <div class="cifras">
        <div><b>{{ cuenta(v) }}</b><small>Candidatos</small></div>
        <div><b>{{ cuenta(v, "contratado") }}</b><small>Contratados</small></div>
      </div>
      <button v-if="puede('edit')" class="btn" @click="alternar(v)">{{ v.abierta ? "Cerrar" : "Reabrir" }}</button>
    </article>
  </div>
</template>
