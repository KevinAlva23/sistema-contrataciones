<script setup>
import { onMounted, ref } from "vue";
import { api, aviso, ROLES, store } from "../store";

const lista = ref([]);
const form = ref({ usuario: "", nombre: "", rol: "reclutador", clave: "" });

const cargar = async () => (lista.value = await api("/usuarios"));
onMounted(cargar);

async function hacer(fn, ok) {
  try {
    await fn();
    if (ok) aviso(ok);
    await cargar();
  } catch (e) {
    aviso(e.message);
  }
}
const crear = () =>
  hacer(async () => {
    await api("/usuarios", { metodo: "POST", cuerpo: form.value });
    form.value = { usuario: "", nombre: "", rol: "reclutador", clave: "" };
  }, "Usuario creado");
const cambiar = (u, cuerpo) => hacer(() => api(`/usuarios/${u.id}`, { metodo: "PATCH", cuerpo }));
const revocar = (u) => hacer(() => api(`/usuarios/${u.id}/cerrar-sesiones`, { metodo: "POST" }), "Sesiones cerradas");
const borrar = (u) =>
  confirm(`¿Eliminar a ${u.nombre}?`) && hacer(() => api(`/usuarios/${u.id}`, { metodo: "DELETE" }));
const reset = (u) => {
  const clave = prompt("Nueva contraseña (10+ caracteres, mayúsculas, minúsculas y números)");
  if (clave) cambiar(u, { clave });
};
</script>

<template>
  <h1 class="titulo">Usuarios</h1>
  <form class="barra" @submit.prevent="crear">
    <input v-model="form.usuario" placeholder="Usuario" aria-label="Usuario" required />
    <input v-model="form.nombre" placeholder="Nombre" aria-label="Nombre" required />
    <select v-model="form.rol" aria-label="Rol"><option v-for="(n, r) in ROLES" :key="r" :value="r">{{ n }}</option></select>
    <input v-model="form.clave" type="password" placeholder="Contraseña inicial" aria-label="Contraseña" required />
    <button class="btn primario">Crear</button>
  </form>
  <div class="tabla-caja">
    <table class="tabla">
      <thead><tr><th>Usuario</th><th>Rol</th><th>Estado</th><th /></tr></thead>
      <tbody>
        <tr v-for="u in lista" :key="u.id">
          <td><b>{{ u.nombre }}</b><br /><small class="tenue">{{ u.usuario }}</small></td>
          <td>
            <select :value="u.rol" :aria-label="`Rol de ${u.nombre}`" @change="cambiar(u, { rol: $event.target.value })">
              <option v-for="(n, r) in ROLES" :key="r" :value="r">{{ n }}</option>
            </select>
          </td>
          <td><span class="chip" :class="u.activo ? 'ok' : 'off'">{{ u.activo ? "Activo" : "Inactivo" }}</span></td>
          <td class="acciones">
            <button class="btn" @click="cambiar(u, { activo: !u.activo })">{{ u.activo ? "Desactivar" : "Activar" }}</button>
            <button class="btn" @click="reset(u)">Restablecer clave</button>
            <button class="btn" @click="revocar(u)">Cerrar sesiones</button>
            <button class="btn peligro" :disabled="u.id === store.usuario.id" @click="borrar(u)">Eliminar</button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
