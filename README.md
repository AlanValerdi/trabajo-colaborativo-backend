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
docker compose build
docker compose up
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

## Carga por área y técnico

Solo los roles `coordinador` y `responsable_area` pueden consultar:

- `GET /workload`: resumen y agrupaciones `byArea`, `byTechnician`, `byAreaAndTechnician`.
- `GET /workload/reports?pendingOnly=true&limit=50&offset=0`: detalle paginado con `items` y `total`.

Enviar `Authorization: Bearer <access_token>`. Ambos aceptan `specialtyId` y
`assigneeId`; el detalle también `status` y `priority`. Los filtros se combinan
con AND. Ejemplo: `/workload/reports?specialtyId=1&assigneeId=5&status=en_progreso`.
Pendientes excluye resueltas y cerradas. Se cuenta la asignación actual, sin sumar
colaboraciones ni asignaciones anteriores. Las áreas son especialidades. Los
registros sin área o técnico tienen ID nulo; `unclassified` identifica la prioridad
sin definir. Ambos roles ven todas las áreas. Los técnicos activos y las
especialidades sin carga aparecen con cero; los técnicos inactivos con carga se
conservan en el resumen.

Pruebas de carga funcional (solo lectura de datos):
`python -m unittest discover -s tests -p test_workload.py -v`.

## HU-27 a HU-30: reportes y atención

Los endpoints requieren `Authorization: Bearer <access_token>`.

| Endpoint | Uso | Acceso |
|---|---|---|
| `GET /analytics/summary` | Totales, distribución por estado/área, promedios y tamaño de muestra | Administrador, coordinador, responsable de área |
| `GET /analytics/reports` | Detalle paginado con tiempos y calificación | Los mismos roles |
| `GET /analytics/export` | Todos los resultados filtrados como CSV UTF-8 | Los mismos roles |
| `GET /reports/{folio}/attention-times` | Tiempos de una incidencia | Autor, técnico asignado y roles de gestión |
| `GET /reports/{folio}/evaluation` | Evaluación o `null` si no existe | Los mismos usuarios |
| `POST /reports/{folio}/evaluation` | Evaluación única de una incidencia cerrada | Exclusivamente el autor |

Los tres endpoints de analítica comparten los filtros `start_date`, `end_date`
(fechas ISO `YYYY-MM-DD`), `campus_id`, `specialty_id`, `assignee_id`, `status`
y `priority`. Se combinan con AND. Las fechas filtran la **creación** del reporte,
incluyendo ambos días en UTC; los estados, área y técnico representan su situación
actual, no una reconstrucción histórica. El detalle acepta además `limit` (1–200,
por defecto 25) y `offset` (desde 0). El CSV exporta el conjunto completo filtrado,
independientemente de la página, con comillas y saltos de línea escapados y
neutralización de fórmulas de hoja de cálculo. Las consultas se procesan en lotes.

Los tiempos son horas naturales desde la creación, incluyendo períodos bloqueados:

- Primera atención: primer evento `en_progreso`.
- Resolución: último evento `resuelta`, solo si el estado actual es resuelta o cerrada.
- Cierre: último evento `cerrada`, solo si actualmente está cerrada.
- Tiempo abierta: antigüedad actual para estados distintos de resuelta/cerrada.

Los hitos sin historial válido se devuelven como `null` y se excluyen de los
promedios; cada promedio incluye su tamaño de muestra. Una reapertura invalida el
tiempo final hasta una nueva resolución. Las fechas de salida incluyen zona UTC.
No se calculan tiempos de jornada laboral ni SLA porque no existe un calendario
de servicio configurado.

La evaluación recibe `{"rating": 5, "comment": "Buena atención"}`: entero de 1 a 5,
comentario opcional de hasta 1000 caracteres. Se permite una sola evaluación por
incidencia, sin edición. Se conserva si posteriormente se reabre la incidencia.
Los intentos duplicados o sobre incidencias abiertas devuelven 409; un usuario
distinto del autor recibe 403. La restricción única en la base de datos protege
también frente a solicitudes concurrentes. Migración: `k1f2a3b4c5d6`.

La implementación mantiene límites por responsabilidad: `routers/analytics.py`
adapta HTTP; `services/analytics.py` genera los reportes y exportaciones;
`services/attention.py` aplica permisos y reglas de evaluación;
`repositories/analytics.py` concentra consultas SQL; `domain/attention.py`
calcula tiempos sin dependencias de HTTP o persistencia; `schemas/analytics.py`
define los contratos y `models/attention_evaluation.py` la persistencia.

Pruebas aisladas con SQLite en memoria, sin modificar MySQL:

```bash
python -m unittest discover -s tests -p test_analytics.py -v
```
