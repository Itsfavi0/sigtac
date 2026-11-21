-- ==============================================================================
-- !! SOLO PARA BASES DE DESARROLLO !!
-- Este script VACÍA (TRUNCATE) todas las tablas de sigtac_db antes de insertar los datos de prueba.
-- ==============================================================================
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
TRUNCATE TABLE tipo_documento;

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

INSERT INTO tipo_documento (id_tipo_documento, codigo, nombre_tipo_documento) VALUES
(1, 'DNI', 'Documento Nacional de Identidad'), (2, 'CE', 'Carné de Extranjería'),
(3, 'PAS', 'Pasaporte'), (4, 'CPP', 'Carné de Permiso Temporal de Permanencia');

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
(3, 'Sala de Observación Adultos', 'Piso 1 - Emergencia'), (4, 'Pabellón de Hospitalización A', 'Piso 3'),
(5, 'Triaje', 'Piso 1 - Emergencia'); -- Área sin camas: solo se asigna a personal de enfermería

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
-- 2. TABLAS MAESTRAS (las fechas de nacimiento son ficticias)
-- ==============================================================================
-- id_area, especialidad y turno solo se llenan según el tipo de empleado (Enfermero, Medico, PersonalLimpieza)
INSERT INTO empleado (id_empleado, id_tipo_documento, num_documento, nombres, apellidos, fecha_nac, colegiatura, id_cargo, id_area, especialidad, turno, estado_registro) VALUES
(1, 1, '11111111', 'Admin', 'Sistema', '1990-01-01', 'CIP-12345', 6, NULL, NULL, NULL, 1),
(2, 1, '22222222', 'Héctor', 'Salazar Mendoza', '1978-03-15', 'CMP-54321', 1, NULL, 'Medicina Intensiva', NULL, 1),
(3, 1, '33333333', 'Favio Enrique', 'Brañez Choquemamani', '1998-07-20', 'CEP-98765', 3, 5, NULL, NULL, 1),
(4, 1, '44444444', 'Renzo Alexander', 'Moya Ángeles', '1999-11-05', NULL, 5, NULL, NULL, 'MAÑANA', 1),
(5, 1, '55555555', 'Leonardo', 'Veliz Neyra', '1985-09-30', 'CMP-67890', 2, NULL, 'Medicina Interna', NULL, 1),
(6, 1, '99999999', 'Médico', 'Despedido', '1975-12-12', 'CMP-00000', 2, NULL, 'Medicina Interna', NULL, 0), -- Empleado inactivo para probar borrado lógico
(7, 1, '77777777', 'Valeria', 'Quispe Torres', '1988-04-22', 'CMP-24680', 2, NULL, 'Medicina Interna', NULL, 1); -- Médica con cuenta, para probar el rol de médico

-- Cuentas para probar el inicio de sesión. SOLO DESARROLLO: nunca usar estas claves fuera de un entorno local.
-- Todas comparten la clave Sigtac#Dev2026 (el hash bcrypt de abajo; comprobado contra cada uno).
--   Documento      Rol                     ¿Puede ingresar?
--   DNI 11111111   Administrador           sí
--   DNI 22222222   Jefe de Guardia         sí
--   DNI 33333333   Enfermero de Triaje     sí
--   DNI 44444444   Personal de Limpieza    sí
--   DNI 77777777   Médico de Emergencia    sí
--   DNI 99999999   Médico de Emergencia    no: cuenta desactivada y empleado de baja (prueba el rechazo)
-- 5 intentos fallidos bloquean la cuenta 15 minutos. El empleado 5 (DNI 55555555) no tiene cuenta a propósito:
-- scripts/verificar_controladores.py se la crea para probar crear_cuenta.
INSERT INTO usuario (id_usuario, id_empleado, id_rol, hash_clave, activo) VALUES
(1, 1, 1, '$2b$12$Kx6Fi0botsesFpvqW3KwZ.C6GmZ3TrcA3oRU1lGRsL51tNMWc1jZC', 1),
(2, 2, 2, '$2b$12$kmUGssmSTQva6xjH0KD6WuJlBgp6iCQXwPqcaxuQaHKgDIrFfgAJ6', 1),
(3, 3, 4, '$2b$12$fMB5vLsZZWGBkxMwiAKwDOpcaEjapNPCH5pvNVo9doSO0wc/pHQX.', 1),
(4, 4, 5, '$2b$12$6NyKLTdaDDiRnwyC7v/EheyivOh8k7wpmJp/0ucVgGyxRwlug6LeS', 1),
(5, 6, 3, '$2b$12$LlWJNQC.mWXbMt7Q5uTWI.EnkvnjmBydy8AMrc69HXCknF60ieyLO', 0), -- Usuario desactivado
(6, 7, 3, '$2b$12$eHm0j0YOSHA2Cgj2rOIlYe1RvcjdZjQfqau1Xa/B9bJRV6L91rkZa', 1);

INSERT INTO paciente (id_paciente, id_tipo_documento, num_documento, nombres, apellidos, fecha_nac, sexo, id_seguro) VALUES
(1, 1, '70123456', 'Rosa', 'Mendoza Flores', '1959-05-14', 'F', 1),
(2, 1, '70987654', 'Carlos', 'García Pérez', '1980-11-22', 'M', 2),
(3, 1, '71234567', 'Luis', 'Sánchez Rivas', '1995-02-10', 'M', 4),
(4, 2, '001234567', 'María José', 'Rodríguez Silva', '1988-06-03', 'F', 4), -- Paciente extranjera con carné de extranjería
(5, NULL, NULL, 'NN', 'NN', '1981-01-01', 'M', 4); -- Paciente sin identificar: edad estimada (~45 años)

