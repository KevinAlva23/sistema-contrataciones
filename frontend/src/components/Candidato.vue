<script setup>
import { computed, onMounted, ref } from "vue";
import { api, aviso, fecha, NOMBRES, puede, store } from "../store";
import Avatar from "./Avatar.vue";
import Icono from "./Icono.vue";

const props = defineProps({ id: { type: Number, required: true }, vacantes: { type: Array, default: () => [] } });
const emit = defineEmits(["cerrar", "cambio"]);

const c = ref(null);
const hist = ref([]);
const form = ref({});
const motivo = ref(store.config.motivos[0]);

async function cargar() {
  const lista = await api("/candidatos");
  c.value = lista.find((x) => x.id === props.id);
  if (!c.value) return emit("cerrar");
  hist.value = await api(`/candidatos/${props.id}/historial`);
  const { nombre, email, telefono, vacante_id, evaluacion, notas, salario } = c.value;
  form.value = { nombre, email, telefono, vacante_id, evaluacion, notas, salario };
}
onMounted(() => cargar().catch((e) => aviso(e.message)));

const edita = computed(() => puede("edit"));
const siguientes = computed(() => store.config.transiciones[c.value.estado].filter((e) => e !== "rechazado"));
const puedeRechazar = computed(() => store.config.transiciones[c.value.estado].includes("rechazado"));
const idx = computed(() => store.config.etapas.indexOf(c.value.estado));
const pasos = store.config.etapas.filter((e) => e !== "rechazado");

async function accion(fn, ok) {
  try {
    await fn();
    if (ok) aviso(ok);
    await cargar();
    emit("cambio");
  } catch (e) {
    aviso(e.message);
  }
}
const guardar = () => accion(() => api(`/candidatos/${props.id}`, { metodo: "PATCH", cuerpo: { ...form.value, salario: Number(form.value.salario) || 0 } }), "Cambios guardados");
const avanzar = (estado, m = "") => accion(() => api(`/candidatos/${props.id}/avanzar`, { metodo: "POST", cuerpo: { estado, motivo: m } }));
const pedir = () => accion(() => api(`/candidatos/${props.id}/solicitar-oferta`, { metodo: "POST" }), "Aprobación solicitada");
const aprobar = () => accion(() => api(`/candidatos/${props.id}/aprobar-oferta`, { metodo: "POST" }), "Oferta aprobada");
async function borrar() {
  if (!confirm(`¿Eliminar a ${c.value.nombre}? Quedará registrado en la bitácora.`)) return;
  try {
    await api(`/candidatos/${props.id}`, { metodo: "DELETE" });
    emit("cambio");
    emit("cerrar");
  } catch (e) {
    aviso(e.message);
  }
}
</script>

<template>
  <div class="velo lado" @click.self="emit('cerrar')">
    <aside v-if="c" class="panel" role="dialog" :aria-label="c.nombre">
      <header class="panel-cab">
        <Avatar :nombre="c.nombre" grande />
        <div>
          <h2>{{ c.nombre }}</h2>
          <span class="chip" :style="{ '--c': `var(--e-${c.estado})` }">{{ NOMBRES[c.estado] }}</span>
        </div>
        <button class="btn icono" aria-label="Cerrar" @click="emit('cerrar')"><Icono n="x" /></button>
      </header>

      <ol class="pasos" aria-label="Progreso">
        <li v-for="(p, i) in pasos" :key="p" :class="{ hecho: i < idx || c.estado === 'contratado', actual: p === c.estado }">
          <i /><span>{{ NOMBRES[p] }}</span>
        </li>
      </ol>

      <section v-if="c.estado === 'rechazado'" class="caja peligro">Rechazado · {{ c.motivo_rechazo }}</section>

      <section class="caja">
        <div class="campos">
          <label>Nombre<input v-model="form.nombre" :disabled="!edita" /></label>
          <label>Correo<input v-model="form.email" type="email" :disabled="!edita" /></label>
          <label>Teléfono<input v-model="form.telefono" :disabled="!edita" /></label>
          <label>Vacante
            <select v-model="form.vacante_id" :disabled="!edita">
              <option v-for="v in vacantes" :key="v.id" :value="v.id">{{ v.titulo }}</option>
            </select>
          </label>
          <label>Evaluación
            <select v-model.number="form.evaluacion" :disabled="!edita">
              <option :value="0">Sin evaluar</option>
              <option v-for="n in 5" :key="n" :value="n">{{ "★".repeat(n) }}</option>
            </select>
          </label>
        </div>
        <label>Notas de seguimiento<textarea v-model="form.notas" rows="3" maxlength="2000" :disabled="!edita" /></label>
        <button v-if="edita" class="btn" @click="guardar">Guardar cambios</button>
      </section>

      <section v-if="['oferta', 'contratado'].includes(c.estado)" class="caja">
        <h3>Oferta económica</h3>
        <label>Salario mensual bruto (MXN)<input v-model="form.salario" type="number" min="0" :disabled="!edita || c.oferta_aprobada" /></label>
        <div class="acciones">
          <span class="chip" :class="c.oferta_aprobada ? 'ok' : ''">{{ c.oferta_aprobada ? "Aprobada" : c.oferta_solicitada ? "Pendiente de aprobación" : "Sin solicitar" }}</span>
          <button v-if="edita && !c.oferta_solicitada && !c.oferta_aprobada" class="btn" @click="guardar().then(pedir)">Guardar y solicitar aprobación</button>
          <button v-if="puede('apr') && c.oferta_solicitada && !c.oferta_aprobada" class="btn primario" @click="aprobar">Aprobar oferta</button>
        </div>
      </section>

      <section v-if="edita && (siguientes.length || puedeRechazar)" class="caja">
        <h3>Siguiente paso</h3>
        <div class="acciones">
          <button v-for="e in siguientes" :key="e" class="btn primario" :disabled="e === 'contratado' && !c.oferta_aprobada" @click="avanzar(e)">{{ NOMBRES[e] }} →</button>
        </div>
        <div v-if="puedeRechazar" class="acciones rechazo">
          <select v-model="motivo" aria-label="Motivo de rechazo"><option v-for="m in store.config.motivos" :key="m">{{ m }}</option></select>
          <button class="btn peligro" @click="avanzar('rechazado', motivo)">Rechazar</button>
        </div>
      </section>

      <section class="caja">
        <h3>Historial</h3>
        <ul class="linea">
          <li v-for="h in hist" :key="h.id"><b>{{ h.accion }}</b><small>{{ fecha(h.fecha) }} · {{ h.usuario }}</small></li>
        </ul>
        <p class="tenue">Datos conservados hasta {{ fecha(c.conservar_hasta).split(",")[0] }}.</p>
      </section>

      <button v-if="puede('del')" class="btn peligro" @click="borrar">Eliminar candidato</button>
    </aside>
  </div>
</template>
