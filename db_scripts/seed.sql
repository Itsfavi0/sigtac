-- ==============================================================================
-- SISTEMA INTEGRADO DE GESTIÓN DE TRIAJE Y ASIGNACIÓN DE CAMAS (SIGTAC)
-- Script de Poblamiento Inicial (Seed Data)
-- ==============================================================================

USE sigtac_db;

-- Desactivar temporalmente validaciones si es necesario limpiar e insertar de cero
-- (Opcional, pero útil si lo corres varias veces)
SET FOREIGN_KEY_CHECKS = 0;

-- Limpiar tablas antes de insertar (Orden inverso)
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

-- Roles de acceso al software
INSERT INTO rol (id_rol, nombre_rol) VALUES
(1, 'Administrador'),
(2, 'Jefe de Guardia'),
(3, 'Médico de Emergencia'),
(4, 'Enfermero de Triaje'),
(5, 'Personal de Limpieza');

-- Cargos laborales del hospital
INSERT INTO cargo (id_cargo, nombre_cargo, tipo) VALUES
(1, 'Médico Intensivista', 'Médico'),
(2, 'Médico Internista', 'Médico'),
(3, 'Licenciado(a) en Enfermería', 'Enfermería'),
(4, 'Técnico(a) de Enfermería', 'Técnico'),
(5, 'Operario de Limpieza', 'Mantenimiento'),
(6, 'Ingeniero de Sistemas', 'Administrativo');

-- Seguros
INSERT INTO seguro (id_seguro, nombre_seguro) VALUES
(1, 'EsSalud'),
(2, 'SIS (Seguro Integral de Salud)'),
(3, 'Seguro Privado (EPS)'),
(4, 'Particular / Sin Seguro');

-- Estados del Episodio
INSERT INTO estado_episodio (id_estado_ep, nombre_estado_episodio) VALUES
(1, 'EN ESPERA DE TRIAJE'),
(2, 'EN ESPERA DE CAMA'),
(3, 'EN ATENCIÓN (CON CAMA)'),
(4, 'ALTA MÉDICA'),
(5, 'REFERIDO'),
(6, 'FUGADO / ABANDONO');

-- Estados de la Cama
INSERT INTO estado_cama (id_estado_cama, nombre_estado_cama) VALUES
(1, 'DISPONIBLE'),
(2, 'RESERVADA'),
(3, 'OCUPADA'),
(4, 'EN LIMPIEZA'),
(5, 'FUERA DE SERVICIO');

-- Áreas del Hospital
INSERT INTO area (id_area, nombre_area, piso) VALUES
(1, 'Trauma Shock', 'Piso 1 - Emergencia'),
(2, 'Unidad de Cuidados Intensivos (UCI)', 'Piso 2'),
(3, 'Sala de Observación Adultos', 'Piso 1 - Emergencia'),
(4, 'Pabellón de Hospitalización A', 'Piso 3');

-- Tipos de Cama (Con nivel mínimo de prioridad para asignar)
INSERT INTO tipo_cama (id_tipo_cama, nombre_tipo_cama, nivel_min) VALUES
(1, 'Cama de Trauma Shock', 1), -- Solo admite Prioridad 1
(2, 'Cama UCI con Ventilador', 2), -- Admite Prioridad 1 y 2
(3, 'Cama de Observación con Monitor', 4), -- Admite Prioridades 1, 2, 3, 4
(4, 'Cama de Hospitalización General', 5); -- Admite todas

-- Niveles de Triaje (Escala de Manchester / MINSA)
INSERT INTO nivel_triaje (id_nivel, numero, color, tiempo_max_min) VALUES
(1, 1, 'Rojo', 0),       -- Atención inmediata
(2, 2, 'Naranja', 10),   -- Urgencia Mayor
(3, 3, 'Amarillo', 60),  -- Urgencia Menor
(4, 4, 'Verde', 120),    -- Prioridad Estándar
(5, 5, 'Azul', 240);     -- No Urgente

