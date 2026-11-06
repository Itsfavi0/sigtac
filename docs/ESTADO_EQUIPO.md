# SIGTAC — Estado del proyecto (6 de noviembre de 2026)

## En resumen

- **La aplicación está completa**: las 8 pantallas funcionan con la base de datos real.
- **Hicimos una revisión de tester**: los 13 casos de prueba del plan pasan. Los 3 problemas y los detalles menores que aparecieron **ya están corregidos**.
- **Siguiente paso**: preparar la sustentación (Fase 7). La verificación contra MySQL ya pasó: 97 de 97.

## Avance por fases

| Fase | Estado |
|---|---|
| 0. Entorno y estructura | ✅ Completada |
| 1. Base de datos (MySQL) | ✅ Completada |
| 2. Modelos (reglas de negocio) | ✅ Completada |
| 3. DAO (acceso a datos) | ✅ Completada |
| 4. Controladores (casos de uso y permisos) | ✅ Completada |
| 5. Utilidades (contraseñas, registro de eventos, PDF) | ✅ Completada |
| 6. Pantallas | ✅ Completada el 04/11 |
| 7. Integración y pruebas | 🔄 En curso: pruebas y correcciones hechas; falta la sustentación |

**2161 pruebas automáticas** pasan (`python -m pytest`). No necesitan MySQL.
Además, la verificación contra MySQL real (`scripts/verificar_controladores.py`) dio **97 de 97 comprobaciones correctas** (06/11).

## Qué hay en la aplicación

- **Login** con bloqueo de la cuenta tras 5 intentos fallidos.
- **Tablero de camas**: estado de la guardia, que se actualiza solo cada 30 s.
- **Triaje**: registra al paciente (con documento o NN), sugiere el nivel con la regla de Manchester y permite reclasificar con justificación.
- **Gestión de camas**: asignar, registrar la llegada, dar de alta, referir, registrar fuga y mantenimiento.
- **Pacientes**: buscar, corregir datos, abrir un episodio e identificar a los NN (con fusión de registros).
- **Limpieza**: confirmar que una cama quedó limpia.
- **Reportes**: indicadores de un período y exportación a PDF.
- **Administración**: cuentas, roles, claves, bitácora, y baja o reactivación de pacientes.

Cada rol ve solo sus módulos. Por ejemplo, Limpieza ve el Tablero y Limpieza.
Esta semana se agregaron íconos y modo oscuro revisado, y las barras de desplazamiento solo aparecen cuando hacen falta.

## Resultado de la revisión de tester

Probamos la aplicación real contra MySQL, manejando la ventana como un usuario (unos 60 casos):

| Caso de prueba del plan | Resultado |
|---|---|
| Autenticación correcta / contraseña incorrecta / usuario desactivado | ✅ |
| Registrar, buscar y editar paciente | ✅ |
| Baja lógica (sin borrar datos) | ✅ |
| Clasificación de triaje | ✅ |
| Reclasificación con y sin justificación (mínimo 10 caracteres) | ✅ |
| Compatibilidad de camas según el nivel | ✅ |
| Reservar una cama que otra PC ya tomó | ✅ Se rechaza y no se guarda nada a medias |
| Auditoría (bitácora) | ✅ |
| Reportes y PDF | ✅ |

También funcionan el ciclo completo de la cama (reservada → ocupada → limpieza → disponible) y los permisos de cada rol.

## Qué se corrigió después de la revisión

**Importantes** (5/11)
1. **Volver a triar a un paciente que ya espera cama.** Ahora Triaje lo reconoce al buscarlo y agrega el nuevo triaje a su mismo episodio.
2. **Ventana muy pequeña.** La ventana ya no se achica por debajo de 1093×540.
3. **Cambio de paciente en Triaje.** Al cambiar de paciente se borran los signos, los síntomas y el motivo escritos.

**Menores** (6/11)
- Los mensajes ya no muestran nombres técnicos: dicen «En atención (con cama)», «Los nombres son obligatorios.» y «Síntoma» (con tilde) en la bitácora.
- Toda la app usa coma decimal (también el PDF), y el PDF trata de usted.
- «Se dio de baja a…» en lugar de «quedó dado de baja», que suponía el género.
- Los síntomas largos se parten en dos líneas.
- Al confirmar con datos que faltan, se marcan todos los campos con error a la vez.
- Si la PA diastólica no es menor que la sistólica, se marcan los dos campos y el botón dice «Corrija los signos vitales».
- En el tablero, el indicador del tiempo hasta la cama se llama «Asignación de cama», para no confundirlo con la espera de quien sigue en la cola.

**Para decidir en equipo:** el botón principal deshabilitado se ve igual que el habilitado. Es una decisión de diseño de octubre: su texto dice qué falta («Complete los signos vitales»). Cambiarlo afecta a todas las pantallas.

## Para probarla

```bash
python -m prototipo.ver        # con datos de demostración, sin MySQL
python main.py                 # la aplicación real (necesita el .env y MySQL)
```

Las cuentas de prueba están en `db_scripts/seed.sql` (solo para uso local).
Si alguien usa la base de la PC donde se hicieron las pruebas, conviene volver a cargar `seed.sql`, porque quedaron datos de prueba («Prueba QA»).

## Próximos pasos

1. Decidir el aspecto del botón deshabilitado.
2. Preparar la sustentación: la demo del flujo completo y la tabla de pruebas.
