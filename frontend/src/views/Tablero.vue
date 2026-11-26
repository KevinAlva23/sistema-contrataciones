<script setup>
import { computed, onMounted, ref } from "vue";
import { api, aviso, dias, NOMBRES, puede, store } from "../store";
import Icono from "../components/Icono.vue";
import Avatar from "../components/Avatar.vue";
import Candidato from "../components/Candidato.vue";

const candidatos = ref([]);
const vacantes = ref([]);
const q = ref("");
const vf = ref(0);
const abierto = ref(null);
const nuevo = ref(null);
const arrastrando = ref(null);
const importado = ref(null);

async function cargar() {
  try {
    [candidatos.value, vacantes.value] = await Promise.all([api("/candidatos"), api("/vacantes")]);
  } catch (e) {
    aviso(e.message);
  }
}
onMounted(cargar);

const vac = (id) => vacantes.value.find((v) => v.id === id)?.titulo ?? "—";
const visibles = computed(() => {
  const t = q.value.trim().toLowerCase();
  return candidatos.value.filter(
    (c) => (!vf.value || c.vacante_id === vf.value) && (!t || (c.nombre + c.email).toLowerCase().includes(t)),
  );
});
const columna = (e) => visibles.value.filter((c) => c.estado === e);
const final = (c) => ["contratado", "rechazado"].includes(c.estado);
const sinAvance = (c) => !final(c) && dias(c.actualizado) > 7;
const kpi = computed(() => {
  const act = candidatos.value.filter((c) => !final(c));
  const h = candidatos.value.filter((c) => c.estado === "contratado").length;
  return {
    total: candidatos.value.length,
    activos: act.length,
    h,
    conv: candidatos.value.length ? Math.round((h / candidatos.value.length) * 100) : 0,
    alerta: act.filter(sinAvance).length,
  };
});

async function soltar(estado) {
  const c = arrastrando.value;
  arrastrando.value = null;
  if (!c || !puede("edit") || c.estado === estado) return;
  if (!store.config.transiciones[c.estado].includes(estado)) return aviso("Ese movimiento no está permitido");
  if (estado === "rechazado" || estado === "contratado") return (abierto.value = c.id);
  try {
    await api(`/candidatos/${c.id}/avanzar`, { metodo: "POST", cuerpo: { estado } });
    await cargar();
  } catch (e) {
    aviso(e.message);
  }
}

async function guardarNuevo() {
  try {
    await api("/candidatos", { metodo: "POST", cuerpo: nuevo.value });
    nuevo.value = null;
    await cargar();
    aviso("Candidato registrado");
  } catch (e) {
    aviso(e.message);
  }
}
const abrirNuevo = () =>
  (nuevo.value = {
    nombre: "", email: "", telefono: "", aviso_privacidad: false,
    vacante_id: vacantes.value.find((v) => v.abierta)?.id ?? 0,
  });

async function exportar() {
  try {
    const b = await api("/candidatos/exportar", { blob: true });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(b);
    a.download = "candidatos.csv";
    a.click();
    URL.revokeObjectURL(a.href);
  } catch (e) {
    aviso(e.message);
  }
}
async function importar(ev) {
  const f = ev.target.files[0];
  ev.target.value = "";
  if (!f) return;
  try {
    const r = await api("/candidatos/importar", { metodo: "POST", archivo: f });
    importado.value = r;
    await cargar();
  } catch (e) {
    aviso(e.message);
  }
}
</script>

