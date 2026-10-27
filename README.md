# Sistema de Contrataciones

Aplicación web para gestionar candidatos (nombre, correo, puesto, teléfono y estado).

## Tecnologías
- Frontend: Vue 3 + Vite, servido con Nginx
- Backend: FastAPI (Python) + SQLModel
- Base de datos: SQLite (volumen persistente)
- Contenedores: Podman / Docker Compose

## Ejecutar
    podman compose up -d --build

Abrir http://localhost:8080

## Estructura
- `backend/`: API (main.py, requirements.txt, Dockerfile)
- `frontend/`: interfaz Vue (src/, nginx.conf, Dockerfile)
- `docker-compose.yml`: orquesta ambos contenedores

## Funciones
- Alta de candidatos con validación
- Cambiar estado: pendiente, contratado, rechazado
- Eliminar candidatos
- Filtro por estado

## Historial de cambios

### v1.6 - Script de inicio
- `iniciar.sh` construye y levanta todo con un comando
- Espera a que el backend esté listo antes de abrir el frontend

### v1.5 - Validaciones en el backend
- Teléfono de 10 dígitos validado en la API
- Email único por candidato
- Mensajes de error visibles en pantalla

### v1.4 - Búsqueda y confirmación
- Buscador por nombre, email o puesto
- Confirmación antes de eliminar un candidato

### v1.3 - Contenedores por separado
- Backend y frontend ejecutables con `podman run`, sin compose
- Red `red-contrataciones` y volumen `datos` creados a mano
- Nueva sección "Ejecutar sin compose"

### v1.2 - Edición de candidatos
- Botón **Editar** que carga los datos en el formulario
- Nueva ruta `PUT /candidatos/{id}` en el backend
- Botón **Cancelar** para salir del modo edición

### v1.1 - Filtro y diseño
- Filtro por estado con contador de resultados
- Diseño en verde y dorado
- Teléfono obligatorio de 10 dígitos

### v1.0 - Primera versión
- Alta, cambio de estado y eliminación de candidatos
- Backend FastAPI + frontend Vue en contenedores Podman

## Ejecutar sin compose (contenedores por separado)

1. Construir las imágenes:

        podman build -t contrataciones_backend ./backend
        podman build -t contrataciones_frontend ./frontend

2. Crear la red y el volumen (la red permite que los contenedores se encuentren por nombre; el volumen guarda la base de datos):

        podman network create red-contrataciones
        podman volume create datos

3. Levantar el backend primero (sin puerto publicado):

        podman run -d --name backend --network red-contrataciones -v datos:/data localhost/contrataciones_backend

4. Levantar el frontend (publica el puerto 8080):

        podman run -d --name frontend --network red-contrataciones -p 8080:80 localhost/contrataciones_frontend

Abrir http://localhost:8080

Para detener: `podman stop frontend backend`. Para iniciar de nuevo: `podman start backend` y luego `podman start frontend`.