-- Pacientes de la guardia (ficticios; los números de documento no son de personas reales). Los episodios
-- que ocupan cada uno están más abajo; los NN (id 8 y el último de la cola de triaje) no tienen documento.
INSERT INTO paciente (id_paciente, id_tipo_documento, num_documento, nombres, apellidos, fecha_nac, sexo, id_seguro) VALUES
(6, 1, '70234561', 'Pedro', 'Ramírez Cueva', '1972-02-18', 'M', 1),
(7, 1, '70345672', 'Lucía', 'Vargas Torres', '1991-09-05', 'F', 2),
(8, NULL, NULL, 'NN', 'NN', '1966-01-01', 'M', 4),
(9, 1, '70456783', 'Miguel Ángel', 'Huamán Ríos', '1984-07-12', 'M', 1),
(10, 1, '70567894', 'Carmen Rosa', 'Delgado Paz', '1979-03-27', 'F', 2),
(11, 1, '70678905', 'Jhon Anderson', 'Castillo Mamani', '2001-12-01', 'M', 4),
(12, 1, '70789016', 'Sofía Alejandra', 'Rojas Campos', '2004-05-19', 'F', 3),
(13, 1, '70890127', 'Teodoro', 'Quispe Huanca', '1951-10-30', 'M', 1),
(14, 1, '71012348', 'Gabriel', 'Núñez Alvarado', '1973-08-08', 'M', 1),
(15, 1, '71123459', 'Elena', 'Cárdenas Ortiz', '1958-01-23', 'F', 1),
(16, 1, '71345601', 'Walter', 'Ccopa Mendoza', '1980-06-14', 'M', 2),
(17, 1, '71456702', 'Marlene', 'Gutiérrez Salas', '1991-11-09', 'F', 1),
(18, 1, '71567803', 'Óscar', 'Villanueva Ríos', '1996-04-02', 'M', 4),
(19, 1, '71678904', 'Dina', 'Flores Huertas', '1954-09-17', 'F', 1),
(20, 1, '71789005', 'Kevin', 'Salinas Pomalaya', '2006-02-25', 'M', 2),
(21, 1, '71890106', 'Rocío', 'Arias Lozano', '1967-12-12', 'F', 1),
(22, 2, '002345678', 'Hugo', 'Medina Tapia', '1962-07-03', 'M', 4),
(23, 1, '72012307', 'Isabel', 'Mamani Quispe', '1984-05-30', 'F', 2),
(24, 1, '72123408', 'Fernando', 'Soto Linares', '1987-03-11', 'M', 3),
(25, 1, '72234509', 'Beatriz', 'Ayala Cruz', '1970-08-21', 'F', 1),
(26, 1, '72345610', 'Mario', 'Cabrera León', '1978-10-04', 'M', 2),
(27, 1, '72456711', 'Nancy', 'Paucar Espinoza', '1999-01-16', 'F', 2),
(28, 1, '72567812', 'Lorenzo', 'Chávez Huamán', '1989-06-28', 'M', 4),
(29, 1, '72678913', 'Gloria', 'Tello Barrios', '1965-11-02', 'F', 1),
(30, 1, '72789014', 'Pablo', 'Zegarra Lima', '1975-09-09', 'M', 1),
(31, 1, '73104248', 'Paola', 'Cruz Gutiérrez', '2004-06-20', 'F', 2),
(32, 1, '73104385', 'Fabián', 'Mendoza Rodríguez', '1962-11-20', 'M', 2),
(33, 1, '73104522', 'Olga', 'Campos Condori', '1971-10-04', 'F', 4),
(34, NULL, NULL, 'NN', 'NN', '1960-01-01', 'F', 4),
(35, 1, '73104796', 'Marco', 'Yupanqui Lara', '1998-12-14', 'M', 2),
(36, 1, '73104933', 'Carlos', 'Ccama Pinedo', '1985-03-11', 'M', 3),
(37, 1, '73105070', 'Elías Walter', 'Cruz Lara', '2004-09-20', 'M', 2),
(38, 1, '73105207', 'Diego', 'Medina Ramos', '1995-10-05', 'M', 2),
(39, 1, '73105344', 'Yeison Cristian', 'Sánchez Chávez', '1994-08-22', 'M', 2),
(40, 1, '73105481', 'Sonia Zoila', 'Huamán Palomino', '1954-01-03', 'F', 2),
(41, 1, '73105618', 'Fabián Tomás', 'Ortiz Cruz', '1967-06-09', 'M', 3),
(42, 1, '73105755', 'Ángel', 'Ríos Pinedo', '1979-08-26', 'M', 1),
(43, 1, '73105892', 'José', 'Paredes Valdez', '1946-06-17', 'M', 3),
(44, 1, '73106029', 'Ramiro', 'Benites Campos', '2004-05-21', 'M', 1),
(45, 1, '73106166', 'Karen', 'Campos Vargas', '1953-07-22', 'F', 4),
(46, 1, '73106303', 'Patricia', 'Benites Torres', '2002-11-17', 'F', 4),
(47, 1, '73106440', 'Ana', 'Rodríguez Carrasco', '1951-03-24', 'F', 3),
(48, 1, '73106577', 'Iván Jorge', 'Castro Cruz', '1972-11-27', 'M', 4),
(49, 1, '73106714', 'Pedro', 'Palomino Paredes', '1970-01-15', 'M', 4),
(50, 1, '73106851', 'Marco', 'Cruz Vargas', '1988-09-12', 'M', 2),
(51, 1, '73106988', 'Rosa', 'Soto Zapata', '1976-05-13', 'F', 2),
(52, 1, '73107125', 'Pedro', 'Castro Vásquez', '1952-04-08', 'M', 1),
(53, 1, '73107262', 'Pedro Miguel', 'Flores Ramos', '1998-06-11', 'M', 2),
(54, 1, '73107399', 'Delia Milagros', 'Torres León', '1965-04-15', 'F', 3),
(55, 1, '73107536', 'María', 'Salazar Soto', '1971-11-10', 'F', 2),
(56, 1, '73107673', 'Yolanda', 'Paredes Ríos', '1991-10-27', 'F', 3),
(57, 1, '73107810', 'Brayan Marco', 'Paredes Palomino', '1981-04-03', 'M', 2),
(58, 1, '73107947', 'Raúl Juan', 'Flores Ccama', '1955-03-21', 'M', 1),
(59, 1, '73108084', 'Úrsula', 'Montes Medina', '2002-03-10', 'F', 4),
(60, 1, '73108221', 'Iván Daniel', 'León Aguilar', '1968-03-26', 'M', 1),
(61, 1, '73108358', 'Rosa', 'Aguilar Lara', '2001-02-15', 'F', 2),
(62, 1, '73108495', 'Patricia', 'Medina Quispe', '2006-08-25', 'F', 2),
(63, 1, '73108632', 'Tomás', 'Ortiz Ccama', '1998-01-17', 'M', 1),
(64, 1, '73108769', 'Miguel Alberto', 'Medina Sánchez', '1996-09-12', 'M', 2),
(65, 1, '73108906', 'Daniel Juan', 'Valdez Lara', '1961-11-17', 'M', 3),
(66, 1, '73109043', 'Cristian Fabián', 'Ramos Ccama', '1992-07-17', 'M', 4),
(67, 1, '73109180', 'Bertha', 'León Rodríguez', '1989-08-21', 'F', 2),
(68, 1, '73109317', 'Carlos', 'Vásquez Quispe', '1976-12-24', 'M', 1),
(69, 1, '73109454', 'Teresa', 'Valdez Paredes', '1970-09-06', 'F', 1),
(70, 1, '73109591', 'Bertha Noemí', 'Gutiérrez Ramos', '1999-05-28', 'F', 1),
(71, 1, '73109728', 'Teresa', 'Salazar Montes', '2005-08-10', 'F', 2),
(72, 1, '73109865', 'César', 'Espinoza Ortiz', '1945-04-23', 'M', 1),
(73, 1, '73110002', 'Samuel', 'Vásquez Carrasco', '2006-01-11', 'M', 1),
(74, 1, '73110139', 'Claudia', 'León Campos', '2001-04-03', 'F', 2),
(75, 1, '73110276', 'Teresa', 'Mamani Salazar', '2003-04-08', 'F', 1),
(76, 1, '73110413', 'Marco', 'León Ccama', '1983-08-21', 'M', 2);

-- 80 camas, para que el tablero se vea como una guardia real. Estados: 26 disponibles, 37 ocupadas, 5 reservadas,
-- 7 en limpieza (cada una con su solicitud pendiente) y 5 fuera de servicio. Las 8 primeras conservan su estado original
-- (scripts/verificar_controladores.py las usa: TRA-02, UCI-01, OBS-01 y OBS-02 deben seguir disponibles).
-- Hospitalización (área 4, tipo 4) solo aparece de la 9 en adelante.
INSERT INTO cama (id_cama, codigo, id_area, id_tipo_cama, id_estado_cama, estado_registro) VALUES
(1, 'TRA-01', 1, 1, 3, 1), (2, 'TRA-02', 1, 1, 1, 1), (3, 'UCI-01', 2, 2, 1, 1),
(4, 'UCI-02', 2, 2, 4, 1), (5, 'UCI-03', 2, 2, 5, 1), (6, 'OBS-01', 3, 3, 1, 1),
(7, 'OBS-02', 3, 3, 1, 1), (8, 'OBS-03', 3, 3, 3, 1), (9, 'TRA-03', 1, 1, 3, 1),
(10, 'TRA-04', 1, 1, 4, 1), (11, 'UCI-04', 2, 2, 3, 1), (12, 'UCI-05', 2, 2, 3, 1),
(13, 'UCI-06', 2, 2, 1, 1), (14, 'OBS-04', 3, 3, 3, 1), (15, 'OBS-05', 3, 3, 3, 1),
(16, 'OBS-06', 3, 3, 2, 1), (17, 'OBS-07', 3, 3, 4, 1), (18, 'OBS-08', 3, 3, 1, 1),
(19, 'OBS-09', 3, 3, 1, 1), (20, 'OBS-10', 3, 3, 3, 1), (21, 'HOS-01', 4, 4, 3, 1),
(22, 'HOS-02', 4, 4, 3, 1), (23, 'HOS-03', 4, 4, 3, 1), (24, 'HOS-04', 4, 4, 2, 1),
(25, 'HOS-05', 4, 4, 4, 1), (26, 'HOS-06', 4, 4, 5, 1), (27, 'HOS-07', 4, 4, 3, 1),
(28, 'HOS-08', 4, 4, 3, 1), (29, 'HOS-09', 4, 4, 3, 1), (30, 'HOS-10', 4, 4, 3, 1),
(31, 'TRA-05', 1, 1, 3, 1), (32, 'UCI-07', 2, 2, 3, 1), (33, 'UCI-08', 2, 2, 3, 1),
(34, 'OBS-11', 3, 3, 3, 1), (35, 'OBS-12', 3, 3, 3, 1), (36, 'OBS-13', 3, 3, 3, 1),
(37, 'HOS-11', 4, 4, 3, 1), (38, 'HOS-12', 4, 4, 3, 1), (39, 'HOS-13', 4, 4, 3, 1),
(40, 'HOS-14', 4, 4, 3, 1), (41, 'TRA-06', 1, 1, 3, 1), (42, 'TRA-07', 1, 1, 1, 1),
(43, 'TRA-08', 1, 1, 1, 1), (44, 'UCI-09', 2, 2, 3, 1), (45, 'UCI-10', 2, 2, 3, 1),
(46, 'UCI-11', 2, 2, 3, 1), (47, 'UCI-12', 2, 2, 3, 1), (48, 'UCI-13', 2, 2, 2, 1),
(49, 'UCI-14', 2, 2, 4, 1), (50, 'UCI-15', 2, 2, 1, 1), (51, 'UCI-16', 2, 2, 5, 1),
(52, 'OBS-14', 3, 3, 3, 1), (53, 'OBS-15', 3, 3, 3, 1), (54, 'OBS-16', 3, 3, 3, 1),
(55, 'OBS-17', 3, 3, 3, 1), (56, 'OBS-18', 3, 3, 3, 1), (57, 'OBS-19', 3, 3, 2, 1),
(58, 'OBS-20', 3, 3, 4, 1), (59, 'OBS-21', 3, 3, 1, 1), (60, 'OBS-22', 3, 3, 1, 1),
(61, 'OBS-23', 3, 3, 1, 1), (62, 'OBS-24', 3, 3, 1, 1), (63, 'OBS-25', 3, 3, 1, 1),
(64, 'OBS-26', 3, 3, 1, 1), (65, 'OBS-27', 3, 3, 1, 1), (66, 'OBS-28', 3, 3, 5, 1),
(67, 'HOS-15', 4, 4, 3, 1), (68, 'HOS-16', 4, 4, 3, 1), (69, 'HOS-17', 4, 4, 2, 1),
(70, 'HOS-18', 4, 4, 1, 1), (71, 'HOS-19', 4, 4, 1, 1), (72, 'HOS-20', 4, 4, 1, 1),
(73, 'HOS-21', 4, 4, 1, 1), (74, 'HOS-22', 4, 4, 1, 1), (75, 'HOS-23', 4, 4, 4, 1),
(76, 'HOS-24', 4, 4, 1, 1), (77, 'HOS-25', 4, 4, 1, 1), (78, 'HOS-26', 4, 4, 1, 1),
(79, 'HOS-27', 4, 4, 1, 1), (80, 'HOS-28', 4, 4, 5, 1);

