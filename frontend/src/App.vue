<script setup>
// ref crea variables "reactivas": cuando cambian, la pantalla se actualiza sola.
// onMounted ejecuta una función cuando la página termina de cargar.
import { ref, computed, onMounted } from 'vue'

// Lista de candidatos que viene del backend. Empieza vacía.
// Para leer o cambiar su valor en el script se usa .value
const candidatos = ref([])

// Datos del formulario. Cada campo se enlaza con un <input> mediante v-model
const form = ref({ nombre: '', email: '', puesto: '', telefono: '' })

// Estado elegido en el selector
const filtro = ref('todos')

// Lista que se muestra: todos o solo los del estado elegido
const filtrados = computed(() =>
  filtro.value === 'todos'
    ? candidatos.value
    : candidatos.value.filter(c => c.estado === filtro.value)
)

// Pide la lista de candidatos al backend
async function cargar() {
  // fetch hace una petición HTTP (GET por defecto).
  // "await" espera la respuesta antes de seguir con la siguiente línea
  const r = await fetch('/api/candidatos')
  // Convierte la respuesta de JSON a un arreglo de JavaScript y lo guarda
  candidatos.value = await r.json()
}

// Envía el formulario para crear un candidato nuevo
async function agregar() {
  await fetch('/api/candidatos', {
    method: 'POST',                                   // POST = crear
    headers: { 'Content-Type': 'application/json' },  // avisa que se envía JSON
    body: JSON.stringify(form.value)                  // convierte el objeto a texto JSON
  })
  // Limpia el formulario dejando todos los campos vacíos
  form.value = { nombre: '', email: '', puesto: '', telefono: '' }
  // Vuelve a pedir la lista para que aparezca el nuevo candidato
  cargar()
}

// Cambia el estado de un candidato (id) al valor e ("contratado" o "rechazado")
async function estado(id, e) {
  // Las comillas invertidas ` ` permiten insertar variables con ${ }
  await fetch(`/api/candidatos/${id}?estado=${e}`, { method: 'PATCH' })  // PATCH = modificar
  cargar()   // recarga la tabla para ver el cambio
}

// Elimina un candidato por su id
async function borrar(id) {
  await fetch(`/api/candidatos/${id}`, { method: 'DELETE' })   // DELETE = borrar
  cargar()   // recarga la tabla
}

// Al terminar de cargar la página, pide la lista de inmediato
onMounted(cargar)
</script>

<template>
  <!-- Caja principal; "contenedor" es la clase de style.css que la centra -->
  <main class="contenedor">
    <h1>Sistema de Contrataciones</h1>

    <!-- @submit.prevent: al enviar el formulario ejecuta agregar() y
         evita que la página se recargue (eso es ".prevent") -->
    <form class="tarjeta formulario" @submit.prevent="agregar">
      <!-- v-model enlaza el campo con la variable: lo que escribes se guarda en form.
           "required" impide enviar el formulario si está vacío -->
      <input v-model="form.nombre" placeholder="Nombre" required />
      <!-- type="email" valida que tenga formato de correo -->
      <input v-model="form.email" type="email" placeholder="Email" required />
      <input v-model="form.puesto" placeholder="Puesto" required />
      <!-- El teléfono no lleva "required": es opcional -->
      <input v-model="form.telefono" placeholder="Teléfono (10 dígitos)" required pattern="[0-9]{10}" title="Escribe 10 números" />
      <!-- Un botón dentro de un form, sin más, lo envía al hacer clic -->
      <button>Agregar</button>
    </form>

    <!-- Selector de filtro -->
    <div class="filtro">
      <label>Filtrar por estado:</label>
      <select v-model="filtro">
        <option value="todos">Todos</option>
        <option value="pendiente">Pendiente</option>
        <option value="contratado">Contratado</option>
        <option value="rechazado">Rechazado</option>
      </select>
      <span>{{ filtrados.length }} candidato(s)</span>
    </div>

    <!-- Tarjeta blanca con scroll horizontal por si la tabla no cabe -->
    <div class="tarjeta tabla-scroll">
      <table>
        <!-- thead = encabezado de la tabla -->
        <thead>
          <tr>
            <th>Nombre</th><th>Email</th><th>Puesto</th>
            <th>Teléfono</th><th>Estado</th><th>Acciones</th>
          </tr>
        </thead>
        <!-- tbody = cuerpo de la tabla (las filas con datos) -->
        <tbody>
          <!-- v-for repite esta fila una vez por cada candidato.
               :key="c.id" ayuda a Vue a identificar cada fila de forma única -->
          <tr v-for="c in filtrados" :key="c.id">
            <!-- {{ }} inserta el valor de la variable como texto -->
            <td>{{ c.nombre }}</td>
            <td>{{ c.email }}</td>
            <td>{{ c.puesto }}</td>
            <td>{{ c.telefono }}</td>
            <td>
              <!-- class="estado" siempre se aplica.
                   :class="c.estado" agrega además la clase dinámica:
                   si el estado es "contratado", queda class="estado contratado"
                   y el CSS lo pinta de verde -->
              <span class="estado" :class="c.estado">{{ c.estado }}</span>
            </td>
            <td class="acciones">
              <!-- @click ejecuta la función al hacer clic.
                   Se le pasa el id del candidato y el nuevo estado -->
              <button class="verde" @click="estado(c.id,'contratado')">Contratar</button>
              <button class="rojo" @click="estado(c.id,'rechazado')">Rechazar</button>
              <button @click="borrar(c.id)">Eliminar</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </main>
</template>
