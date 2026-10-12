# SIGTAC — Sistema Integrado de Gestión de Triaje y Asignación de Camas

Prototipo de aplicación de escritorio para modelar el triaje y la asignación de camas
de una unidad de emergencia. Proyecto integrador del curso **Programación Orientada a
Objetos II** (Universidad Nacional del Callao).

> **Aviso:** es un proyecto académico. Los algoritmos de triaje (`models/estrategias.py`)
> son una **simulación didáctica**: sus umbrales y pesos no están validados clínicamente.
> No deben usarse con pacientes reales.

## Estado

En desarrollo. Ya existen la base de datos, los modelos del dominio y el DAO de
autenticación. Los controladores y la interfaz gráfica están pendientes. Todavía no hay
punto de entrada (`main.py`). Detalle en [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md)
y registro de cambios en [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

## Requisitos

- Python 3.12 o superior
- MySQL 8.0 o superior (el esquema usa `utf8mb4_0900_ai_ci` y restricciones `CHECK`;
  no funciona en MariaDB)

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Configuración

1. Copia la plantilla y completa tus datos:

   ```bash
   cp .env.example .env
   ```

2. Edita `.env` con el host, usuario, contraseña y nombre de la base de datos.
   Si falta alguna variable obligatoria, la aplicación se detiene con un mensaje claro.

3. Recomendado: no uses `root`. Crea un usuario con permisos solo sobre la base de datos:

   ```sql
   CREATE USER 'sigtac_app'@'localhost' IDENTIFIED BY '<una_clave_segura>';
   GRANT SELECT, INSERT, UPDATE ON sigtac_db.* TO 'sigtac_app'@'localhost';
   ```

   (Para ejecutar los scripts de la sección siguiente usa una cuenta con más permisos.)

## Base de datos

Los scripts están en `db_scripts/`:

| Script | Qué hace |
|---|---|
| `schema.sql` | Crea la base `sigtac_db` y sus tablas. **Borra las tablas existentes** (`DROP TABLE`). |
| `seed.sql` | Carga datos de prueba. **Vacía todas las tablas** (`TRUNCATE`) antes de insertar. |

```bash
mysql -u <usuario_admin> -p < db_scripts/schema.sql
mysql -u <usuario_admin> -p < db_scripts/seed.sql
```

> Ejecútalos solo en una base de desarrollo: destruyen los datos existentes.

Los usuarios de prueba del seed comparten la clave de desarrollo indicada en
[`docs/CHANGELOG.md`](docs/CHANGELOG.md). Nunca la uses fuera de un entorno local.

## Estructura

```text
SIGTAC/
├── dao/           Acceso a datos (conexión Singleton y DAOs)
├── models/        Modelos del dominio, estrategias de triaje y excepciones
├── utils/         Seguridad (bcrypt) y configuración de logging
├── db_scripts/    Esquema, datos de prueba y diagrama de la BD
├── docs/          Contexto, plan de desarrollo, estado y changelog
└── requirements.txt
```

Arquitectura por capas (vistas → controladores → modelos → DAO → MySQL) con los patrones
DAO, Strategy y Singleton. Más información en
[`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md).
