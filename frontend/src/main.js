// Importa la función createApp desde la librería Vue
import { createApp } from 'vue'
// Importa tu pantalla principal (el archivo App.vue)
import App from './App.vue'
// Importa los estilos; Vite los incluye en la compilación final
import './style.css'

// Crea la aplicación con App y la "monta" dentro del <div id="app">
// que está en index.html. Desde aquí Vue controla esa parte de la página
createApp(App).mount('#app')