-- Catálogo de Síntomas con Pesos Clínicos (Para el motor de reglas)
INSERT INTO sintoma (id_sintoma, nombre_sintoma, peso_clinico) VALUES
(1, 'Paro Cardiorrespiratorio', 10.00),
(2, 'Dolor Torácico Opresivo', 8.50),
(3, 'Dificultad Respiratoria Severa (Disnea)', 8.00),
(4, 'Sangrado Activo Profuso', 7.50),
(5, 'Alteración de la Conciencia (Glasgow < 8)', 9.00),
(6, 'Fiebre Alta (> 39°C)', 4.00),
(7, 'Dolor Abdominal Intenso', 5.00),
(8, 'Vómitos Persistentes', 3.50),
(9, 'Herida Superficial', 1.00),
(10, 'Tos Leve', 0.50);

-- ==============================================================================
-- 2. TABLAS MAESTRAS (EMPLEADOS, USUARIOS, PACIENTES Y CAMAS)
-- ==============================================================================

-- Empleados
INSERT INTO empleado (id_empleado, dni, nombres, apellidos, colegiatura, id_cargo) VALUES
(1, '11111111', 'Admin', 'Sistema', 'CIP-12345', 6),
(2, '22222222', 'Héctor', 'Salazar Mendoza', 'CMP-54321', 1), -- Jefe de Guardia
(3, '33333333', 'Favio Enrique', 'Brañez Choquemamani', 'CEP-98765', 3), -- Enfermero Triaje
(4, '44444444', 'Renzo Alexander', 'Moya Ángeles', NULL, 5), -- Limpieza
(5, '55555555', 'Leonardo', 'Veliz Neyra', 'CMP-67890', 2); -- Médico Internista

-- Usuarios (Clave por defecto: 'admin123' y '123456'. Usa un hash real de bcrypt en tu app final)
-- Por ahora pongo un hash de ejemplo: $2b$12$EjemploDeHashBcryptGeneradoParaContraseñas123
INSERT INTO usuario (id_usuario, id_empleado, id_rol, hash_clave) VALUES
(1, 1, 1, '$2b$12$EjemploHash1234567890123456789012345678901234567890123'), -- Admin
(2, 2, 2, '$2b$12$EjemploHash1234567890123456789012345678901234567890123'), -- Jefe de Guardia
(3, 3, 4, '$2b$12$EjemploHash1234567890123456789012345678901234567890123'), -- Enfermero Triaje
(4, 4, 5, '$2b$12$EjemploHash1234567890123456789012345678901234567890123'); -- Limpieza

-- Pacientes de Prueba
INSERT INTO paciente (id_paciente, dni, nombres, apellidos, fecha_nac, sexo, id_seguro) VALUES
(1, '70123456', 'Rosa', 'Mendoza Flores', '1959-05-14', 'F', 1),
(2, '70987654', 'Carlos', 'García Pérez', '1980-11-22', 'M', 2),
(3, '71234567', 'Luis', 'Sánchez Rivas', '1995-02-10', 'M', 4);

-- Inventario de Camas (Combinando áreas, tipos y estados)
INSERT INTO cama (id_cama, codigo, id_area, id_tipo_cama, id_estado_cama) VALUES
-- Trauma Shock (Piso 1)
(1, 'TRA-01', 1, 1, 3), -- Ocupada
(2, 'TRA-02', 1, 1, 1), -- Disponible
-- UCI (Piso 2)
(3, 'UCI-01', 2, 2, 1), -- Disponible
(4, 'UCI-02', 2, 2, 4), -- En Limpieza
(5, 'UCI-03', 2, 2, 5), -- Mantenimiento
-- Observación (Piso 1)
(6, 'OBS-01', 3, 3, 1), -- Disponible
(7, 'OBS-02', 3, 3, 1), -- Disponible
(8, 'OBS-03', 3, 3, 3); -- Ocupada

-- ==============================================================================
-- 3. DATOS TRANSACCIONALES (SIMULANDO ATENCIONES EN CURSO)
-- ==============================================================================

-- Creamos 3 episodios de emergencia simulando que ocurrieron HOY temprano
INSERT INTO episodio_emergencia (id_episodio, id_paciente, fecha_ingreso, motivo_consulta, id_estado_ep) VALUES
(1, 1, DATE_SUB(NOW(), INTERVAL 2 HOUR), 'Dolor intenso en pecho irradiado a brazo izquierdo, sudoración fría.', 3), -- Ya con cama
(2, 2, DATE_SUB(NOW(), INTERVAL 45 MINUTE), 'Caída de segundo piso, dolor fuerte en pierna derecha.', 2), -- En espera de cama
(3, 3, DATE_SUB(NOW(), INTERVAL 15 MINUTE), 'Fiebre persistente y malestar general desde ayer.', 2); -- En espera de cama