-- ==============================================================================
-- 3. DATOS TRANSACCIONALES
-- ==============================================================================
INSERT INTO episodio_emergencia (id_episodio, id_paciente, fecha_ingreso, motivo_consulta, id_estado_ep) VALUES
(1, 1, DATE_SUB(NOW(), INTERVAL 2 HOUR), 'Dolor intenso en pecho irradiado a brazo izquierdo, sudoración fría.', 3),
(2, 2, DATE_SUB(NOW(), INTERVAL 45 MINUTE), 'Caída de segundo piso, dolor fuerte en pierna derecha.', 2),
(3, 3, DATE_SUB(NOW(), INTERVAL 15 MINUTE), 'Fiebre persistente y malestar general desde ayer.', 2);

-- Episodios 4 a 74: 7 esperan triaje, 9 esperan cama (niveles 2 a 5, ninguno de nivel 1), 41 están en atención
-- con cama y 14 terminaron (ALTA MÉDICA, REFERIDO o FUGADO). Todos ingresaron en las últimas 24 horas.
INSERT INTO episodio_emergencia (id_episodio, id_paciente, fecha_ingreso, fecha_alta, motivo_consulta, id_estado_ep) VALUES
(4, 6, DATE_SUB(NOW(), INTERVAL 8 MINUTE), NULL, 'Dolor de garganta intenso y fiebre desde anoche.', 1),
(5, 7, DATE_SUB(NOW(), INTERVAL 22 MINUTE), NULL, 'Mareos y náuseas desde hace dos horas.', 1),
(6, 8, DATE_SUB(NOW(), INTERVAL 3 MINUTE), NULL, 'Hallado en la vía pública, desorientado y sin documentos.', 1),
(7, 9, DATE_SUB(NOW(), INTERVAL 35 MINUTE), NULL, 'Herida cortante profunda en el antebrazo con sangrado que no cede.', 2),
(8, 10, DATE_SUB(NOW(), INTERVAL 50 MINUTE), NULL, 'Dolor abdominal en la parte baja derecha desde la noche.', 2),
(9, 11, DATE_SUB(NOW(), INTERVAL 70 MINUTE), NULL, 'Vómitos repetidos desde la tarde.', 2),
(10, 12, DATE_SUB(NOW(), INTERVAL 95 MINUTE), NULL, 'Tos leve y malestar general.', 2),
(11, 13, DATE_SUB(NOW(), INTERVAL 60 MINUTE), NULL, 'Fiebre alta y decaimiento; es diabético e hipertenso.', 2),
(12, 14, DATE_SUB(NOW(), INTERVAL 240 MINUTE), NULL, 'Colapso en la vía pública, recuperado tras maniobras de reanimación.', 3),
(13, 15, DATE_SUB(NOW(), INTERVAL 360 MINUTE), NULL, 'Falta de aire intensa con labios morados.', 3),
(14, 16, DATE_SUB(NOW(), INTERVAL 300 MINUTE), NULL, 'Dolor opresivo en el pecho tras un esfuerzo.', 3),
(15, 17, DATE_SUB(NOW(), INTERVAL 25 MINUTE), NULL, 'Familiar la encontró confusa y somnolienta.', 3),
(16, 18, DATE_SUB(NOW(), INTERVAL 180 MINUTE), NULL, 'Dolor abdominal intenso con náuseas.', 3),
(17, 19, DATE_SUB(NOW(), INTERVAL 420 MINUTE), NULL, 'Fiebre alta con vómitos y deshidratación.', 3),
(18, 20, DATE_SUB(NOW(), INTERVAL 540 MINUTE), NULL, 'Herida en la mano por un vidrio.', 3),
(19, 21, DATE_SUB(NOW(), INTERVAL 720 MINUTE), NULL, 'Dolor abdominal tipo cólico, persistente.', 3),
(20, 22, DATE_SUB(NOW(), INTERVAL 900 MINUTE), NULL, 'Tos persistente con silbidos; antecedente de EPOC.', 3),
(21, 23, DATE_SUB(NOW(), INTERVAL 40 MINUTE), NULL, 'Herida infectada en la pierna izquierda.', 3),
(22, 24, DATE_SUB(NOW(), INTERVAL 600 MINUTE), DATE_SUB(NOW(), INTERVAL 120 MINUTE), 'Dolor abdominal intenso; mejoró con el tratamiento.', 4),
(23, 25, DATE_SUB(NOW(), INTERVAL 1200 MINUTE), DATE_SUB(NOW(), INTERVAL 90 MINUTE), 'Vómitos persistentes y deshidratación leve.', 4),
(24, 26, DATE_SUB(NOW(), INTERVAL 300 MINUTE), DATE_SUB(NOW(), INTERVAL 45 MINUTE), 'Politraumatismo por accidente de tránsito.', 5),
(25, 27, DATE_SUB(NOW(), INTERVAL 480 MINUTE), DATE_SUB(NOW(), INTERVAL 180 MINUTE), 'Herida superficial por una caída.', 4),
(26, 28, DATE_SUB(NOW(), INTERVAL 360 MINUTE), DATE_SUB(NOW(), INTERVAL 240 MINUTE), 'Vómitos y dolor de cabeza.', 6),
(27, 29, DATE_SUB(NOW(), INTERVAL 1320 MINUTE), DATE_SUB(NOW(), INTERVAL 1020 MINUTE), 'Fiebre alta de dos días.', 4),
(28, 30, DATE_SUB(NOW(), INTERVAL 200 MINUTE), NULL, 'Dolor en el pecho de origen poco claro; se deja en observación.', 3),
(29, 31, DATE_SUB(NOW(), INTERVAL 27 MINUTE), NULL, 'Esguince de tobillo jugando fútbol.', 1),
(30, 32, DATE_SUB(NOW(), INTERVAL 8 MINUTE), NULL, 'Esguince de tobillo jugando fútbol.', 1),
(31, 33, DATE_SUB(NOW(), INTERVAL 3 MINUTE), NULL, 'Esguince de tobillo jugando fútbol.', 1),
(32, 34, DATE_SUB(NOW(), INTERVAL 19 MINUTE), NULL, 'Hallado en la vía pública, desorientado y sin documentos.', 1),
(33, 35, DATE_SUB(NOW(), INTERVAL 121 MINUTE), NULL, 'Desorientación de inicio brusco.', 2),
(34, 36, DATE_SUB(NOW(), INTERVAL 53 MINUTE), NULL, 'Fiebre alta de dos días.', 2),
(35, 37, DATE_SUB(NOW(), INTERVAL 120 MINUTE), NULL, 'Náuseas y vómitos después de comer.', 2),
(36, 38, DATE_SUB(NOW(), INTERVAL 92 MINUTE), NULL, 'Rasguño infectado y tos leve.', 2),
(37, 39, DATE_SUB(NOW(), INTERVAL 220 MINUTE), NULL, 'Colapso en la vía pública, recuperado tras maniobras de reanimación.', 3),
(38, 40, DATE_SUB(NOW(), INTERVAL 309 MINUTE), NULL, 'Ahogo severo que no cede con su inhalador.', 3),
(39, 41, DATE_SUB(NOW(), INTERVAL 290 MINUTE), NULL, 'Dolor opresivo en el pecho con falta de aire.', 3),
(40, 42, DATE_SUB(NOW(), INTERVAL 103 MINUTE), NULL, 'Dificultad para respirar desde la noche.', 3),
(41, 43, DATE_SUB(NOW(), INTERVAL 578 MINUTE), NULL, 'Desorientación de inicio brusco.', 3),
(42, 44, DATE_SUB(NOW(), INTERVAL 272 MINUTE), NULL, 'Paro presenciado en el hogar; llega con pulso.', 3),
(43, 45, DATE_SUB(NOW(), INTERVAL 1104 MINUTE), NULL, 'Fiebre alta con vómitos y deshidratación.', 3),
(44, 46, DATE_SUB(NOW(), INTERVAL 786 MINUTE), NULL, 'Familiar lo encontró confuso y somnoliento.', 3),
(45, 47, DATE_SUB(NOW(), INTERVAL 222 MINUTE), NULL, 'Dolor opresivo en el pecho tras un esfuerzo.', 3),
(46, 48, DATE_SUB(NOW(), INTERVAL 483 MINUTE), NULL, 'Fiebre con tos desde hace tres días.', 3),
(47, 49, DATE_SUB(NOW(), INTERVAL 787 MINUTE), NULL, 'Fiebre y escalofríos desde ayer.', 3),
(48, 50, DATE_SUB(NOW(), INTERVAL 255 MINUTE), NULL, 'Rasguño infectado y tos leve.', 3),
(49, 51, DATE_SUB(NOW(), INTERVAL 541 MINUTE), NULL, 'Dolor abdominal tipo cólico, persistente.', 3),
(50, 52, DATE_SUB(NOW(), INTERVAL 208 MINUTE), NULL, 'Rasguño infectado y tos leve.', 3),
(51, 53, DATE_SUB(NOW(), INTERVAL 1214 MINUTE), NULL, 'Fiebre con tos desde hace tres días.', 3),
(52, 54, DATE_SUB(NOW(), INTERVAL 230 MINUTE), NULL, 'Dolor opresivo en el pecho tras un esfuerzo.', 3),
(53, 55, DATE_SUB(NOW(), INTERVAL 889 MINUTE), NULL, 'Rasguño infectado y tos leve.', 3),
(54, 56, DATE_SUB(NOW(), INTERVAL 107 MINUTE), NULL, 'Fiebre con tos desde hace tres días.', 3),
(55, 57, DATE_SUB(NOW(), INTERVAL 843 MINUTE), NULL, 'Rasguño infectado y tos leve.', 3),
(56, 58, DATE_SUB(NOW(), INTERVAL 1169 MINUTE), NULL, 'Solicita control por tos de una semana.', 3),
(57, 59, DATE_SUB(NOW(), INTERVAL 852 MINUTE), NULL, 'Vómitos repetidos desde la tarde.', 3),
(58, 60, DATE_SUB(NOW(), INTERVAL 251 MINUTE), NULL, 'Dolor abdominal intenso con náuseas.', 3),
(59, 61, DATE_SUB(NOW(), INTERVAL 239 MINUTE), NULL, 'Tos leve y malestar general.', 3),
(60, 62, DATE_SUB(NOW(), INTERVAL 752 MINUTE), NULL, 'Rasguño infectado y tos leve.', 3),
(61, 63, DATE_SUB(NOW(), INTERVAL 675 MINUTE), NULL, 'Náuseas y vómitos después de comer.', 3),
(62, 64, DATE_SUB(NOW(), INTERVAL 729 MINUTE), NULL, 'Tos leve y malestar general.', 3),
(63, 65, DATE_SUB(NOW(), INTERVAL 165 MINUTE), NULL, 'Fiebre y escalofríos desde ayer.', 3),
(64, 66, DATE_SUB(NOW(), INTERVAL 45 MINUTE), NULL, 'Fiebre alta con vómitos y deshidratación.', 3),
(65, 67, DATE_SUB(NOW(), INTERVAL 43 MINUTE), NULL, 'Dolor abdominal tipo cólico, persistente.', 3),
(66, 68, DATE_SUB(NOW(), INTERVAL 36 MINUTE), NULL, 'Rasguño infectado y tos leve.', 3),
(67, 69, DATE_SUB(NOW(), INTERVAL 568 MINUTE), DATE_SUB(NOW(), INTERVAL 96 MINUTE), 'Dolor opresivo en el pecho con falta de aire.', 5),
(68, 70, DATE_SUB(NOW(), INTERVAL 1119 MINUTE), DATE_SUB(NOW(), INTERVAL 278 MINUTE), 'Fiebre con tos desde hace tres días.', 4),
(69, 71, DATE_SUB(NOW(), INTERVAL 585 MINUTE), DATE_SUB(NOW(), INTERVAL 147 MINUTE), 'Rasguño infectado y tos leve.', 4),
(70, 72, DATE_SUB(NOW(), INTERVAL 1248 MINUTE), DATE_SUB(NOW(), INTERVAL 215 MINUTE), 'Herida en la mano por un vidrio.', 4),
(71, 73, DATE_SUB(NOW(), INTERVAL 836 MINUTE), DATE_SUB(NOW(), INTERVAL 223 MINUTE), 'Fiebre con tos desde hace tres días.', 4),
(72, 74, DATE_SUB(NOW(), INTERVAL 924 MINUTE), DATE_SUB(NOW(), INTERVAL 128 MINUTE), 'Solicita control por tos de una semana.', 4),
(73, 75, DATE_SUB(NOW(), INTERVAL 519 MINUTE), DATE_SUB(NOW(), INTERVAL 102 MINUTE), 'Herida en la mano por un vidrio.', 6),
(74, 76, DATE_SUB(NOW(), INTERVAL 798 MINUTE), DATE_SUB(NOW(), INTERVAL 279 MINUTE), 'Solicita control por tos de una semana.', 4);

