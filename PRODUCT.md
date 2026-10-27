# Product

<!-- impeccable:product-schema 1 -->

## Platform

desktop

Aplicación de escritorio para Windows con CustomTkinter (Python). No es web ni móvil: no hay navegador, CSS
ni diseño adaptable a celulares.

## Users

Personal de un servicio de emergencia hospitalario. Cada uno entra con su cuenta y ve solo lo que su rol permite:

- **Enfermero de triaje**: registra al paciente, mide sus signos vitales, marca los síntomas y confirma o
  corrige el nivel que sugiere el sistema. Trabaja de pie, con gente esperando, y repite este flujo decenas de
  veces por turno.
- **Médico de emergencia**: además de triar, asigna camas compatibles, da de alta, refiere y registra fugas.
- **Jefe de guardia**: todo lo anterior y los indicadores de la guardia (ocupación, esperas, reclasificaciones).
- **Administrador**: cuentas de usuario, bitácora de auditoría y reportes; no atiende pacientes.
- **Personal de limpieza**: ve el mapa de camas y confirma que una cama quedó limpia.

El proyecto se evalúa con **dos públicos a la vez**: el jurado del curso, en una demo, y el criterio de cómo
lo usaría el personal real en una guardia. Ninguno de los dos se sacrifica por el otro.

## Product Purpose

SIGTAC (Sistema Integrado de Gestión de Triaje y Asignación de Camas) ordena la atención en emergencia:

1. registra al paciente (con documento o sin identificar, «NN») y abre su episodio;
2. sugiere el nivel de triaje (1 Rojo a 5 Azul) a partir de signos vitales y síntomas;
3. arma la cola por prioridad y luego por orden de llegada;
4. propone solo las camas compatibles con ese nivel y controla su ciclo: disponible → reservada → ocupada →
   en limpieza → disponible.

El éxito es que, en un vistazo, se sepa quién es el más urgente, qué cama le corresponde y en qué estado está
cada cama. Y que nadie pueda saltarse una regla crítica.

Es el proyecto integrador del curso Programación Orientada a Objetos II (Universidad Nacional del Callao), con
entrega el 19/12/2026. Es una simulación didáctica: los algoritmos de triaje no están validados clínicamente.

## Positioning

- **El sistema sugiere y el profesional decide.** El nivel sugerido se muestra siempre, y cambiarlo exige una
  justificación escrita (RN-10). Las dos cosas quedan registradas.
- **Las reglas viven en el sistema, no en la memoria del personal:**
  - no se asigna cama sin triaje (RN-01);
  - no se reserva una cama ocupada (RN-05);
  - una cama no vuelve a estar disponible sin confirmar su limpieza (RN-07/08).
- **Varias PCs trabajan a la vez sobre la misma guardia:** si dos personas toman la misma cama, gana una y la
  otra recibe un aviso claro.

## Operating Context

- **Guardia de emergencia:** luz fluorescente y de día, ruido, interrupciones y PCs compartidas entre turnos.
  En el turno de noche, algunas áreas están en penumbra.
- **Pantallas:**
  - laptops del equipo (1366×768 a 1920×1080, con el zoom de Windows al 125–150 %);
  - PCs de hospital con monitores antiguos (1366×768 o 1280×1024);
  - un proyector en la sustentación, visto desde lejos.
- **La demo ante el jurado** recorre el flujo completo: login → registrar paciente → triaje → cola → asignar
  cama → alta → limpieza → indicadores.
- **Antecedente de diseño:** el equipo hizo un primer diseño en Figma Make (modo oscuro, solo «Tablero de
  Camas» y «Nuevo Triaje») que sirve de punto de partida.

## Capabilities and Constraints

- Hay 5 pantallas en el alcance actual: inicio de sesión, ventana principal con navegación por rol, tablero
  (indicadores y mapa de camas), triaje y pacientes. Camas, limpieza, reportes y administración ya tienen la
  lógica hecha y sus pantallas vienen después.
- **CustomTkinter permite:** colores planos, bordes, esquinas redondeadas, fuentes TTF propias, íconos PNG,
  modo claro y oscuro, y cambio de color al pasar el mouse.
- **CustomTkinter no permite:** sombras, degradados, transparencias, desenfoque, pesos de letra intermedios
  (solo normal y negrita), interletrado, ni animaciones con curvas o escala.
- **Modo claro por defecto y oscuro opcional** para el turno de noche (decisión del equipo, 2026-10-27).
- **Términos del dominio** que la interfaz usa tal cual:
  - nivel de triaje 1 a 5 (Rojo, Naranja, Amarillo, Verde, Azul);
  - estados de cama: Disponible, Reservada, Ocupada, En limpieza, Fuera de servicio;
  - estados del episodio: En espera de triaje, En espera de cama, En atención, Alta médica, Referido,
    Fugado/Abandono;
  - documentos: DNI, Carné de extranjería, Pasaporte, CPP;
  - paciente «NN» (sin identificar).
- **Signos vitales del modelo:** PA sistólica y PA diastólica por separado, FC, FR, temperatura y SatO2. No hay
  escala de dolor.

## Brand Commitments

- Solo la marca SIGTAC: sin logos de hospitales, del MINSA ni de la universidad.
- Textos en español, en el registro del personal de salud peruano.
- El aviso «prototipo académico, no validado clínicamente» aparece donde corresponde (login, reportes).

## Evidence on Hand

- Datos de prueba en `db_scripts/seed.sql`: catálogos reales (niveles, estados, tipos de cama, documentos,
  síntomas) y pacientes y empleados de ejemplo.
- No hay usuarios reales, testimonios ni métricas reales: ningún número de la interfaz o de la demo se presenta
  como dato real.

## Product Principles

1. **Lo urgente se ve primero.** El color rojo y la posición más visible se reservan para lo que es urgente de
   verdad (nivel 1, cama ocupada, error). Nada decorativo compite con eso.
2. **Nunca solo color.** Cada nivel y cada estado lleva también su texto o número, porque hay daltonismo,
   monitores malos y proyectores.
3. **Rápido en lo repetido.** Lo que se hace decenas de veces por turno (triar, elegir un paciente, navegar)
   va sin animaciones, sin pasos de más y se puede hacer con el teclado.
4. **Las reglas se explican, no solo se aplican.** Cuando el sistema rechaza algo, dice qué regla y qué hacer.
5. **Se lee desde lejos.** El texto se puede leer en un monitor viejo y en un proyector.

## Accessibility & Inclusion

- Contraste mínimo de 4.5:1 para el texto (3:1 para letra grande o bordes que indican estado), en modo claro
  y en oscuro.
- Letra de al menos 12–13 px. El primer diseño de Figma usaba de 7 a 10 px y se corrige.
- Todo se puede usar sin mouse: orden de tabulación lógico, Enter para la acción principal y un foco visible.
- Información crítica nunca solo por color (principio 2).
