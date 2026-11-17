import { createApp } from 'vue'
import App from './App.vue'
import './style.css'

// Aplica el tema guardado antes de montar la app (evita parpadeos).
// Va aquí y no en index.html porque la CSP de Nginx bloquea scripts en línea.
try {
  const t = localStorage.getItem('tema')
  if (t) document.documentElement.dataset.tema = t
  if (localStorage.getItem('compacto') === '1') document.documentElement.classList.add('compacto')
} catch (e) {}

createApp(App).mount('#app')