-- FECHAS CORREGIDAS: Los signos se toman pocos minutos después del ingreso
INSERT INTO signos_vitales (id_si, id_episodio, pa_sis, pa_dia, fc, fr, temp, sato2, fecha_hora) VALUES
(1, 1, 165, 98, 118, 26, 37.2, 89, DATE_SUB(NOW(), INTERVAL 118 MINUTE)), 
(2, 2, 130, 85, 95, 20, 36.8, 97, DATE_SUB(NOW(), INTERVAL 42 MINUTE)),  
(3, 3, 120, 80, 85, 18, 39.5, 98, DATE_SUB(NOW(), INTERVAL 12 MINUTE));  

INSERT INTO signos_vitales (id_si, id_episodio, pa_sis, pa_dia, fc, fr, temp, sato2, fecha_hora) VALUES
(4, 7, 105, 70, 112, 22, 36.6, 95, DATE_SUB(NOW(), INTERVAL 32 MINUTE)),
(5, 8, 118, 76, 92, 18, 37.4, 98, DATE_SUB(NOW(), INTERVAL 47 MINUTE)),
(6, 9, 122, 78, 88, 17, 37.0, 98, DATE_SUB(NOW(), INTERVAL 67 MINUTE)),
(7, 10, 116, 74, 80, 16, 36.7, 99, DATE_SUB(NOW(), INTERVAL 92 MINUTE)),
(8, 11, 150, 90, 104, 20, 39.2, 96, DATE_SUB(NOW(), INTERVAL 57 MINUTE)),
(9, 12, 85, 55, 130, 28, 35.9, 91, DATE_SUB(NOW(), INTERVAL 237 MINUTE)),
(10, 13, 110, 70, 124, 30, 36.8, 88, DATE_SUB(NOW(), INTERVAL 357 MINUTE)),
(11, 14, 160, 100, 102, 22, 36.9, 95, DATE_SUB(NOW(), INTERVAL 297 MINUTE)),
(12, 15, 130, 85, 76, 16, 36.5, 97, DATE_SUB(NOW(), INTERVAL 22 MINUTE)),
(13, 16, 125, 82, 98, 20, 37.1, 98, DATE_SUB(NOW(), INTERVAL 177 MINUTE)),
(14, 17, 138, 84, 110, 22, 39.4, 95, DATE_SUB(NOW(), INTERVAL 417 MINUTE)),
(15, 18, 128, 82, 86, 17, 36.7, 99, DATE_SUB(NOW(), INTERVAL 537 MINUTE)),
(16, 19, 132, 84, 90, 18, 37.0, 98, DATE_SUB(NOW(), INTERVAL 717 MINUTE)),
(17, 20, 140, 86, 92, 22, 36.8, 94, DATE_SUB(NOW(), INTERVAL 897 MINUTE)),
(18, 21, 124, 80, 84, 17, 37.8, 98, DATE_SUB(NOW(), INTERVAL 37 MINUTE)),
(19, 22, 126, 82, 94, 19, 37.0, 98, DATE_SUB(NOW(), INTERVAL 597 MINUTE)),
(20, 23, 118, 76, 88, 17, 36.8, 98, DATE_SUB(NOW(), INTERVAL 1197 MINUTE)),
(21, 24, 88, 52, 128, 28, 36.2, 93, DATE_SUB(NOW(), INTERVAL 297 MINUTE)),
(22, 25, 120, 78, 82, 16, 36.6, 99, DATE_SUB(NOW(), INTERVAL 477 MINUTE)),
(23, 26, 121, 79, 90, 18, 37.0, 98, DATE_SUB(NOW(), INTERVAL 357 MINUTE)),
(24, 27, 134, 84, 96, 20, 39.0, 97, DATE_SUB(NOW(), INTERVAL 1317 MINUTE)),
(25, 28, 136, 86, 92, 18, 36.8, 96, DATE_SUB(NOW(), INTERVAL 197 MINUTE)),
(26, 33, 128, 85, 71, 16, 36.3, 97, DATE_SUB(NOW(), INTERVAL 118 MINUTE)),
(27, 34, 137, 82, 100, 20, 38.9, 97, DATE_SUB(NOW(), INTERVAL 50 MINUTE)),
(28, 35, 122, 77, 92, 17, 37.2, 98, DATE_SUB(NOW(), INTERVAL 117 MINUTE)),
(29, 36, 117, 76, 81, 17, 36.6, 99, DATE_SUB(NOW(), INTERVAL 89 MINUTE)),
(30, 37, 80, 56, 128, 29, 35.8, 91, DATE_SUB(NOW(), INTERVAL 217 MINUTE)),
(31, 38, 107, 72, 127, 30, 36.9, 88, DATE_SUB(NOW(), INTERVAL 306 MINUTE)),
(32, 39, 97, 61, 118, 27, 36.9, 89, DATE_SUB(NOW(), INTERVAL 287 MINUTE)),
(33, 40, 130, 80, 99, 25, 36.8, 93, DATE_SUB(NOW(), INTERVAL 100 MINUTE)),
(34, 41, 127, 83, 79, 15, 36.7, 97, DATE_SUB(NOW(), INTERVAL 575 MINUTE)),
(35, 42, 83, 57, 132, 27, 35.8, 91, DATE_SUB(NOW(), INTERVAL 269 MINUTE)),
(36, 43, 137, 87, 115, 21, 39.6, 95, DATE_SUB(NOW(), INTERVAL 1101 MINUTE)),
(37, 44, 128, 84, 71, 15, 36.7, 97, DATE_SUB(NOW(), INTERVAL 783 MINUTE)),
(38, 45, 160, 103, 102, 23, 36.9, 95, DATE_SUB(NOW(), INTERVAL 219 MINUTE)),
(39, 46, 130, 84, 88, 19, 38.8, 97, DATE_SUB(NOW(), INTERVAL 480 MINUTE)),
(40, 47, 131, 82, 100, 20, 39.1, 97, DATE_SUB(NOW(), INTERVAL 784 MINUTE)),
(41, 48, 120, 73, 81, 16, 36.6, 99, DATE_SUB(NOW(), INTERVAL 252 MINUTE)),
(42, 49, 126, 83, 98, 20, 37.2, 98, DATE_SUB(NOW(), INTERVAL 538 MINUTE)),
(43, 50, 113, 73, 87, 15, 36.6, 99, DATE_SUB(NOW(), INTERVAL 205 MINUTE)),
(44, 51, 135, 84, 89, 17, 38.4, 97, DATE_SUB(NOW(), INTERVAL 1211 MINUTE)),
(45, 52, 161, 98, 101, 21, 36.9, 95, DATE_SUB(NOW(), INTERVAL 227 MINUTE)),
(46, 53, 114, 78, 78, 16, 36.7, 99, DATE_SUB(NOW(), INTERVAL 886 MINUTE)),
(47, 54, 132, 82, 90, 19, 38.7, 97, DATE_SUB(NOW(), INTERVAL 104 MINUTE)),
(48, 55, 119, 78, 82, 16, 36.5, 99, DATE_SUB(NOW(), INTERVAL 840 MINUTE)),
(49, 56, 117, 76, 75, 16, 36.8, 99, DATE_SUB(NOW(), INTERVAL 1166 MINUTE)),
(50, 57, 117, 81, 83, 17, 37.2, 98, DATE_SUB(NOW(), INTERVAL 849 MINUTE)),
(51, 58, 129, 81, 94, 19, 36.9, 98, DATE_SUB(NOW(), INTERVAL 248 MINUTE)),
(52, 59, 119, 75, 75, 15, 36.7, 99, DATE_SUB(NOW(), INTERVAL 236 MINUTE)),
(53, 60, 118, 74, 80, 16, 36.4, 99, DATE_SUB(NOW(), INTERVAL 749 MINUTE)),
(54, 61, 119, 77, 91, 17, 36.9, 98, DATE_SUB(NOW(), INTERVAL 672 MINUTE)),
(55, 62, 117, 75, 85, 17, 36.7, 99, DATE_SUB(NOW(), INTERVAL 726 MINUTE)),
(56, 63, 135, 87, 91, 21, 39.1, 97, DATE_SUB(NOW(), INTERVAL 162 MINUTE)),
(57, 64, 138, 83, 111, 22, 39.6, 95, DATE_SUB(NOW(), INTERVAL 42 MINUTE)),
(58, 65, 121, 85, 97, 21, 36.9, 98, DATE_SUB(NOW(), INTERVAL 40 MINUTE)),
(59, 66, 117, 77, 80, 17, 36.7, 99, DATE_SUB(NOW(), INTERVAL 33 MINUTE)),
(60, 67, 102, 62, 115, 26, 36.6, 89, DATE_SUB(NOW(), INTERVAL 565 MINUTE)),
(61, 68, 130, 82, 94, 17, 38.8, 97, DATE_SUB(NOW(), INTERVAL 1116 MINUTE)),
(62, 69, 113, 73, 78, 15, 36.7, 99, DATE_SUB(NOW(), INTERVAL 582 MINUTE)),
(63, 70, 124, 80, 82, 17, 36.6, 99, DATE_SUB(NOW(), INTERVAL 1245 MINUTE)),
(64, 71, 132, 87, 86, 17, 38.4, 97, DATE_SUB(NOW(), INTERVAL 833 MINUTE)),
(65, 72, 117, 73, 79, 16, 36.7, 99, DATE_SUB(NOW(), INTERVAL 921 MINUTE)),
(66, 73, 123, 84, 88, 18, 36.8, 99, DATE_SUB(NOW(), INTERVAL 516 MINUTE)),
(67, 74, 119, 74, 77, 16, 36.5, 99, DATE_SUB(NOW(), INTERVAL 795 MINUTE));

