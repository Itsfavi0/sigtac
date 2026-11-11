# Contenido de las diapositivas (para pasar al Canva)

14 diapositivas para 15 minutos. Siguen el orden de los 8 criterios del profesor, para que pueda ir marcando su lista.

**Reglas de diseño (para que se lea desde el fondo del aula):**

- Una idea por diapositiva. Máximo 25 palabras, sin contar el código.
- Letra de 28 puntos o más; el código, de 20 o más y con fuente monoespaciada (JetBrains Mono, Fira Code).
- En una esquina, el número del criterio: «Criterio 3 de 8».
- Colores de la aplicación (`views/tema.py`): azul `#2563B8` para los títulos, fondo `#ECEFF3`, texto `#252A31`.
  Niveles de triaje (`utils/colores.py`): 1 rojo `#D93025`, 2 naranja `#E8710A`, 3 amarillo `#F9AB00`,
  4 verde `#188038` y 5 azul `#1967D2`.
- Las capturas están en `docs/sustentacion/capturas/` (1280 × 720).
- Animaciones: solo «aparecer» para revelar el código por partes. Nada que gire ni rebote.

---

## 1. Portada

**SIGTAC**
Sistema Integrado de Gestión de Triaje y Asignación de Camas

Programación Orientada a Objetos II · Universidad Nacional del Callao · 2026-B
Brañez · Moya · Veliz · Sevillano · Malpartida

*Imagen:* `capturas/tablero.png` a media página.

## 2. El problema y la solución

**En emergencia se atiende por gravedad, no por orden de llegada.**

- Antes: la cama se busca por teléfono y el estado está en una pizarra.
- Con SIGTAC: el triaje y las camas están en un mismo sistema.

*Nota del orador (Favio, 1 minuto):* es un prototipo académico; el triaje es una sugerencia y el profesional decide.

## 3. Criterio 1 — La observación de la primera presentación

**«¿Cómo migrarían a otro motor de base de datos?»**

| Antes | Ahora |
|---|---|
| «Solo se cambian los DAO» | MySQL se importa en **3 archivos**, todos de `dao/` |
| Era una intención | Una **prueba automática** impide que otra capa use MySQL |

**Estado: atendida.**

*Nota del orador (Renzo):* mostrar en la terminal el `grep` de [OBSERVACIONES.md](OBSERVACIONES.md).

## 4. Criterio 1 — Qué cambia y qué no

*Diagrama de las 4 capas, con `dao/` resaltada:*

```text
views        6 679 líneas   no cambia
controllers  1 127 líneas   no cambia
models       1 368 líneas   no cambia
dao          1 853 líneas   ← solo aquí
```

## 5. Criterio 2 — Clases principales

*Diagrama de clases simplificado (solo nombres y flechas):*

```text
Persona ◁── Paciente                 Cama ◁── CamaTraumaShock
        ◁── Empleado ◁── Enfermero        ◁── CamaUCI
                     ◁── Medico           ◁── CamaObservacion
                     ◁── PersonalLimpieza ◁── CamaHospitalizacion

Paciente ──< EpisodioEmergencia ◆── Triaje ◆── Sintoma
                                ◆── SignosVitales
EpisodioEmergencia ── AsignacionCama ── Cama
```

*Nota del orador (Ian):* por cada clase, una frase: qué representa, qué guarda y qué hace.

## 6. Criterio 3 — Encapsulamiento

**El estado de una cama no se asigna: se pide.**

```python
@property
def estado(self): return self._estado      # solo lectura

def reservar(self):
    if self._estado != Cama.ESTADO_DISPONIBLE:
        raise CamaEstadoInvalidoError(...)
    self._estado = Cama.ESTADO_RESERVADA
```

`cama.estado = "OCUPADA"` → **error**

## 7. Criterio 4 — Herencia y polimorfismo

**Un mensaje, cuatro respuestas.**

```python
class CamaTraumaShock(Cama):
    def es_compatible(self, nivel): return nivel == 1
class CamaUCI(Cama):
    def es_compatible(self, nivel): return nivel in (1, 2)
class CamaObservacion(Cama):
    def es_compatible(self, nivel): return nivel in (2, 3, 4)
class CamaHospitalizacion(Cama):
    def es_compatible(self, nivel): return nivel in (3, 4, 5)
```

## 8. Criterio 4 — Los objetos colaboran

**Asignar una cama, en 5 pasos.**

1. La **sesión** dice si el rol tiene permiso.
2. El **episodio** comprueba que tenga triaje.
3. La **cama** responde si es compatible y si está disponible.
4. Los **DAO** guardan.
5. La **bitácora** registra quién lo hizo.

Si algo falla, la transacción deshace todo.

## 9. Criterios 5 y 6 — Demostración

**Demo en vivo**

Login → Triaje → Cola → Asignar cama → Alta → Limpieza → Reporte

Tres rechazos: un dato **incorrecto**, uno **incompleto** y uno **duplicado**.

*Si la demo falla:* las diapositivas de respaldo 15 a 18 tienen las capturas.

## 10. Criterio 6 — Cómo se manejan los errores

| Tipo | Ejemplo | Quién lo detecta |
|---|---|---|
| Dato inválido (`ValueError`) | Saturación de 150 % | La clase, al crearse |
| Regla de negocio (`SigtacError`) | Reservar una cama ocupada | El método de la clase |
| Duplicado | El mismo documento dos veces | El controlador y la base de datos (`UNIQUE`) |

El modelo lanza el error · la pantalla lo muestra · la transacción deshace.

## 11. Criterio 7 — Organización del código

```text
views/        pantallas          → nunca SQL
controllers/  casos de uso       → permisos
models/       clases y reglas    → la POO está aquí
dao/          acceso a datos     → único lugar con SQL
tests/        2 332 pruebas
```

Nombres en español que dicen lo que hacen: `cama.reservar()` · `episodio.dar_alta()` · `exigir_permiso()`

## 12. Criterio 8 — Una decisión técnica

**¿Qué camas sirven para un paciente de nivel 2?**

| | Opción A: en SQL | Opción B: polimorfismo ✔ |
|---|---|---|
| Cómo | Columna `nivel_min` | Método `es_compatible()` |
| Problema | Un número no alcanza: Observación acepta 2, 3 y 4 | Se filtra en Python |
| Regla | Escrita dos veces | **Un solo dueño** |

## 13. Aportes adicionales

- **Base de datos MySQL**: 22 tablas y transacciones
- **Reporte en PDF** con indicadores
- **5 roles**: cada uno ve solo sus módulos
- **Bitácora** de auditoría
- **Claves cifradas** con bcrypt
- **2 332 pruebas** automáticas
- Modo oscuro

## 14. Cierre

**SIGTAC en números**

8 pantallas · 5 roles · 22 tablas · 2 332 pruebas

Qué sigue: que cada usuario cambie su clave y probarlo con varias PCs.

**¿Preguntas?**

---

## Diapositivas de respaldo (no se muestran salvo que la demo falle o pregunten)

| N.º | Contenido | Imagen |
|---|---|---|
| 15 | Tablero de camas | `capturas/tablero.png` |
| 16 | Triaje | `capturas/triaje.png` |
| 17 | Gestión de camas | `capturas/camas.png` |
| 18 | Limpieza, Reportes y Administración | `capturas/limpieza.png`, `reportes.png`, `admin.png` |
| 19 | Modo oscuro | `capturas/tablero_oscuro.png` |
| 20 | Patrones: DAO, Strategy, Singleton | Una línea por patrón |
| 21 | Tabla de pruebas | La primera tabla de [TABLA_PRUEBAS.md](TABLA_PRUEBAS.md) |
