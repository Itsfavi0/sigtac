# Los 8 criterios: qué mostrar y dónde está

Cada criterio dice qué pide el profesor, qué mostramos y qué decimos. El código citado es el real del repositorio.

---

## 1. Corrección de las observaciones

Ver [OBSERVACIONES.md](OBSERVACIONES.md). En resumen: preguntó cómo migrar a otro motor de base de datos; respondimos
que solo se tocan los DAO, y ahora lo demostramos (MySQL se importa solo en 3 archivos de `dao/` y una prueba lo exige).

---

## 2. Diseño de clases y objetos

Pide: clases principales, qué representa cada una, qué datos guarda y qué operaciones realiza.

| Clase | Archivo | Qué representa | Datos que guarda | Operaciones |
|---|---|---|---|---|
| `Persona` (abstracta) | `models/persona.py` | Cualquier persona del sistema | documento, nombres, apellidos, fecha de nacimiento | `calcular_edad()`, `obtener_resumen()` (abstracto) |
| `Paciente` | `models/persona.py` | Quien llega a emergencia; puede no estar identificado (NN) | sexo, seguro, activo | `identificar()`, `actualizar_datos()`, `anular()`, `reactivar()` |
| `Empleado` y sus hijas | `models/persona.py` | Personal: `Enfermero`, `Medico`, `PersonalLimpieza` | cargo, colegiatura; área, especialidad o turno | `obtener_resumen()` propio de cada una |
| `DocumentoIdentidad` | `models/documento.py` | Un documento (tipo + número) | tipo, número | Se valida al crearse; no cambia después |
| `EpisodioEmergencia` | `models/triaje.py` | Una visita del paciente a emergencia | motivo, estado, fechas, sus triajes y signos | `agregar_triaje()`, `asignar_cama()`, `dar_alta()`, `referir()`, `registrar_fuga()` |
| `SignosVitales` | `models/triaje.py` | Una toma de signos | presión, FC, FR, temperatura, SatO₂ | Valida rangos al crearse |
| `Triaje` | `models/triaje.py` | Una clasificación de prioridad | nivel sugerido, nivel final, justificación, síntomas | `agregar_sintoma()`, `reclasificar()` |
| `Cama` (abstracta) y 4 hijas | `models/cama.py` | Una cama física | código, área, estado | `reservar()`, `ocupar()`, `dar_alta()`, `liberar_limpieza()`, `es_compatible()` |
| `EstrategiaTriaje` y 2 hijas | `models/estrategias.py` | Un algoritmo de clasificación | — | `evaluar()`, `clasificar()`, `justificar()` |
| `CuentaUsuario` | `models/usuario.py` | El acceso de un empleado al sistema | rol, activo, intentos fallidos | `activar()`, `desactivar()`, `cambiar_rol()`, `desbloquear()` |

**Qué decir:** «Cada clase es una cosa del hospital. Un paciente existe siempre; un episodio es una visita.
Por eso son dos clases: un paciente puede venir diez veces al año.»

---

## 3. Encapsulamiento

Pide: cómo una clase controla el acceso o la modificación de sus datos; un método que impide un valor inválido.

### Ejemplo principal — el estado de una cama (`models/cama.py`)

```python
class Cama(ABC):
    def __init__(self, id_cama, codigo, area, estado: str = ESTADO_DISPONIBLE):
        self._estado = EstadoCama(estado)  # ValueError si el estado no existe

    @property
    def estado(self): return self._estado          # se puede leer...

    def reservar(self):                            # ...pero solo cambia por aquí
        """RN-05: Solo se puede reservar si está disponible."""
        if self._estado != Cama.ESTADO_DISPONIBLE:
            raise CamaEstadoInvalidoError(
                f"No se puede reservar la cama {self.codigo} desde el estado «{self._estado.texto}».")
        self._estado = Cama.ESTADO_RESERVADA
```

**Qué decir:**