INSERT INTO triaje (id_triaje, id_episodio, id_nivel, id_nivel_sugerido, id_empleado, fecha_hora, justificacion) VALUES
(1, 1, 1, 1, 3, DATE_SUB(NOW(), INTERVAL 115 MINUTE), NULL),
(2, 2, 2, 3, 3, DATE_SUB(NOW(), INTERVAL 40 MINUTE), 'Paciente con antecedente de fractura expuesta previa en la misma extremidad; se prioriza pese a signos vitales estables por alto riesgo de complicación vascular.'),
(3, 3, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 10 MINUTE), NULL);

-- RN-10: los triajes 8, 17, 21, 33, 40, 54 tienen el nivel final distinto del sugerido y llevan su justificación.
INSERT INTO triaje (id_triaje, id_episodio, id_nivel, id_nivel_sugerido, id_empleado, fecha_hora, justificacion) VALUES
(4, 7, 2, 2, 3, DATE_SUB(NOW(), INTERVAL 30 MINUTE), NULL),
(5, 8, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 45 MINUTE), NULL),
(6, 9, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 65 MINUTE), NULL),
(7, 10, 5, 5, 3, DATE_SUB(NOW(), INTERVAL 90 MINUTE), NULL),
(8, 11, 2, 3, 3, DATE_SUB(NOW(), INTERVAL 55 MINUTE), 'Paciente diabético e hipertenso con fiebre alta y decaimiento; se prioriza por riesgo de descompensación.'),
(9, 12, 1, 1, 3, DATE_SUB(NOW(), INTERVAL 235 MINUTE), NULL),
(10, 13, 1, 1, 3, DATE_SUB(NOW(), INTERVAL 355 MINUTE), NULL),
(11, 14, 2, 2, 3, DATE_SUB(NOW(), INTERVAL 295 MINUTE), NULL),
(12, 15, 2, 2, 3, DATE_SUB(NOW(), INTERVAL 20 MINUTE), NULL),
(13, 16, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 175 MINUTE), NULL),
(14, 17, 2, 2, 3, DATE_SUB(NOW(), INTERVAL 415 MINUTE), NULL),
(15, 18, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 535 MINUTE), NULL),
(16, 19, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 715 MINUTE), NULL),
(17, 20, 4, 5, 3, DATE_SUB(NOW(), INTERVAL 895 MINUTE), 'Antecedente de EPOC; se observa en hospitalización por riesgo de complicación respiratoria.'),
(18, 21, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 35 MINUTE), NULL),
(19, 22, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 595 MINUTE), NULL),
(20, 23, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 1195 MINUTE), NULL),
(21, 24, 1, 2, 3, DATE_SUB(NOW(), INTERVAL 295 MINUTE), 'Politraumatismo por accidente de tránsito con inestabilidad hemodinámica; se prioriza como nivel 1.'),
(22, 25, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 475 MINUTE), NULL),
(23, 26, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 355 MINUTE), NULL),
(24, 27, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 1315 MINUTE), NULL),
(25, 28, 2, 2, 3, DATE_SUB(NOW(), INTERVAL 195 MINUTE), NULL),
(26, 33, 2, 2, 3, DATE_SUB(NOW(), INTERVAL 116 MINUTE), NULL),
(27, 34, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 48 MINUTE), NULL),
(28, 35, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 115 MINUTE), NULL),
(29, 36, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 87 MINUTE), NULL),
(30, 37, 1, 1, 3, DATE_SUB(NOW(), INTERVAL 215 MINUTE), NULL),
(31, 38, 1, 1, 3, DATE_SUB(NOW(), INTERVAL 304 MINUTE), NULL),
(32, 39, 1, 1, 3, DATE_SUB(NOW(), INTERVAL 285 MINUTE), NULL),
(33, 40, 1, 2, 3, DATE_SUB(NOW(), INTERVAL 98 MINUTE), 'Adulto mayor con comorbilidades; se prioriza por riesgo de descompensación.'),
(34, 41, 2, 2, 3, DATE_SUB(NOW(), INTERVAL 573 MINUTE), NULL),
(35, 42, 1, 1, 3, DATE_SUB(NOW(), INTERVAL 267 MINUTE), NULL),
(36, 43, 2, 2, 3, DATE_SUB(NOW(), INTERVAL 1099 MINUTE), NULL),
(37, 44, 2, 2, 3, DATE_SUB(NOW(), INTERVAL 781 MINUTE), NULL),
(38, 45, 2, 2, 3, DATE_SUB(NOW(), INTERVAL 217 MINUTE), NULL),
(39, 46, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 478 MINUTE), NULL),
(40, 47, 2, 3, 3, DATE_SUB(NOW(), INTERVAL 782 MINUTE), 'Antecedente cardíaco conocido; se sube un nivel por riesgo de complicación.'),
(41, 48, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 250 MINUTE), NULL),
(42, 49, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 536 MINUTE), NULL),
(43, 50, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 203 MINUTE), NULL),
(44, 51, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 1209 MINUTE), NULL),
(45, 52, 2, 2, 3, DATE_SUB(NOW(), INTERVAL 225 MINUTE), NULL),
(46, 53, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 884 MINUTE), NULL),
(47, 54, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 102 MINUTE), NULL),
(48, 55, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 838 MINUTE), NULL),
(49, 56, 5, 5, 3, DATE_SUB(NOW(), INTERVAL 1164 MINUTE), NULL),
(50, 57, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 847 MINUTE), NULL),
(51, 58, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 246 MINUTE), NULL),
(52, 59, 5, 5, 3, DATE_SUB(NOW(), INTERVAL 234 MINUTE), NULL),
(53, 60, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 747 MINUTE), NULL),
(54, 61, 3, 4, 3, DATE_SUB(NOW(), INTERVAL 670 MINUTE), 'Paciente con dolor persistente pese a la analgesia; se prioriza tras la reevaluación.'),
(55, 62, 5, 5, 3, DATE_SUB(NOW(), INTERVAL 724 MINUTE), NULL),
(56, 63, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 160 MINUTE), NULL),
(57, 64, 2, 2, 3, DATE_SUB(NOW(), INTERVAL 40 MINUTE), NULL),
(58, 65, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 38 MINUTE), NULL),
(59, 66, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 31 MINUTE), NULL),
(60, 67, 1, 1, 3, DATE_SUB(NOW(), INTERVAL 563 MINUTE), NULL),
(61, 68, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 1114 MINUTE), NULL),
(62, 69, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 580 MINUTE), NULL),
(63, 70, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 1243 MINUTE), NULL),
(64, 71, 3, 3, 3, DATE_SUB(NOW(), INTERVAL 831 MINUTE), NULL),
(65, 72, 5, 5, 3, DATE_SUB(NOW(), INTERVAL 919 MINUTE), NULL),
(66, 73, 4, 4, 3, DATE_SUB(NOW(), INTERVAL 514 MINUTE), NULL),
(67, 74, 5, 5, 3, DATE_SUB(NOW(), INTERVAL 793 MINUTE), NULL);

