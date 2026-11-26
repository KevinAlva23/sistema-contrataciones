<script setup>
defineProps({ n: { type: String, required: true } });
const P = {
  tablero: "M3 3h7v9H3z M14 3h7v5h-7z M14 12h7v9h-7z M3 16h7v5H3z",
  vacantes: "M4 7h16v13H4z M9 7V4h6v3 M4 13h16",
  bitacora: "M8 4h8l4 4v12H4V4h4 M8 12h8 M8 16h8",
  reportes: "M3 3v18h18 M8 17v-5 M13 17V8 M18 17v-9",
  usuarios: "M16 20v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 10a4 4 0 1 0 0-8 4 4 0 0 0 0 8 M22 20v-2a4 4 0 0 0-3-3.9 M16 2.1a4 4 0 0 1 0 7.8",
  mas: "M12 5v14 M5 12h14",
  x: "M18 6 6 18 M6 6l12 12",
  luna: "M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8z",
  salir: "M9 21H5V3h4 M16 17l5-5-5-5 M21 12H9",
  bajar: "M12 3v12 M7 10l5 5 5-5 M4 21h16",
  subir: "M12 15V3 M7 8l5-5 5 5 M4 21h16",
  alerta: "M12 9v4 M12 17h.01 M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z",
};
</script>

<template>
  <svg
    width="18"
    height="18"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="2"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="P[n]" />
  </svg>
</template>
