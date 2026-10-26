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