INSERT INTO triaje_sintoma (id_triaje, id_sintoma) VALUES
(1, 2), (1, 3), (2, 7), (3, 6);

INSERT INTO triaje_sintoma (id_triaje, id_sintoma) VALUES
(4, 4), (5, 7), (6, 8), (7, 10), (8, 6), (9, 1),
(10, 3), (11, 2), (12, 5), (13, 7), (14, 6), (14, 8),
(15, 9), (16, 7), (17, 10), (18, 9), (19, 7), (20, 8),
(21, 4), (22, 9), (23, 8), (24, 6), (25, 2), (26, 5),
(27, 6), (28, 8), (29, 9), (29, 10), (30, 1), (31, 3),
(32, 2), (32, 3), (33, 3), (34, 5), (35, 1), (36, 6),
(36, 8), (37, 5), (38, 2), (39, 6), (39, 10), (40, 6),
(41, 9), (41, 10), (42, 7), (43, 9), (43, 10), (44, 6),
(44, 10), (45, 2), (46, 9), (46, 10), (47, 6), (47, 10),
(48, 9), (48, 10), (49, 10), (50, 8), (51, 7), (52, 10),
(53, 9), (53, 10), (54, 8), (55, 10), (56, 6), (57, 6),
(57, 8), (58, 7), (59, 9), (59, 10), (60, 2), (60, 3),
(61, 6), (61, 10), (62, 9), (62, 10), (63, 9), (64, 6),
(64, 10), (65, 10), (66, 9), (67, 10);

INSERT INTO asignacion_cama (id_asignacion, id_episodio, id_cama, id_empleado, fecha_asignacion, fecha_liberacion) VALUES
(1, 1, 1, 2, DATE_SUB(NOW(), INTERVAL 110 MINUTE), NULL); 

INSERT INTO asignacion_cama (id_asignacion, id_episodio, id_cama, id_empleado, fecha_asignacion, fecha_liberacion) VALUES
(2, 12, 9, 2, DATE_SUB(NOW(), INTERVAL 230 MINUTE), NULL),
(3, 13, 12, 2, DATE_SUB(NOW(), INTERVAL 350 MINUTE), NULL),
(4, 14, 11, 7, DATE_SUB(NOW(), INTERVAL 290 MINUTE), NULL),
(5, 15, 16, 2, DATE_SUB(NOW(), INTERVAL 5 MINUTE), NULL),
(6, 16, 14, 7, DATE_SUB(NOW(), INTERVAL 170 MINUTE), NULL),
(7, 17, 15, 2, DATE_SUB(NOW(), INTERVAL 410 MINUTE), NULL),
(8, 18, 21, 7, DATE_SUB(NOW(), INTERVAL 530 MINUTE), NULL),
(9, 19, 22, 2, DATE_SUB(NOW(), INTERVAL 710 MINUTE), NULL),
(10, 20, 23, 7, DATE_SUB(NOW(), INTERVAL 890 MINUTE), NULL),
(11, 21, 24, 2, DATE_SUB(NOW(), INTERVAL 10 MINUTE), NULL),
(12, 22, 17, 2, DATE_SUB(NOW(), INTERVAL 590 MINUTE), DATE_SUB(NOW(), INTERVAL 120 MINUTE)),
(13, 23, 25, 7, DATE_SUB(NOW(), INTERVAL 1190 MINUTE), DATE_SUB(NOW(), INTERVAL 90 MINUTE)),
(14, 24, 10, 2, DATE_SUB(NOW(), INTERVAL 290 MINUTE), DATE_SUB(NOW(), INTERVAL 45 MINUTE)),
(15, 25, 18, 7, DATE_SUB(NOW(), INTERVAL 470 MINUTE), DATE_SUB(NOW(), INTERVAL 180 MINUTE)),
(16, 27, 19, 2, DATE_SUB(NOW(), INTERVAL 1310 MINUTE), DATE_SUB(NOW(), INTERVAL 1020 MINUTE)),
(17, 28, 8, 7, DATE_SUB(NOW(), INTERVAL 190 MINUTE), NULL),
(18, 37, 31, 7, DATE_SUB(NOW(), INTERVAL 210 MINUTE), NULL),
(19, 38, 41, 7, DATE_SUB(NOW(), INTERVAL 292 MINUTE), NULL),
(20, 39, 32, 2, DATE_SUB(NOW(), INTERVAL 269 MINUTE), NULL),
(21, 40, 33, 7, DATE_SUB(NOW(), INTERVAL 84 MINUTE), NULL),
(22, 41, 44, 2, DATE_SUB(NOW(), INTERVAL 555 MINUTE), NULL),
(23, 42, 45, 2, DATE_SUB(NOW(), INTERVAL 255 MINUTE), NULL),
(24, 43, 46, 7, DATE_SUB(NOW(), INTERVAL 1085 MINUTE), NULL),
(25, 44, 47, 2, DATE_SUB(NOW(), INTERVAL 765 MINUTE), NULL),
(26, 45, 20, 7, DATE_SUB(NOW(), INTERVAL 205 MINUTE), NULL),
(27, 46, 34, 7, DATE_SUB(NOW(), INTERVAL 462 MINUTE), NULL),
(28, 47, 35, 7, DATE_SUB(NOW(), INTERVAL 770 MINUTE), NULL),
(29, 48, 36, 7, DATE_SUB(NOW(), INTERVAL 230 MINUTE), NULL),
(30, 49, 52, 7, DATE_SUB(NOW(), INTERVAL 526 MINUTE), NULL),
(31, 50, 53, 7, DATE_SUB(NOW(), INTERVAL 188 MINUTE), NULL),
(32, 51, 54, 7, DATE_SUB(NOW(), INTERVAL 1204 MINUTE), NULL),
(33, 52, 55, 2, DATE_SUB(NOW(), INTERVAL 206 MINUTE), NULL),
(34, 53, 56, 2, DATE_SUB(NOW(), INTERVAL 879 MINUTE), NULL),
(35, 54, 27, 7, DATE_SUB(NOW(), INTERVAL 96 MINUTE), NULL),
(36, 55, 28, 7, DATE_SUB(NOW(), INTERVAL 818 MINUTE), NULL),
(37, 56, 29, 7, DATE_SUB(NOW(), INTERVAL 1145 MINUTE), NULL),
(38, 57, 30, 2, DATE_SUB(NOW(), INTERVAL 830 MINUTE), NULL),
(39, 58, 37, 7, DATE_SUB(NOW(), INTERVAL 231 MINUTE), NULL),
(40, 59, 38, 7, DATE_SUB(NOW(), INTERVAL 220 MINUTE), NULL),
(41, 60, 39, 7, DATE_SUB(NOW(), INTERVAL 730 MINUTE), NULL),
(42, 61, 40, 2, DATE_SUB(NOW(), INTERVAL 660 MINUTE), NULL),
(43, 62, 67, 2, DATE_SUB(NOW(), INTERVAL 716 MINUTE), NULL),
(44, 63, 68, 2, DATE_SUB(NOW(), INTERVAL 145 MINUTE), NULL),
(45, 64, 48, 2, DATE_SUB(NOW(), INTERVAL 5 MINUTE), NULL),
(46, 65, 57, 7, DATE_SUB(NOW(), INTERVAL 5 MINUTE), NULL),
(47, 66, 69, 7, DATE_SUB(NOW(), INTERVAL 3 MINUTE), NULL),
(48, 67, 49, 2, DATE_SUB(NOW(), INTERVAL 558 MINUTE), DATE_SUB(NOW(), INTERVAL 96 MINUTE)),
(49, 68, 58, 2, DATE_SUB(NOW(), INTERVAL 1109 MINUTE), DATE_SUB(NOW(), INTERVAL 278 MINUTE)),
(50, 69, 75, 7, DATE_SUB(NOW(), INTERVAL 575 MINUTE), DATE_SUB(NOW(), INTERVAL 147 MINUTE)),
(51, 70, 60, 7, DATE_SUB(NOW(), INTERVAL 1238 MINUTE), DATE_SUB(NOW(), INTERVAL 215 MINUTE)),
(52, 71, 61, 7, DATE_SUB(NOW(), INTERVAL 826 MINUTE), DATE_SUB(NOW(), INTERVAL 223 MINUTE)),
(53, 72, 76, 7, DATE_SUB(NOW(), INTERVAL 914 MINUTE), DATE_SUB(NOW(), INTERVAL 128 MINUTE));

