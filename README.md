# SIGTAC — Sistema Integrado de Gestión de Triaje y Asignación de Camas

Prototipo de aplicación de escritorio para modelar el triaje y la asignación de camas
de una unidad de emergencia. Proyecto integrador del curso **Programación Orientada a
Objetos II** (Universidad Nacional del Callao).

> **Aviso:** es un proyecto académico. Los algoritmos de triaje (`models/estrategias.py`)
> son una **simulación didáctica**: sus umbrales y pesos no están validados clínicamente.
> No deben usarse con pacientes reales.

## Estado

La aplicación está completa: base de datos, modelos, acceso a datos, controladores e interfaz gráfica
(CustomTkinter). Está en la fase final de integración y pruebas: pasó una revisión de tester con los 13 casos
del plan y la verificación contra MySQL real. Detalle en [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md),
resumen para el equipo en [`docs/ESTADO_EQUIPO.md`](docs/ESTADO_EQUIPO.md) y registro de cambios en
[`docs/CHANGELOG.md`](docs/CHANGELOG.md).

### Pantallas

Cada rol ve solo los módulos que su rol permite.

| Pantalla | Qué hace |
|---|---|
| Inicio de sesión | Documento y clave; bloquea la cuenta tras 5 intentos fallidos durante 15 minutos |
| Tablero de camas | Indicadores, mapa de camas por tipo y quién espera cama; se actualiza cada 30 s |
| Triaje | Registra al paciente (con documento o sin identificar), sugiere el nivel y permite reclasificar con justificación |
| Gestión de camas | Asigna una cama compatible, registra la llegada, el alta, la referencia o la fuga, y el mantenimiento |
| Pacientes | Busca, corrige datos, abre un episodio e identifica a los pacientes sin identificar |
| Limpieza | Confirma que una cama dada de alta quedó limpia |
| Reportes | Indicadores de un período y exportación a PDF |
| Administración | Cuentas de usuario, roles, claves, bitácora y baja o reactivación de pacientes |

Tiene modo claro y oscuro, y se puede usar con el teclado.

## Requisitos

- Python 3.12 o superior
- MySQL 8.0 o superior (el esquema usa `utf8mb4_0900_ai_ci`, restricciones `CHECK`, columnas
  generadas y el tipo `JSON`). También se ha probado con MariaDB 11.8; no con versiones
  anteriores de MariaDB.

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

3. Recomendado: no uses `root`. Crea un usuario con permisos solo sobre la base de datos ejecutando
   `db_scripts/crear_usuario_app.sql` como administrador (por ejemplo, en MySQL Workbench), tras reemplazar
   `<una_clave_segura>`. Equivale a:

   ```sql
   CREATE USER 'sigtac_app'@'localhost' IDENTIFIED BY '<una_clave_segura>';
   GRANT SELECT, INSERT, UPDATE ON sigtac_db.* TO 'sigtac_app'@'localhost';
   ```

   Sin `DELETE` (RN-11: no hay borrado físico) ni `DROP`/`CREATE`/`ALTER`.

   `UPDATE` es necesario para el bloqueo temporal de cuentas por intentos fallidos.
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

Los usuarios de prueba del seed (documento, rol y clave de desarrollo) están en el comentario sobre
`INSERT INTO usuario` de [`db_scripts/seed.sql`](db_scripts/seed.sql). Nunca uses esas claves fuera de un entorno local.

## Abrir la aplicación

```bash
python main.py              # la aplicación real: necesita el .env y MySQL
python -m prototipo.ver     # una demostración con datos inventados, sin MySQL ni .env
```

La demostración acepta `--rol` (p. ej. `--rol "Enfermero de Triaje"`), `--modo oscuro` y `--tamano 1093x614`.

## Pruebas

Las pruebas usan `pytest` y **no necesitan MySQL ni un `.env`**: la base de datos se simula.

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Para comprobar el flujo completo contra MySQL real, en una base temporal que se crea y se borra (no toca
`sigtac_db`; pide la clave de una cuenta de administrador):

```bash
python scripts/verificar_controladores.py
```

## Estructura

```text
SIGTAC/
├── main.py        Punto de entrada: el inicio de sesión y la ventana principal
├── views/         Interfaz (CustomTkinter): las pantallas, sus piezas compartidas y el tema
├── controllers/   Casos de uso y permisos por rol
├── models/        Modelos del dominio, estrategias de triaje y excepciones
├── dao/           Acceso a datos (conexión Singleton y DAOs)
├── utils/         Seguridad (bcrypt), logging, reporte PDF y colores compartidos
├── prototipo/     Controladores de demostración para abrir la app sin MySQL
├── db_scripts/    Esquema, datos de prueba y diagrama de la BD
├── scripts/       Verificación del flujo completo contra MySQL real
├── tests/         Pruebas automáticas (pytest)
├── docs/          Contexto, plan de desarrollo, estado, changelog y diseño
└── requirements.txt
```

Arquitectura por capas (vistas → controladores → modelos → DAO → MySQL) con los patrones
DAO, Strategy y Singleton. Más información en
[`docs/PROJECT_CONTEXT.md`](docs/PROJECT_CONTEXT.md).
