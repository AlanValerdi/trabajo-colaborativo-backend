# trabajo-colaborativo-backend

API REST con FastAPI, MySQL y arquitectura en capas (routers → services → models).

- Docker Engine 24+
- Docker Compose v2+

### 2. Comandos básicos de Docker

| Comando                                 | Descripción |
|---------                                |-------------|
| `docker ps`                             | Contenedores en ejecución |
| `docker ps -a`                          | Todos los contenedores |
| `docker images`                         | Imágenes locales |
| `docker compose up`                     | Levantar servicios definidos en `docker-compose.yml` |
| `docker compose up -d`                  | Levantar en segundo plano |
| `docker compose down`                   | Detener y eliminar contenedores |
| `docker compose logs -f`                | Ver logs en tiempo real |
| `docker compose exec <servicio> <cmd>`  | Ejecutar comando dentro de un contenedor |


El archivo `.env` define la URL de conexión a MySQL y las credenciales.

### 4. Construir y levantar los contenedores

```bash
docker compose up --build -d
```

Esto hará lo siguiente:

1. Descargará la imagen de MySQL 8.0
2. Construirá la imagen de la API (FastAPI)
3. Iniciará MySQL y esperará a que esté saludable (`healthcheck`)
4. Iniciará la API en el puerto **8000** con hot reload

Verifica que ambos servicios estén corriendo:

```bash
docker compose ps
```

Deberías ver `db` y `api` en estado `running` (y `db` como `healthy`).

### 5. Ejecutar las migraciones

Una vez que MySQL esté listo, aplica las migraciones de Alembic manualmente:

```bash
docker compose exec api alembic upgrade head
```

Deberías ver un mensaje similar a:

```
INFO  [alembic.runtime.migration] Running upgrade  -> a1b2c3d4e5f6, create users table
```

### 6. Verificar que la tabla `users` existe

```bash
docker compose exec db mysql -uapp_user -papp_password app_db -e "SHOW TABLES; DESCRIBE users;"
```

Deberías ver la tabla `users` con las columnas `id` y `name`. (Puedes utilizar un gestor de db...)

### 7. Probar la API

- Documentación interactiva (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

### 8. Hot reload (desarrollo)

El servicio `api` monta la carpeta local `./app` dentro del contenedor y ejecuta uvicorn con `--reload`. Al guardar un archivo `.py`, la API se reinicia automáticamente.

```bash
docker compose logs -f api
```

Si cambias `requirements.txt` o el `Dockerfile`, reconstruye la imagen:

```bash
docker compose up --build -d
```

### 9. Comandos útiles del día a día

```bash
# Ver estado de los servicios
docker compose ps

# Ver logs de la API
docker compose logs -f api

# Ver logs de MySQL
docker compose logs -f db

# Aplicar migraciones (tras cambios en alembic/versions/)
docker compose exec api alembic upgrade head

# Ver historial de migraciones
docker compose exec api alembic history

# Revertir última migración
docker compose exec api alembic downgrade -1

# Detener todo
docker compose down

# Detener y eliminar volúmenes (borra datos de MySQL)
docker compose down -v
```

## Arquitectura en capas

```
app/
├── core/config.py      # Configuración (variables de entorno)
├── db/database.py      # Conexión SQLAlchemy + sesión
├── models/user.py      # Modelo de datos (SQLModel)
├── schemas/user.py     # DTOs Pydantic (entrada/salida)
├── services/user.py    # Lógica de negocio
├── routers/user.py     # Endpoints HTTP
└── main.py             # Punto de entrada FastAPI
```