INSERT INTO solicitud_limpieza (id_solicitud, id_cama, id_empleado, fecha_solicitud, fecha_atencion) VALUES
(1, 4, NULL, DATE_SUB(NOW(), INTERVAL 30 MINUTE), NULL);

-- Pendientes (camas en limpieza): UCI-02 y OBS-07, HOS-05, TRA-04, UCI-14, OBS-20, HOS-23. Atendidas por el empleado 4: las que traen fecha de atención.
INSERT INTO solicitud_limpieza (id_solicitud, id_cama, id_empleado, fecha_solicitud, fecha_atencion) VALUES
(2, 17, NULL, DATE_SUB(NOW(), INTERVAL 120 MINUTE), NULL),
(3, 25, NULL, DATE_SUB(NOW(), INTERVAL 90 MINUTE), NULL),
(4, 10, NULL, DATE_SUB(NOW(), INTERVAL 45 MINUTE), NULL),
(5, 18, 4, DATE_SUB(NOW(), INTERVAL 180 MINUTE), DATE_SUB(NOW(), INTERVAL 150 MINUTE)),
(6, 19, 4, DATE_SUB(NOW(), INTERVAL 1020 MINUTE), DATE_SUB(NOW(), INTERVAL 990 MINUTE)),
(7, 49, NULL, DATE_SUB(NOW(), INTERVAL 96 MINUTE), NULL),
(8, 58, NULL, DATE_SUB(NOW(), INTERVAL 278 MINUTE), NULL),
(9, 75, NULL, DATE_SUB(NOW(), INTERVAL 147 MINUTE), NULL),
(10, 60, 4, DATE_SUB(NOW(), INTERVAL 215 MINUTE), DATE_SUB(NOW(), INTERVAL 177 MINUTE)),
(11, 61, 4, DATE_SUB(NOW(), INTERVAL 223 MINUTE), DATE_SUB(NOW(), INTERVAL 191 MINUTE)),
(12, 76, 4, DATE_SUB(NOW(), INTERVAL 128 MINUTE), DATE_SUB(NOW(), INTERVAL 94 MINUTE));

