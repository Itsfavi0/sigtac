-- ==============================================================================
-- SISTEMA INTEGRADO DE GESTIÓN DE TRIAJE Y ASIGNACIÓN DE CAMAS (SIGTAC)
-- Script de Poblamiento Inicial (Seed Data) - REFACTORIZADO FASE 3
-- ==============================================================================

USE sigtac_db;

SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE bitacora_auditoria;
TRUNCATE TABLE historial_estado_cama;
TRUNCATE TABLE solicitud_limpieza;
TRUNCATE TABLE asignacion_cama;
TRUNCATE TABLE triaje_sintoma;
TRUNCATE TABLE triaje;
TRUNCATE TABLE signos_vitales;
TRUNCATE TABLE episodio_emergencia;
TRUNCATE TABLE cama;
TRUNCATE TABLE paciente;
TRUNCATE TABLE usuario;
TRUNCATE TABLE empleado;
TRUNCATE TABLE sintoma;
TRUNCATE TABLE nivel_triaje;
TRUNCATE TABLE tipo_cama;
TRUNCATE TABLE area;
TRUNCATE TABLE estado_cama;
TRUNCATE TABLE estado_episodio;
TRUNCATE TABLE seguro;
TRUNCATE TABLE cargo;
TRUNCATE TABLE rol;

SET FOREIGN_KEY_CHECKS = 1;

-- ==============================================================================
-- 1. CATÁLOGOS PARAMÉTRICOS
-- ==============================================================================
INSERT INTO rol (id_rol, nombre_rol) VALUES
(1, 'Administrador'), (2, 'Jefe de Guardia'), (3, 'Médico de Emergencia'), 
(4, 'Enfermero de Triaje'), (5, 'Personal de Limpieza');

INSERT INTO cargo (id_cargo, nombre_cargo, tipo) VALUES
(1, 'Médico Intensivista', 'Médico'), (2, 'Médico Internista', 'Médico'),
(3, 'Licenciado(a) en Enfermería', 'Enfermería'), (4, 'Técnico(a) de Enfermería', 'Técnico'),
(5, 'Operario de Limpieza', 'Mantenimiento'), (6, 'Ingeniero de Sistemas', 'Administrativo');

INSERT INTO seguro (id_seguro, nombre_seguro) VALUES
(1, 'EsSalud'), (2, 'SIS (Seguro Integral de Salud)'), 
(3, 'Seguro Privado (EPS)'), (4, 'Particular / Sin Seguro');

INSERT INTO estado_episodio (id_estado_ep, nombre_estado_episodio) VALUES
(1, 'EN ESPERA DE TRIAJE'), (2, 'EN ESPERA DE CAMA'), 
(3, 'EN ATENCIÓN (CON CAMA)'), (4, 'ALTA MÉDICA'), 
(5, 'REFERIDO'), (6, 'FUGADO / ABANDONO');

INSERT INTO estado_cama (id_estado_cama, nombre_estado_cama) VALUES
(1, 'DISPONIBLE'), (2, 'RESERVADA'), (3, 'OCUPADA'), 
(4, 'EN LIMPIEZA'), (5, 'FUERA DE SERVICIO');

INSERT INTO area (id_area, nombre_area, piso) VALUES
(1, 'Trauma Shock', 'Piso 1 - Emergencia'), (2, 'Unidad de Cuidados Intensivos (UCI)', 'Piso 2'),
(3, 'Sala de Observación Adultos', 'Piso 1 - Emergencia'), (4, 'Pabellón de Hospitalización A', 'Piso 3');

INSERT INTO tipo_cama (id_tipo_cama, nombre_tipo_cama, nivel_min) VALUES
(1, 'Cama de Trauma Shock', 1), (2, 'Cama UCI con Ventilador', 2), 
(3, 'Cama de Observación con Monitor', 4), (4, 'Cama de Hospitalización General', 5);

INSERT INTO nivel_triaje (id_nivel, numero, color, tiempo_max_min) VALUES
(1, 1, 'Rojo', 0), (2, 2, 'Naranja', 10), (3, 3, 'Amarillo', 60), 
(4, 4, 'Verde', 120), (5, 5, 'Azul', 240);

INSERT INTO sintoma (id_sintoma, nombre_sintoma, peso_clinico) VALUES
(1, 'Paro Cardiorrespiratorio', 10.00), (2, 'Dolor Torácico Opresivo', 8.50),
(3, 'Dificultad Respiratoria Severa (Disnea)', 8.00), (4, 'Sangrado Activo Profuso', 7.50),
(5, 'Alteración de la Conciencia (Glasgow < 8)', 9.00), (6, 'Fiebre Alta (> 39°C)', 4.00),
(7, 'Dolor Abdominal Intenso', 5.00), (8, 'Vómitos Persistentes', 3.50),
(9, 'Herida Superficial', 1.00), (10, 'Tos Leve', 0.50);

-- ==============================================================================
-- 2. TABLAS MAESTRAS
-- ==============================================================================
INSERT INTO empleado (id_empleado, dni, nombres, apellidos, colegiatura, id_cargo, estado_registro) VALUES
(1, '11111111', 'Admin', 'Sistema', 'CIP-12345', 6, 1),
(2, '22222222', 'Héctor', 'Salazar Mendoza', 'CMP-54321', 1, 1),
(3, '33333333', 'Favio Enrique', 'Brañez Choquemamani', 'CEP-98765', 3, 1),
(4, '44444444', 'Renzo Alexander', 'Moya Ángeles', NULL, 5, 1),
(5, '55555555', 'Leonardo', 'Veliz Neyra', 'CMP-67890', 2, 1),
(6, '99999999', 'Médico', 'Despedido', 'CMP-00000', 2, 0); -- Empleado inactivo para probar borrado lógico

