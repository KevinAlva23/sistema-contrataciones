# Sistema de Contrataciones

Aplicación web para gestionar candidatos (nombre, correo, puesto, teléfono y estado), con inicio de sesión y roles, ejecutada en contenedores con Podman.

## Tecnologías
- Frontend: Vue 3 + Vite, servido con Nginx
- Backend: FastAPI (Python) + SQLModel
- Base de datos: SQLite (volumen persistente)
- Seguridad: contraseñas con bcrypt y sesiones JWT
- Contenedores: Podman (también compatible con Docker)

## Requisitos
- Podman instalado
- Git

## Configuración inicial (archivo .env)

Antes de la primera ejecución, crea un archivo `.env` en la raíz del proyecto. **No se sube a GitHub** (está en `.gitignore`):

    SECRET_KEY=pulsarns200
    ADMIN_USER=admin
    ADMIN_PASSWORD=Kev210905

- `SECRET_KEY`: firma los tokens de sesión.
- `ADMIN_USER` y `ADMIN_PASSWORD`: crean el primer administrador al arrancar, solo si la base no tiene usuarios.

Protege el archivo:

    chmod 600 .env

## Ejecutar

    git clone https://github.com/KevinAlva23/sistema-contrataciones.git
    cd sistema-contrataciones
    chmod +x iniciar.sh
    ./iniciar.sh

Abrir http://localhost:8080

El script construye las imágenes, crea la red y el volumen si no existen, levanta el backend, espera a que esté listo y después levanta el frontend.

Para apagar todo (los datos se conservan en el volumen):

    ./iniciar.sh detener

## Roles y permisos

| Rol | Ver | Agregar y editar | Contratar / rechazar | Eliminar | Gestionar usuarios |
|---|---|---|---|---|---|
| admin | Sí | Sí | Sí | Sí | Sí |
| reclutador | Sí | Sí | Sí | No | No |
| auditor | Sí | No | No | No | No |

- Los permisos se validan en el backend; ocultar botones en la pantalla no es la única protección.
- Las sesiones caducan a las 8 horas.
- El auditor es de solo lectura: ve la tabla, sin formulario ni acciones.

## Crear usuarios

Con el sistema en marcha, un administrador puede crear cuentas desde http://localhost:8080/api/docs (botón Authorize con el token de `POST /login`, y luego `POST /usuarios`) con el rol `reclutador` o `auditor`. La contraseña debe tener al menos 8 caracteres.

## Estructura
- `iniciar.sh`: construye y levanta todo con un comando
- `docker-compose.yml`: alternativa con compose (no usar a la vez que el script)
- `backend/`: API (`main.py`, `requirements.txt`, `Dockerfile`)
- `frontend/`: interfaz Vue (`src/`, `nginx.conf`, `Dockerfile`)
- `.env`: secretos locales (no se sube a GitHub)

## Arquitectura
- El navegador entra por el puerto 8080 al contenedor `frontend` (Nginx).
- Nginx sirve la interfaz y reenvía `/api` al contenedor `backend` (FastAPI).
- Los dos contenedores comparten la red `red-contrataciones` y se encuentran por nombre.
- La base de datos SQLite vive en el volumen `datos`, así sobrevive aunque se borren los contenedores.
- Solo el frontend publica un puerto; el backend no es accesible desde fuera.

## Funciones
- Inicio de sesión con roles (admin, reclutador, auditor)
- Alta de candidatos con validación (frontend y backend)
- Edición de candidatos
- Cambiar estado: pendiente, contratado, rechazado
- Eliminar candidatos con confirmación (solo admin)
- Búsqueda por nombre, email o puesto
- Filtro por estado
- Email único y teléfono de 10 dígitos

## API
Documentación interactiva en http://localhost:8080/api/docs

- `POST /login`: inicia sesión y devuelve el token
- `GET /yo`: datos del usuario actual
- `GET /usuarios`, `POST /usuarios`, `DELETE /usuarios/{id}`: gestión de usuarios (admin)
- `GET /candidatos`: lista (todos los roles)
- `POST /candidatos`: crea (admin, reclutador)
- `PUT /candidatos/{id}`: edita datos (admin, reclutador)
- `PATCH /candidatos/{id}?estado=...`: cambia el estado (admin, reclutador)
- `DELETE /candidatos/{id}`: elimina (admin)

## Comandos útiles

    podman ps                  # ver contenedores
    podman logs -f backend     # logs del backend
    podman logs -f frontend    # logs del frontend

## Respaldos

    ./respaldo.sh                      # crea un respaldo con fecha
    ./respaldo.sh listar               # lista los respaldos
    ./respaldo.sh restaurar ARCHIVO    # restaura uno

La carpeta `respaldos/` no se sube a GitHub: contiene datos personales.

## Pruebas

    cd backend
    pip install -r requirements.txt -r requirements-dev.txt
    pytest

## Historial de cambios

### v1.13 - Pruebas automáticas
- Pruebas con pytest de login, roles, validaciones, bloqueo y bitácora
- GitHub Actions ejecuta las pruebas y compila el frontend en cada push
- La ruta de la base se puede configurar con `DATABASE_URL`
- Corrección de las respuestas de crear candidato y cambiar estado

### v1.12 - Respaldos
- `respaldo.sh` crea copias seguras de la base de datos con fecha
- Conserva los últimos 14 respaldos y permite programarlos con cron
- Restauración con `./respaldo.sh restaurar ARCHIVO`

### v1.11 - Bitácora de auditoría
- Registro de quién crea, edita, cambia el estado o elimina candidatos
- Registro de altas y cambios de usuarios, inicios de sesión y accesos fallidos
- Pestaña Bitácora para admin y auditor (solo lectura)

### v1.10 - Administración de usuarios
- Pantalla para crear, activar/desactivar y eliminar usuarios
- Cambio de rol y restablecimiento de contraseña
- Protección para no quedarse sin administrador

### v1.9 - Seguridad de acceso
- Bloqueo de 10 minutos tras 5 intentos fallidos de login

### v1.8 - Rediseño
- Barra superior con usuario y rol
- Tarjetas de resumen por estado
- Formulario, filtros y tabla en paneles
- Diseño adaptable a celular

### v1.7 - Usuarios y roles
- Login con contraseñas cifradas (bcrypt) y sesión JWT de 8 horas
- Roles: admin, reclutador y auditor (solo lectura)
- Permisos validados en el backend
- Botones visibles según el rol
- Configuración de secretos con archivo `.env`

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
- Backend y frontend en contenedores independientes
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
