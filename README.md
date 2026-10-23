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
