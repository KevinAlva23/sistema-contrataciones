<script setup>
import { computed, onMounted, ref } from "vue";
import { api, ROLES, aviso, puede, salir, store } from "./store";
import Icono from "./components/Icono.vue";
import Avatar from "./components/Avatar.vue";
import Login from "./views/Login.vue";
import Tablero from "./views/Tablero.vue";
import Vacantes from "./views/Vacantes.vue";
import Bitacora from "./views/Bitacora.vue";
import Reportes from "./views/Reportes.vue";
import Usuarios from "./views/Usuarios.vue";

const vista = ref("tablero");
const listo = ref(false);
const tema = ref(localStorage.getItem("tema") || "auto");

const MENU = [
  { id: "tablero", t: "Tablero", i: "tablero", ok: () => true },
  { id: "vacantes", t: "Vacantes", i: "vacantes", ok: () => true },
  { id: "reportes", t: "Reportes", i: "reportes", ok: () => puede("aud") },
  { id: "bitacora", t: "Bitácora", i: "bitacora", ok: () => puede("aud") },
  { id: "usuarios", t: "Usuarios", i: "usuarios", ok: () => puede("usuarios") },
];
const menu = computed(() => MENU.filter((m) => m.ok()));
const COMP = { tablero: Tablero, vacantes: Vacantes, reportes: Reportes, bitacora: Bitacora, usuarios: Usuarios };

function aplicarTema() {
  if (tema.value === "auto") document.documentElement.removeAttribute("data-tema");
  else document.documentElement.dataset.tema = tema.value;
}
function cambiarTema() {
  const oscuro = getComputedStyle(document.documentElement).colorScheme.includes("dark");
  tema.value = oscuro ? "claro" : "oscuro";
  localStorage.setItem("tema", tema.value);
  aplicarTema();
}

async function arrancar() {
  try {
    store.config = await api("/config");
    if (store.token) store.usuario = await api("/yo");
  } catch (e) {
    aviso(e.message);
  }
  listo.value = true;
}
onMounted(() => {
  aplicarTema();
  arrancar();
});
async function entrado() {
  vista.value = "tablero";
}
</script>

<template>
  <div v-if="!listo" class="carga">Cargando…</div>
  <Login v-else-if="!store.usuario" @entrar="entrado" />
  <div v-else class="app">
    <aside class="lateral">
      <div class="marca"><span class="punto" /> Talento</div>
      <nav aria-label="Secciones">
        <button
          v-for="m in menu"
          :key="m.id"
          class="nav"
          :aria-current="vista === m.id"
          @click="vista = m.id"
        >
          <Icono :n="m.i" /><span>{{ m.t }}</span>
        </button>
      </nav>
      <div class="pie">
        <button class="nav" aria-label="Cambiar tema" @click="cambiarTema"><Icono n="luna" /><span>Tema</span></button>
        <div class="yo">
          <Avatar :nombre="store.usuario.nombre" />
          <div>
            <b>{{ store.usuario.nombre }}</b>
            <small>{{ ROLES[store.usuario.rol] }}</small>
          </div>
        </div>
        <button class="nav" @click="salir"><Icono n="salir" /><span>Salir</span></button>
      </div>
    </aside>
    <main id="contenido" class="contenido">
      <component :is="COMP[vista]" />
    </main>
  </div>
  <div v-if="store.toast" class="toast" role="status">{{ store.toast }}</div>
</template>