-- Signos Vitales para los 3 episodios
INSERT INTO signos_vitales (id_si, id_episodio, pa_sis, pa_dia, fc, fr, temp, sato2) VALUES
(1, 1, 165, 98, 118, 26, 37.2, 89), -- Paciente 1 (Grave)
(2, 2, 130, 85, 95, 20, 36.8, 97),  -- Paciente 2 (Traumatismo)
(3, 3, 120, 80, 85, 18, 39.5, 98);  -- Paciente 3 (Fiebre)

-- Triajes realizados por el Enfermero (id_empleado = 3)
-- El triaje 2 demuestra RN-10: el sistema sugirió Nivel III y el profesional
-- reclasificó a Nivel II, dejando constancia escrita de por qué difiere.
INSERT INTO triaje (id_triaje, id_episodio, id_nivel, id_nivel_sugerido, id_empleado, fecha_hora, justificacion) VALUES
(1, 1, 1, 1, 3, DATE_SUB(NOW(), INTERVAL 115 MINUTE), NULL), -- Prioridad 1 (Rojo), sin reclasificar
(2, 2, 2, 3, 3, DATE_SUB(NOW(), INTERVAL 40 MINUTE),
    'Paciente con antecedente de fractura expuesta previa en la misma extremidad; se prioriza pese a signos vitales estables por alto riesgo de complicación vascular.'),
(3, 3, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 10 MINUTE), NULL);  -- Prioridad 3 (Amarillo), sin reclasificar

-- Síntomas asociados a cada Triaje (Tabla Puente)
INSERT INTO triaje_sintoma (id_triaje, id_sintoma) VALUES
(1, 2), (1, 3), -- Triaje 1 tiene Dolor Torácico y Disnea
(2, 7),         -- Triaje 2 tiene Dolor Intenso
(3, 6);         -- Triaje 3 tiene Fiebre Alta

-- Simulamos que el Paciente 1 ya tiene una cama asignada (TRA-01) por el Jefe (id_empleado = 2)
INSERT INTO asignacion_cama (id_asignacion, id_episodio, id_cama, id_empleado, fecha_asignacion, fecha_liberacion) VALUES
(1, 1, 1, 2, DATE_SUB(NOW(), INTERVAL 110 MINUTE), NULL); 

-- Simulamos que la cama UCI-02 tiene una limpieza pendiente
INSERT INTO solicitud_limpieza (id_solicitud, id_cama, id_empleado, fecha_solicitud, fecha_atencion) VALUES
(1, 4, NULL, DATE_SUB(NOW(), INTERVAL 30 MINUTE), NULL);

-- ==============================================================================
-- 4. HISTORIAL Y AUDITORÍA
-- ==============================================================================

-- Historial de estado de camas (Para que no esté vacío el reporte de rotación)
INSERT INTO historial_estado_cama (id_historial, id_cama, id_estado_cama, fecha_cambio) VALUES
(1, 1, 1, DATE_SUB(NOW(), INTERVAL 3 DAY)),
(2, 1, 3, DATE_SUB(NOW(), INTERVAL 110 MINUTE)), -- Pasó a Ocupada hoy
(3, 4, 3, DATE_SUB(NOW(), INTERVAL 2 DAY)),
(4, 4, 4, DATE_SUB(NOW(), INTERVAL 30 MINUTE)); -- Pasó a En Limpieza hoy

-- Auditoría (Un inicio de sesión y una creación de paciente)
INSERT INTO bitacora_auditoria (id_bitacora, id_usuario, tabla_afectada, accion, fecha_hora) VALUES
(1, 1, 'usuario', 'LOGIN', DATE_SUB(NOW(), INTERVAL 3 HOUR)),
(2, 3, 'paciente', 'INSERT', DATE_SUB(NOW(), INTERVAL 120 MINUTE));