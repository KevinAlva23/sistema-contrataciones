<script setup>
import { ref } from "vue";
import { api, guardarToken, store } from "../store";

const emit = defineEmits(["entrar"]);
const usuario = ref("");
const clave = ref("");
const error = ref("");
const cargando = ref(false);

async function enviar() {
  error.value = "";
  cargando.value = true;
  try {
    const r = await api("/login", { metodo: "POST", cuerpo: { usuario: usuario.value, clave: clave.value } });
    guardarToken(r.token);
    store.usuario = r.usuario;
    emit("entrar");
  } catch (e) {
    error.value = e.message;
  } finally {
    cargando.value = false;
  }
}
</script>

<template>
  <div class="login">
    <section class="login-arte">
      <div class="marca"><span class="punto" /> Talento</div>
      <h1>Contrata con claridad, de la primera entrevista a la oferta.</h1>
      <p>Seguimiento por etapas, aprobaciones y bitácora de auditoría en un solo lugar.</p>
    </section>
    <section class="login-form">
      <form @submit.prevent="enviar">
        <h2>Iniciar sesión</h2>
        <label>Usuario<input v-model="usuario" autocomplete="username" required autofocus /></label>
        <label>Contraseña<input v-model="clave" type="password" autocomplete="current-password" required /></label>
        <p v-if="error" class="error" role="alert">{{ error }}</p>
        <button class="btn primario" :disabled="cargando">{{ cargando ? "Entrando…" : "Entrar" }}</button>
      </form>
    </section>
  </div>
</template>
