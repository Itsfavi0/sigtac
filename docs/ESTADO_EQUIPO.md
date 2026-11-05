# SIGTAC — Estado del proyecto (5 de noviembre de 2026)

## En resumen

- **La aplicación está completa**: las 8 pantallas funcionan con la base de datos real.
- **Hicimos una revisión de tester**: los 13 casos de prueba del plan pasan. Aparecieron 3 problemas para corregir y algunos detalles menores.
- **Siguiente paso**: corregir esos problemas y preparar la sustentación (Fase 7).

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
| 7. Integración y pruebas | 🔄 En curso: pruebas hechas, faltan las correcciones |

**2115 pruebas automáticas** pasan (`python -m pytest`). No necesitan MySQL.

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

## Qué falta corregir

**Importantes**
1. **Volver a triar a un paciente que ya espera cama.** Si empeora, hoy no se puede registrar un nuevo triaje desde la pantalla. La regla existe en el sistema, pero la pantalla no la ofrece.
2. **Ventana muy pequeña.** Por debajo de ~1093×614 se cortan textos. En Triaje desaparece la pestaña «En cola».
3. **Cambio de paciente en Triaje.** Si se empieza a registrar a uno y se cambia a «Sin identificar», los signos vitales escritos se quedan.

**Menores** (redacción y aspecto)
- Algunos mensajes muestran nombres técnicos, como «EN ATENCIÓN (CON CAMA)».
- Un botón deshabilitado se ve igual que uno habilitado.
- El PDF usa punto decimal y uno de sus mensajes trata de «tú»; el resto de la app trata de usted.
- Dos síntomas largos no caben en su casilla en pantallas pequeñas.

## Para probarla

```bash
python -m prototipo.ver        # con datos de demostración, sin MySQL
python main.py                 # la aplicación real (necesita el .env y MySQL)
```

Las cuentas de prueba están en `db_scripts/seed.sql` (solo para uso local).
Si alguien usa la base de la PC donde se hicieron las pruebas, conviene volver a cargar `seed.sql`, porque quedaron datos de prueba («Prueba QA»).

## Próximos pasos

1. Corregir los 3 problemas importantes.
2. Corregir los detalles menores.
3. Ejecutar `scripts/verificar_controladores.py` contra MySQL (confirmación final con datos reales).
4. Preparar la sustentación: la demo del flujo completo y la tabla de pruebas.