INSERT INTO usuario (id_usuario, id_empleado, id_rol, hash_clave, activo) VALUES
(1, 1, 1, '$2b$12$EjemploHash1234567890123456789012345678901234567890123', 1),
(2, 2, 2, '$2b$12$EjemploHash1234567890123456789012345678901234567890123', 1),
(3, 3, 4, '$2b$12$EjemploHash1234567890123456789012345678901234567890123', 1),
(4, 4, 5, '$2b$12$EjemploHash1234567890123456789012345678901234567890123', 1),
(5, 6, 3, '$2b$12$EjemploHash1234567890123456789012345678901234567890123', 0); -- Usuario desactivado

INSERT INTO paciente (id_paciente, dni, nombres, apellidos, fecha_nac, sexo, id_seguro) VALUES
(1, '70123456', 'Rosa', 'Mendoza Flores', '1959-05-14', 'F', 1),
(2, '70987654', 'Carlos', 'García Pérez', '1980-11-22', 'M', 2),
(3, '71234567', 'Luis', 'Sánchez Rivas', '1995-02-10', 'M', 4);

INSERT INTO cama (id_cama, codigo, id_area, id_tipo_cama, id_estado_cama, estado_registro) VALUES
(1, 'TRA-01', 1, 1, 3, 1), (2, 'TRA-02', 1, 1, 1, 1),
(3, 'UCI-01', 2, 2, 1, 1), (4, 'UCI-02', 2, 2, 4, 1), (5, 'UCI-03', 2, 2, 5, 1),
(6, 'OBS-01', 3, 3, 1, 1), (7, 'OBS-02', 3, 3, 1, 1), (8, 'OBS-03', 3, 3, 3, 1);

-- ==============================================================================
-- 3. DATOS TRANSACCIONALES
-- ==============================================================================
INSERT INTO episodio_emergencia (id_episodio, id_paciente, fecha_ingreso, motivo_consulta, id_estado_ep) VALUES
(1, 1, DATE_SUB(NOW(), INTERVAL 2 HOUR), 'Dolor intenso en pecho irradiado a brazo izquierdo, sudoración fría.', 3),
(2, 2, DATE_SUB(NOW(), INTERVAL 45 MINUTE), 'Caída de segundo piso, dolor fuerte en pierna derecha.', 2),
(3, 3, DATE_SUB(NOW(), INTERVAL 15 MINUTE), 'Fiebre persistente y malestar general desde ayer.', 2);

-- FECHAS CORREGIDAS: Los signos se toman pocos minutos después del ingreso
INSERT INTO signos_vitales (id_si, id_episodio, pa_sis, pa_dia, fc, fr, temp, sato2, fecha_hora) VALUES
(1, 1, 165, 98, 118, 26, 37.2, 89, DATE_SUB(NOW(), INTERVAL 118 MINUTE)), 
(2, 2, 130, 85, 95, 20, 36.8, 97, DATE_SUB(NOW(), INTERVAL 42 MINUTE)),  
(3, 3, 120, 80, 85, 18, 39.5, 98, DATE_SUB(NOW(), INTERVAL 12 MINUTE));  

INSERT INTO triaje (id_triaje, id_episodio, id_nivel, id_nivel_sugerido, id_empleado, fecha_hora, justificacion) VALUES
(1, 1, 1, 1, 3, DATE_SUB(NOW(), INTERVAL 115 MINUTE), NULL),
(2, 2, 2, 3, 3, DATE_SUB(NOW(), INTERVAL 40 MINUTE), 'Paciente con antecedente de fractura expuesta previa en la misma extremidad; se prioriza pese a signos vitales estables por alto riesgo de complicación vascular.'),
(3, 3, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 10 MINUTE), NULL);

INSERT INTO triaje_sintoma (id_triaje, id_sintoma) VALUES
(1, 2), (1, 3), (2, 7), (3, 6);

INSERT INTO asignacion_cama (id_asignacion, id_episodio, id_cama, id_empleado, fecha_asignacion, fecha_liberacion) VALUES
(1, 1, 1, 2, DATE_SUB(NOW(), INTERVAL 110 MINUTE), NULL); 

INSERT INTO solicitud_limpieza (id_solicitud, id_cama, id_empleado, fecha_solicitud, fecha_atencion) VALUES
(1, 4, NULL, DATE_SUB(NOW(), INTERVAL 30 MINUTE), NULL);

-- ==============================================================================
-- 4. HISTORIAL Y AUDITORÍA
-- ==============================================================================
INSERT INTO historial_estado_cama (id_historial, id_cama, id_estado_cama, fecha_cambio) VALUES
(1, 1, 1, DATE_SUB(NOW(), INTERVAL 3 DAY)),
(2, 1, 3, DATE_SUB(NOW(), INTERVAL 110 MINUTE)),
(3, 4, 3, DATE_SUB(NOW(), INTERVAL 2 DAY)),
(4, 4, 4, DATE_SUB(NOW(), INTERVAL 30 MINUTE));

-- AUDITORÍA CORREGIDA: Se añade el ID del registro afectado
INSERT INTO bitacora_auditoria (id_bitacora, id_usuario, tabla_afectada, accion, id_registro_afectado, fecha_hora) VALUES
(1, 1, 'empleado', 'UPDATE', 6, DATE_SUB(NOW(), INTERVAL 3 HOUR)), -- Admin desactivó al empleado 6
(2, 3, 'paciente', 'INSERT', 1, DATE_SUB(NOW(), INTERVAL 120 MINUTE)); -- Enfermero registró al paciente 1