-- ==============================================================================
-- 4. HISTORIAL Y AUDITORÍA
-- ==============================================================================
INSERT INTO historial_estado_cama (id_historial, id_cama, id_estado_cama, fecha_cambio) VALUES
(1, 1, 1, DATE_SUB(NOW(), INTERVAL 3 DAY)),
(2, 1, 3, DATE_SUB(NOW(), INTERVAL 110 MINUTE)),
(3, 4, 3, DATE_SUB(NOW(), INTERVAL 2 DAY)),
(4, 4, 4, DATE_SUB(NOW(), INTERVAL 30 MINUTE)),
(5, 8, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(6, 8, 2, DATE_SUB(NOW(), INTERVAL 190 MINUTE)),
(7, 8, 3, DATE_SUB(NOW(), INTERVAL 185 MINUTE)),
(8, 9, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(9, 9, 2, DATE_SUB(NOW(), INTERVAL 230 MINUTE)),
(10, 9, 3, DATE_SUB(NOW(), INTERVAL 225 MINUTE)),
(11, 10, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(12, 10, 2, DATE_SUB(NOW(), INTERVAL 290 MINUTE)),
(13, 10, 3, DATE_SUB(NOW(), INTERVAL 285 MINUTE)),
(14, 10, 4, DATE_SUB(NOW(), INTERVAL 45 MINUTE)),
(15, 11, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(16, 11, 2, DATE_SUB(NOW(), INTERVAL 290 MINUTE)),
(17, 11, 3, DATE_SUB(NOW(), INTERVAL 285 MINUTE)),
(18, 12, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(19, 12, 2, DATE_SUB(NOW(), INTERVAL 350 MINUTE)),
(20, 12, 3, DATE_SUB(NOW(), INTERVAL 345 MINUTE)),
(21, 14, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(22, 14, 2, DATE_SUB(NOW(), INTERVAL 170 MINUTE)),
(23, 14, 3, DATE_SUB(NOW(), INTERVAL 165 MINUTE)),
(24, 15, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(25, 15, 2, DATE_SUB(NOW(), INTERVAL 410 MINUTE)),
(26, 15, 3, DATE_SUB(NOW(), INTERVAL 405 MINUTE)),
(27, 16, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(28, 16, 2, DATE_SUB(NOW(), INTERVAL 5 MINUTE)),
(29, 17, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(30, 17, 2, DATE_SUB(NOW(), INTERVAL 590 MINUTE)),
(31, 17, 3, DATE_SUB(NOW(), INTERVAL 585 MINUTE)),
(32, 17, 4, DATE_SUB(NOW(), INTERVAL 120 MINUTE)),
(33, 18, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(34, 18, 2, DATE_SUB(NOW(), INTERVAL 470 MINUTE)),
(35, 18, 3, DATE_SUB(NOW(), INTERVAL 465 MINUTE)),
(36, 18, 4, DATE_SUB(NOW(), INTERVAL 180 MINUTE)),
(37, 18, 1, DATE_SUB(NOW(), INTERVAL 150 MINUTE)),
(38, 19, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(39, 19, 2, DATE_SUB(NOW(), INTERVAL 1310 MINUTE)),
(40, 19, 3, DATE_SUB(NOW(), INTERVAL 1305 MINUTE)),
(41, 19, 4, DATE_SUB(NOW(), INTERVAL 1020 MINUTE)),
(42, 19, 1, DATE_SUB(NOW(), INTERVAL 990 MINUTE)),
(43, 20, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(44, 20, 2, DATE_SUB(NOW(), INTERVAL 205 MINUTE)),
(45, 20, 3, DATE_SUB(NOW(), INTERVAL 200 MINUTE)),
(46, 21, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(47, 21, 2, DATE_SUB(NOW(), INTERVAL 530 MINUTE)),
(48, 21, 3, DATE_SUB(NOW(), INTERVAL 525 MINUTE)),
(49, 22, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(50, 22, 2, DATE_SUB(NOW(), INTERVAL 710 MINUTE)),
(51, 22, 3, DATE_SUB(NOW(), INTERVAL 705 MINUTE)),
(52, 23, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(53, 23, 2, DATE_SUB(NOW(), INTERVAL 890 MINUTE)),
(54, 23, 3, DATE_SUB(NOW(), INTERVAL 885 MINUTE)),
(55, 24, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(56, 24, 2, DATE_SUB(NOW(), INTERVAL 10 MINUTE)),
(57, 25, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(58, 25, 2, DATE_SUB(NOW(), INTERVAL 1190 MINUTE)),
(59, 25, 3, DATE_SUB(NOW(), INTERVAL 1185 MINUTE)),
(60, 25, 4, DATE_SUB(NOW(), INTERVAL 90 MINUTE)),
(61, 26, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(62, 26, 5, DATE_SUB(NOW(), INTERVAL 600 MINUTE)),
(63, 27, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(64, 27, 2, DATE_SUB(NOW(), INTERVAL 96 MINUTE)),
(65, 27, 3, DATE_SUB(NOW(), INTERVAL 91 MINUTE)),
(66, 28, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(67, 28, 2, DATE_SUB(NOW(), INTERVAL 818 MINUTE)),
(68, 28, 3, DATE_SUB(NOW(), INTERVAL 813 MINUTE)),
(69, 29, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(70, 29, 2, DATE_SUB(NOW(), INTERVAL 1145 MINUTE)),
(71, 29, 3, DATE_SUB(NOW(), INTERVAL 1140 MINUTE)),
(72, 30, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(73, 30, 2, DATE_SUB(NOW(), INTERVAL 830 MINUTE)),
(74, 30, 3, DATE_SUB(NOW(), INTERVAL 825 MINUTE)),
(75, 31, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(76, 31, 2, DATE_SUB(NOW(), INTERVAL 210 MINUTE)),
(77, 31, 3, DATE_SUB(NOW(), INTERVAL 205 MINUTE)),
(78, 32, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(79, 32, 2, DATE_SUB(NOW(), INTERVAL 269 MINUTE)),
(80, 32, 3, DATE_SUB(NOW(), INTERVAL 264 MINUTE)),
(81, 33, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(82, 33, 2, DATE_SUB(NOW(), INTERVAL 84 MINUTE)),
(83, 33, 3, DATE_SUB(NOW(), INTERVAL 79 MINUTE)),
(84, 34, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(85, 34, 2, DATE_SUB(NOW(), INTERVAL 462 MINUTE)),
(86, 34, 3, DATE_SUB(NOW(), INTERVAL 457 MINUTE)),
(87, 35, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(88, 35, 2, DATE_SUB(NOW(), INTERVAL 770 MINUTE)),
(89, 35, 3, DATE_SUB(NOW(), INTERVAL 765 MINUTE)),
(90, 36, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(91, 36, 2, DATE_SUB(NOW(), INTERVAL 230 MINUTE)),
(92, 36, 3, DATE_SUB(NOW(), INTERVAL 225 MINUTE)),
(93, 37, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(94, 37, 2, DATE_SUB(NOW(), INTERVAL 231 MINUTE)),
(95, 37, 3, DATE_SUB(NOW(), INTERVAL 226 MINUTE)),
(96, 38, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(97, 38, 2, DATE_SUB(NOW(), INTERVAL 220 MINUTE)),
(98, 38, 3, DATE_SUB(NOW(), INTERVAL 215 MINUTE)),
(99, 39, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(100, 39, 2, DATE_SUB(NOW(), INTERVAL 730 MINUTE)),
(101, 39, 3, DATE_SUB(NOW(), INTERVAL 725 MINUTE)),
(102, 40, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(103, 40, 2, DATE_SUB(NOW(), INTERVAL 660 MINUTE)),
(104, 40, 3, DATE_SUB(NOW(), INTERVAL 655 MINUTE)),
(105, 41, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(106, 41, 2, DATE_SUB(NOW(), INTERVAL 292 MINUTE)),
(107, 41, 3, DATE_SUB(NOW(), INTERVAL 287 MINUTE)),
(108, 44, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(109, 44, 2, DATE_SUB(NOW(), INTERVAL 555 MINUTE)),
(110, 44, 3, DATE_SUB(NOW(), INTERVAL 550 MINUTE)),
(111, 45, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(112, 45, 2, DATE_SUB(NOW(), INTERVAL 255 MINUTE)),
(113, 45, 3, DATE_SUB(NOW(), INTERVAL 250 MINUTE)),
(114, 46, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(115, 46, 2, DATE_SUB(NOW(), INTERVAL 1085 MINUTE)),
(116, 46, 3, DATE_SUB(NOW(), INTERVAL 1080 MINUTE)),
(117, 47, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(118, 47, 2, DATE_SUB(NOW(), INTERVAL 765 MINUTE)),
(119, 47, 3, DATE_SUB(NOW(), INTERVAL 760 MINUTE)),
(120, 48, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(121, 48, 2, DATE_SUB(NOW(), INTERVAL 5 MINUTE)),
(122, 49, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(123, 49, 2, DATE_SUB(NOW(), INTERVAL 558 MINUTE)),
(124, 49, 3, DATE_SUB(NOW(), INTERVAL 553 MINUTE)),
(125, 49, 4, DATE_SUB(NOW(), INTERVAL 96 MINUTE)),
(126, 51, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(127, 51, 5, DATE_SUB(NOW(), INTERVAL 871 MINUTE)),
(128, 52, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(129, 52, 2, DATE_SUB(NOW(), INTERVAL 526 MINUTE)),
(130, 52, 3, DATE_SUB(NOW(), INTERVAL 521 MINUTE)),
(131, 53, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(132, 53, 2, DATE_SUB(NOW(), INTERVAL 188 MINUTE)),
(133, 53, 3, DATE_SUB(NOW(), INTERVAL 183 MINUTE)),
(134, 54, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(135, 54, 2, DATE_SUB(NOW(), INTERVAL 1204 MINUTE)),
(136, 54, 3, DATE_SUB(NOW(), INTERVAL 1199 MINUTE)),
(137, 55, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(138, 55, 2, DATE_SUB(NOW(), INTERVAL 206 MINUTE)),
(139, 55, 3, DATE_SUB(NOW(), INTERVAL 201 MINUTE)),
(140, 56, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(141, 56, 2, DATE_SUB(NOW(), INTERVAL 879 MINUTE)),
(142, 56, 3, DATE_SUB(NOW(), INTERVAL 874 MINUTE)),
(143, 57, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(144, 57, 2, DATE_SUB(NOW(), INTERVAL 5 MINUTE)),
(145, 58, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(146, 58, 2, DATE_SUB(NOW(), INTERVAL 1109 MINUTE)),
(147, 58, 3, DATE_SUB(NOW(), INTERVAL 1104 MINUTE)),
(148, 58, 4, DATE_SUB(NOW(), INTERVAL 278 MINUTE)),
(149, 60, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(150, 60, 2, DATE_SUB(NOW(), INTERVAL 1238 MINUTE)),
(151, 60, 3, DATE_SUB(NOW(), INTERVAL 1233 MINUTE)),
(152, 60, 4, DATE_SUB(NOW(), INTERVAL 215 MINUTE)),
(153, 60, 1, DATE_SUB(NOW(), INTERVAL 177 MINUTE)),
(154, 61, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(155, 61, 2, DATE_SUB(NOW(), INTERVAL 826 MINUTE)),
(156, 61, 3, DATE_SUB(NOW(), INTERVAL 821 MINUTE)),
(157, 61, 4, DATE_SUB(NOW(), INTERVAL 223 MINUTE)),
(158, 61, 1, DATE_SUB(NOW(), INTERVAL 191 MINUTE)),
(159, 66, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(160, 66, 5, DATE_SUB(NOW(), INTERVAL 438 MINUTE)),
(161, 67, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(162, 67, 2, DATE_SUB(NOW(), INTERVAL 716 MINUTE)),
(163, 67, 3, DATE_SUB(NOW(), INTERVAL 711 MINUTE)),
(164, 68, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(165, 68, 2, DATE_SUB(NOW(), INTERVAL 145 MINUTE)),
(166, 68, 3, DATE_SUB(NOW(), INTERVAL 140 MINUTE)),
(167, 69, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(168, 69, 2, DATE_SUB(NOW(), INTERVAL 3 MINUTE)),
(169, 75, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(170, 75, 2, DATE_SUB(NOW(), INTERVAL 575 MINUTE)),
(171, 75, 3, DATE_SUB(NOW(), INTERVAL 570 MINUTE)),
(172, 75, 4, DATE_SUB(NOW(), INTERVAL 147 MINUTE)),
(173, 76, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(174, 76, 2, DATE_SUB(NOW(), INTERVAL 914 MINUTE)),
(175, 76, 3, DATE_SUB(NOW(), INTERVAL 909 MINUTE)),
(176, 76, 4, DATE_SUB(NOW(), INTERVAL 128 MINUTE)),
(177, 76, 1, DATE_SUB(NOW(), INTERVAL 94 MINUTE)),
(178, 80, 1, DATE_SUB(NOW(), INTERVAL 2880 MINUTE)),
(179, 80, 5, DATE_SUB(NOW(), INTERVAL 553 MINUTE));

-- AUDITORÍA CORREGIDA: Se añade el ID del registro afectado
INSERT INTO bitacora_auditoria (id_bitacora, id_usuario, tabla_afectada, accion, id_registro_afectado, fecha_hora) VALUES
(1, 1, 'empleado', 'UPDATE', 6, DATE_SUB(NOW(), INTERVAL 3 HOUR)), -- Admin desactivó al empleado 6
(2, 3, 'paciente', 'INSERT', 1, DATE_SUB(NOW(), INTERVAL 120 MINUTE)), -- Enfermero registró al paciente 1
(3, 3, 'paciente', 'INSERT', 14, DATE_SUB(NOW(), INTERVAL 240 MINUTE)),
(4, 3, 'triaje', 'INSERT', 9, DATE_SUB(NOW(), INTERVAL 235 MINUTE)),
(6, 2, 'episodio_emergencia', 'UPDATE', 22, DATE_SUB(NOW(), INTERVAL 120 MINUTE)),
(7, 4, 'cama', 'UPDATE', 18, DATE_SUB(NOW(), INTERVAL 150 MINUTE)),
(8, 1, 'cama', 'UPDATE', 26, DATE_SUB(NOW(), INTERVAL 600 MINUTE)),
(9, 3, 'paciente', 'INSERT', 40, DATE_SUB(NOW(), INTERVAL 95 MINUTE)),
(10, 2, 'asignacion_cama', 'INSERT', 21, DATE_SUB(NOW(), INTERVAL 90 MINUTE)),
(11, 4, 'cama', 'UPDATE', 76, DATE_SUB(NOW(), INTERVAL 180 MINUTE));