<template>
  <header class="cabecera">
    <h1 class="titulo">Tablero de contratación</h1>
    <div class="acciones">
      <button v-if="puede('aud')" class="btn" @click="exportar"><Icono n="bajar" /> Exportar</button>
      <label v-if="puede('usuarios')" class="btn"><Icono n="subir" /> Importar<input type="file" accept=".csv" hidden @change="importar" /></label>
      <button v-if="puede('edit')" class="btn primario" @click="abrirNuevo"><Icono n="mas" /> Candidato</button>
    </div>
  </header>

  <div class="kpis">
    <div class="kpi"><b>{{ kpi.total }}</b><span>Candidatos</span></div>
    <div class="kpi"><b>{{ kpi.activos }}</b><span>En proceso</span></div>
    <div class="kpi"><b>{{ kpi.h }}</b><span>Contratados</span></div>
    <div class="kpi"><b>{{ kpi.conv }}%</b><span>Conversión</span></div>
    <div class="kpi alerta"><b>{{ kpi.alerta }}</b><span>Sin avance &gt; 7 días</span></div>
  </div>

  <div class="barra">
    <input v-model="q" type="search" placeholder="Buscar por nombre o correo" aria-label="Buscar" />
    <select v-model="vf" aria-label="Filtrar por vacante">
      <option :value="0">Todas las vacantes</option>
      <option v-for="v in vacantes" :key="v.id" :value="v.id">{{ v.titulo }}</option>
    </select>
  </div>

  <div class="tablero">
    <section
      v-for="e in store.config.etapas"
      :key="e"
      class="columna"
      :aria-label="NOMBRES[e]"
      @dragover.prevent
      @drop="soltar(e)"
    >
      <h2><span class="pto" :style="{ background: `var(--e-${e})` }" />{{ NOMBRES[e] }}<em>{{ columna(e).length }}</em></h2>
      <button
        v-for="c in columna(e)"
        :key="c.id"
        class="cand"
        :style="{ '--c': `var(--e-${e})` }"
        :draggable="puede('edit') && !final(c)"
        @dragstart="arrastrando = c"
        @click="abierto = c.id"
      >
        <Avatar :nombre="c.nombre" />
        <span class="cuerpo">
          <b>{{ c.nombre }}</b>
          <small>{{ vac(c.vacante_id) }}</small>
          <span v-if="c.evaluacion" class="estrellas">{{ "★".repeat(c.evaluacion) }}<i>{{ "★".repeat(5 - c.evaluacion) }}</i></span>
        </span>
        <span v-if="sinAvance(c)" class="aviso-dias" title="Sin avance"><Icono n="alerta" /> {{ dias(c.actualizado) }} d</span>
      </button>
      <p v-if="!columna(e).length" class="vacio">Sin candidatos</p>
    </section>
  </div>

  <Candidato v-if="abierto" :id="abierto" :vacantes="vacantes" @cerrar="abierto = null" @cambio="cargar" />

  <div v-if="nuevo" class="velo" @click.self="nuevo = null">
    <form class="modal" role="dialog" aria-label="Nuevo candidato" @submit.prevent="guardarNuevo">
      <h2>Nuevo candidato</h2>
      <label>Nombre completo<input v-model="nuevo.nombre" maxlength="120" required /></label>
      <label>Correo electrónico<input v-model="nuevo.email" type="email" required /></label>
      <label>Teléfono (10 dígitos)<input v-model="nuevo.telefono" pattern="[0-9]{10}" inputmode="numeric" required /></label>
      <label>Vacante
        <select v-model="nuevo.vacante_id" required>
          <option v-for="v in vacantes.filter((x) => x.abierta)" :key="v.id" :value="v.id">{{ v.titulo }}</option>
        </select>
      </label>
      <label class="casilla"><input v-model="nuevo.aviso_privacidad" type="checkbox" required /> El candidato aceptó el aviso de privacidad (datos conservados 24 meses)</label>
      <div class="acciones fin"><button type="button" class="btn" @click="nuevo = null">Cancelar</button><button class="btn primario">Guardar</button></div>
    </form>
  </div>

  <div v-if="importado" class="velo" @click.self="importado = null">
    <div class="modal" role="dialog" aria-label="Resultado de importación">
      <h2>Importación terminada</h2>
      <p>{{ importado.importados }} candidatos importados, {{ importado.errores.length }} con error.</p>
      <ul class="errores"><li v-for="e in importado.errores" :key="e.fila">Fila {{ e.fila }}: {{ e.motivo }}</li></ul>
      <div class="acciones fin"><button class="btn primario" @click="importado = null">Cerrar</button></div>
    </div>
  </div>
</template>
