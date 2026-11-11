# Tabla de pruebas

Tres niveles de prueba. Los dos primeros se pueden repetir en cualquier momento con un comando.

| Nivel | Qué prueba | Cómo se ejecuta | Resultado |
|---|---|---|---|
| Pruebas automáticas | Cada clase y cada pantalla por separado, sin MySQL | `python -m pytest` | **2 332 de 2 332** pasan (11/11/2026) |
| Verificación contra MySQL | El flujo completo en una base temporal que se crea y se borra | `python scripts/verificar_controladores.py` | **97 de 97** comprobaciones (06/11/2026) |
| Revisión de tester | La aplicación real manejada como un usuario | A mano, unos 60 casos | Los 13 casos del plan pasan (05/11/2026) |

## Los 13 casos del plan de pruebas (Fase 7)

| N.º | Caso | Qué se hace | Resultado esperado | Estado |
|---|---|---|---|---|
| 1 | Autenticación correcta | Documento y clave válidos | Entra y ve los módulos de su rol | ✅ |
| 2 | Contraseña incorrecta | Clave equivocada | Rechaza sin decir la causa; 5 fallos bloquean 15 min | ✅ |
| 3 | Usuario desactivado | Entrar con DNI 99999999 | Rechaza con el mismo mensaje | ✅ |
| 4 | Registrar, buscar y editar paciente | Alta, búsqueda por documento y corrección | Los datos se guardan y se recuperan | ✅ |
| 5 | Borrado lógico | Dar de baja a un paciente | No se borra: `estado_registro = FALSE` (RN-11) | ✅ |
| 6 | Clasificación | Signos y síntomas | Sugiere un nivel de 1 a 5 y muestra los criterios | ✅ |
| 7 | Reclasificación con justificación | Cambiar el nivel con un texto de 10 o más caracteres | Se guarda el nivel final y la justificación | ✅ |
| 8 | Reclasificación sin justificación | Cambiar el nivel con texto corto o vacío | Se rechaza (RN-10) | ✅ |
| 9 | Compatibilidad de camas | Elegir un paciente de la cola | Solo se ofrecen las camas de su nivel | ✅ |
| 10 | Reserva de cama no disponible | Dos PCs toman la misma cama | La segunda se rechaza | ✅ |
| 11 | Transacciones | Forzar un fallo a mitad de una operación | ROLLBACK: no queda nada a medias | ✅ |
| 12 | Auditoría | Hacer una operación sensible | Aparece en la bitácora con usuario y hora | ✅ |
| 13 | Reportes | Elegir un período y exportar | Indicadores y PDF | ✅ |

## Qué cubren las pruebas automáticas

| Capa | Archivos de prueba | Ejemplos |
|---|---|---|
| Modelos | `test_cama.py`, `test_triaje.py`, `test_persona.py`, `test_estrategias.py`, `test_usuario.py`… | Cada transición de estado de la cama; los valores límite de los signos y de la justificación |
| DAO | `test_*_dao.py`, `test_transaccion.py` | El SQL lleva parámetros; los errores de MySQL se traducen |
| Controladores | `test_*_controller.py` | Permisos por rol; el orden: validar → transacción → auditar |
| Pantallas | `test_*_view.py`, `test_componentes.py` | Cada pantalla con controladores falsos |
| Reglas del proyecto | `test_capas.py`, `test_estados_vs_bd.py`, `test_tema.py` | Las vistas no usan SQL; los estados de Python coinciden con la BD; el contraste de los colores |

## Qué decir si preguntan por las pruebas

- «Las pruebas no necesitan MySQL: la base de datos se simula. Así cualquiera del equipo las corre en su PC.»
- «Cada regla de negocio tiene su prueba, y los valores límite se prueban a propósito.»
- «Aparte, un script corre el flujo completo contra MySQL real en una base temporal, para no tocar la nuestra.»
