# Sistema de Contrataciones

Aplicación web para gestionar candidatos (nombre, correo, puesto, teléfono y estado), ejecutada en contenedores con Podman.

## Tecnologías
- Frontend: Vue 3 + Vite, servido con Nginx
- Backend: FastAPI (Python) + SQLModel
- Base de datos: SQLite (volumen persistente)
- Contenedores: Podman (también compatible con Docker)

## Requisitos
- Podman instalado
- Git

## Ejecutar (recomendado)

    git clone https://github.com/KevinAlva23/sistema-contrataciones.git
    cd sistema-contrataciones
    chmod +x iniciar.sh
    ./iniciar.sh

Abrir http://localhost:8080

El script construye las imágenes, crea la red y el volumen si no existen, levanta el backend, espera a que esté listo y después levanta el frontend.

Para apagar todo (los datos se conservan en el volumen):

    ./iniciar.sh detener

## Ejecutar con compose (alternativa)

    podman compose up -d --build

No uses compose y el script al mismo tiempo: ambos usan el puerto 8080 y nombres de contenedor que chocan. Para cambiar de método, apaga primero el anterior.

## Estructura
- `iniciar.sh`: construye y levanta todo con un comando
- `docker-compose.yml`: alternativa con compose
- `backend/`: API (`main.py`, `requirements.txt`, `Dockerfile`)
- `frontend/`: interfaz Vue (`src/`, `nginx.conf`, `Dockerfile`)

## Arquitectura
- El navegador entra por el puerto 8080 al contenedor `frontend` (Nginx).
- Nginx sirve la interfaz y reenvía `/api` al contenedor `backend` (FastAPI).
- Los dos contenedores comparten la red `red-contrataciones` y se encuentran por nombre.
- La base de datos SQLite vive en el volumen `datos`, así sobrevive aunque se borren los contenedores.
- Solo el frontend publica un puerto; el backend no es accesible desde fuera.

## Funciones
- Alta de candidatos con validación (frontend y backend)
- Edición de candidatos
- Cambiar estado: pendiente, contratado, rechazado
- Eliminar candidatos con confirmación
- Búsqueda por nombre, email o puesto
- Filtro por estado
- Email único y teléfono de 10 dígitos

## API
Documentación interactiva en http://localhost:8080/api/docs

- `GET /candidatos`: lista
- `POST /candidatos`: crea
- `PUT /candidatos/{id}`: edita datos
- `PATCH /candidatos/{id}?estado=...`: cambia el estado
- `DELETE /candidatos/{id}`: elimina

## Comandos útiles

    podman ps                  # ver contenedores
    podman logs -f backend     # logs del backend
    podman logs -f frontend    # logs del frontend

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
- Red `red-contrataciones` y volumen `datos`

### v1.2 - Edición de candidatos
- Botón Editar que carga los datos en el formulario
- Ruta `PUT /candidatos/{id}` en el backend
- Botón Cancelar para salir del modo edición

### v1.1 - Filtro y diseño
- Filtro por estado con contador de resultados
- Diseño en verde y dorado
- Teléfono obligatorio de 10 dígitos

### v1.0 - Primera versión
- Alta, cambio de estado y eliminación de candidatos
- Backend FastAPI y frontend Vue en contenedores Podman