- El atributo es `_estado` (protegido). Desde fuera solo se **lee**, con `@property`. No hay *setter*.
- `cama.estado = "OCUPADA"` da error: Python responde `AttributeError`, porque la propiedad no tiene *setter*.
- La única forma de cambiarlo es un método con nombre de acción (`reservar`, `ocupar`, `dar_alta`), y cada uno
  comprueba que la transición sea válida. Una cama ocupada no se puede reservar.

### Segundo ejemplo — valores imposibles (`models/triaje.py`)

```python
class SignosVitales:
    RANGOS = {'pa_sis': (20, 300), 'pa_dia': (0, 250), 'fc': (0, 300),
              'fr': (0, 80), 'temp': (25.0, 45.0), 'sato2': (0, 100)}

    def __init__(self, pa_sis, pa_dia, fc, fr, temp, sato2, id_si):
        for nombre, valor in valores.items():
            minimo, maximo = self.RANGOS[nombre]
            if not (minimo <= valor <= maximo):
                raise ValueError(f"{nombre} fuera del rango admitido ({minimo}-{maximo}): {valor}")
        self.validar_presion(pa_sis, pa_dia)   # la sistólica debe ser mayor que la diastólica
```

**Qué decir:** «No puede existir un objeto `SignosVitales` con una saturación de 150 %. El objeto se valida al
nacer, así que cualquier objeto que exista ya es válido.»

### Tercer ejemplo — reclasificar exige justificación (`Triaje.reclasificar`, RN-10)

```python
def reclasificar(self, nuevo_nivel: int, justificacion: str):
    if not _es_nivel_valido(nuevo_nivel):
        raise NivelTriajeInvalidoError("El nivel de triaje debe estar entre 1 (Rojo) y 5 (Azul).")
    if not justificacion or len(justificacion.strip()) < self.MIN_JUSTIFICACION:   # 10
        raise ValueError("Debe proporcionar una justificación médica válida (mínimo 10 caracteres).")
    self._nivel_final = nuevo_nivel
    self._justificacion = justificacion
```

Este se ve **en vivo** en la demo (paso 4 del guion).

---

## 4. Relaciones entre clases

Pide: cómo colaboran dos o más objetos en una operación; asociación, composición, herencia o polimorfismo **que aplicaron**.

| Relación | Dónde | Por qué se usó |
|---|---|---|
| **Herencia** | `Persona` → `Paciente`, `Empleado` → `Enfermero`, `Medico`, `PersonalLimpieza` | Un enfermero **es un** empleado y **es una** persona |
| **Herencia** | `Cama` → `CamaTraumaShock`, `CamaUCI`, `CamaObservacion`, `CamaHospitalizacion` | Todas son camas, pero admiten niveles distintos |
| **Clase abstracta** | `Persona`, `Cama`, `EstrategiaTriaje` (con `ABC`) | No existe «una cama genérica»: siempre es de un tipo |
| **Polimorfismo** | `es_compatible(nivel)` en cada tipo de cama | El mismo mensaje, cuatro respuestas |
| **Polimorfismo** | `evaluar()` en `ReglaManchester` y `ReglaMINSA` | Cambiar de algoritmo sin tocar el controlador (patrón Strategy) |
| **Composición** | `EpisodioEmergencia` contiene sus `Triaje` y `SignosVitales`; `Triaje` contiene sus `Sintoma` | Un triaje no existe sin su episodio |
| **Asociación** | `AsignacionCama` une un episodio con una cama | Ninguno contiene al otro: se relacionan durante un tiempo |
| **Asociación** | `Persona` usa un `DocumentoIdentidad`; `CuentaUsuario` se refiere a un empleado y a un `Rol` | — |

### El polimorfismo en cuatro líneas (`models/cama.py`)

```python
class CamaTraumaShock(Cama):
    def es_compatible(self, nivel_triaje): return nivel_triaje == 1          # solo nivel I
class CamaUCI(Cama):
    def es_compatible(self, nivel_triaje): return nivel_triaje in (1, 2)
class CamaObservacion(Cama):
    def es_compatible(self, nivel_triaje): return nivel_triaje in (2, 3, 4)
class CamaHospitalizacion(Cama):
    def es_compatible(self, nivel_triaje): return nivel_triaje in (3, 4, 5)
```

Y quien lo usa (`controllers/cama_controller.py`) no pregunta de qué tipo es cada cama:

```python
return [cama for cama in CamaDAO.listar_disponibles() if cama.es_compatible(nivel)]
```

**Qué decir:** «El controlador nunca pregunta de qué tipo es la cama. Si mañana se agrega una cama pediátrica,
se crea una clase nueva y esta línea no se toca.»

### Objetos que colaboran: asignar una cama (`CamaController.asignar`)

```python
sesion = exigir_permiso(self._sesion, Permiso.GESTION_CAMAS)     # 1. ¿puede este rol?
with transaccion():                                             # 2. todo o nada
    episodio = self._cargar_episodio(id_episodio)
    cama = self._cargar_cama(id_cama)
    episodio.asignar_cama()                                     # 3. el episodio valida RN-01
    nivel = episodio.nivel_actual
    if not cama.es_compatible(nivel):                           # 4. la cama responde (polimorfismo)
        raise ReglaNegocioError(...)
    cama.reservar()                                             # 5. la cama valida RN-05
    EpisodioDAO.cambiar_estado(episodio, anterior_ep)           # 6. los DAO guardan
    CamaDAO.cambiar_estado(cama, anterior_cama)
    id_asignacion = AsignacionDAO.crear(id_episodio, id_cama, sesion.id_empleado)
    AuditoriaDAO.registrar(...)                                 # 7. queda en la bitácora
```

**Qué decir:** «Colaboran la sesión, el episodio, la cama, la asignación y la bitácora.
Cada uno decide lo suyo: el episodio sabe si tiene triaje, la cama sabe si está disponible y si es compatible.
El controlador solo los coordina. Si algo falla, la transacción deshace todo.»

---

## 5. Avances funcionales

Pide: ejecutar el proyecto y demostrar al menos una funcionalidad. Mostramos el flujo completo:
ver [GUION_DEMO.md](GUION_DEMO.md).

Lo que funciona hoy: 8 pantallas (login, tablero, triaje, gestión de camas, pacientes, limpieza, reportes y
administración), 5 roles y la base de datos MySQL.

---

## 6. Validación de datos y manejo de errores

Pide: probar un caso con datos incorrectos, incompletos o duplicados y mostrar cómo responde el sistema.

| Tipo | Caso en la demo | Respuesta del sistema | Dónde vive la regla |
|---|---|---|---|
| **Incorrecto** | Presión diastólica mayor que la sistólica | Marca los dos campos; el botón dice «Corrija los signos vitales» | `SignosVitales.validar_presion` |
| **Incompleto** | Reclasificar con una justificación de 2 letras | El botón no deja continuar: «Faltan 8 caracteres (mínimo 10)» (RN-10) | `Triaje.reclasificar` |
| **Duplicado** | Abrir otro episodio a un paciente que ya está en emergencia | «El paciente ya tiene un episodio abierto…» | `PacienteController.abrir_episodio` |
| Incorrecto | Clave equivocada en el login | No dice si falló el documento o la clave; 5 fallos bloquean 15 min | `UsuarioDAO.autenticar` |

**Cómo se manejan los errores (para explicar):**

- `ValueError` = dato de entrada inválido. `SigtacError` y sus hijas = regla de negocio violada (`models/excepciones.py`).
- El modelo lanza el error; el controlador **no** lo captura; la pantalla lo muestra con un mensaje claro.
- Nunca se usa `except Exception`: se capturan errores específicos.
- Si el error ocurre a mitad de una operación, la transacción hace ROLLBACK: no queda nada guardado a medias.
- Las reglas críticas también están en la base de datos (`UNIQUE`, `CHECK`), por si dos PCs actúan a la vez.

---

## 7. Organización y legibilidad del código

Pide: cómo se organiza el código en archivos, clases y métodos; nombres claros.

```text
views/        Pantallas (CustomTkinter). Nunca SQL ni reglas de negocio.
controllers/  Casos de uso y permisos por rol.
models/       Las clases del dominio y las reglas de negocio.
dao/          El único lugar con SQL.
utils/        Contraseñas (bcrypt), PDF, registro de eventos.
db_scripts/   schema.sql y seed.sql.
tests/        Una prueba por módulo: test_cama.py prueba models/cama.py.
```

```text
views → controllers → models → dao → MySQL        (las dependencias van solo hacia abajo)
```

**Qué mostrar:** el árbol de carpetas en el editor y un nombre de cada capa:
`triage_view.py` → `TriajeController.registrar()` → `Triaje.reclasificar()` → `TriajeDAO`.

**Qué decir:**

- Los nombres están en español y dicen lo que hacen: `cama.reservar()`, `episodio.dar_alta()`, `exigir_permiso()`.
- Un archivo por tema; una regla tiene un solo dueño (no se repite en dos capas).
- Los colores y las letras de todas las pantallas salen de un solo archivo, `views/tema.py`.
- Tamaño: unas 11 400 líneas de aplicación y 13 000 de pruebas.

---

## 8. Sustentación técnica

Pide: explicar una decisión tomada y responder preguntas; cada integrante explica su contribución.

### La decisión que explicamos: la compatibilidad cama–paciente se decide con polimorfismo, no en SQL

- **El problema:** ¿qué camas sirven para un paciente de nivel 2?
- **La primera idea:** una columna `nivel_min` en la tabla `tipo_cama` y un `WHERE` con ese número en SQL.
- **Por qué se descartó:** un solo número no alcanza. Observación acepta los niveles 2, 3 y 4; Hospitalización, 3, 4
  y 5. No es «de tal nivel en adelante». Además la regla quedaba escrita dos veces (en SQL y en Python) y se contradecían.
- **Lo que se hizo:** la regla vive en un solo lugar, `Cama.es_compatible()`. El DAO trae las camas disponibles y
  cada cama responde por sí misma.
- **Lo que costó:** se filtra en Python y no en la base de datos. Con las camas de una emergencia (decenas) no se nota; con miles habría que revisarlo.

Otras decisiones que se pueden contar si preguntan: separar `rol` de `cargo`; baja lógica en lugar de borrar
(RN-11); `UPDATE` condicional para que dos PCs no reserven la misma cama.

Las contribuciones de cada integrante están en [HOJAS_DE_ESTUDIO.md](HOJAS_DE_ESTUDIO.md).

---

## Aportes adicionales (hay que declararlos expresamente)

| Aporte | Qué se agregó | Cómo se demuestra |
|---|---|---|
| **Base de datos MySQL** | 22 tablas, transacciones, claves foráneas | Registrar un paciente, cerrar la aplicación, abrirla y buscarlo |
| **Reporte PDF** | Indicadores de un período (ReportLab) | Exportar y abrir el PDF |
| **Búsqueda** | Paciente por documento; pacientes con cama por nombre | Buscar en Triaje y en Gestión de camas |
| **Roles y permisos** | 5 roles; cada uno ve solo sus módulos | Entrar como Limpieza: solo ve Tablero y Limpieza |
| **Bitácora de auditoría** | Quién hizo qué y cuándo | Administración → Bitácora, después de la demo |
| **Seguridad** | Claves con bcrypt; bloqueo tras 5 intentos | Mostrar la columna `hash_clave` |
| **Pruebas automáticas** | 2 332 pruebas (`python -m pytest`) | Correrlas, o mostrar el resultado |
| **Modo oscuro** | Toda la interfaz en claro y oscuro | El interruptor del menú |
