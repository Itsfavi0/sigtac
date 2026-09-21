-- ==============================================================================
-- SISTEMA INTEGRADO DE GESTIÓN DE TRIAJE Y ASIGNACIÓN DE CAMAS (SIGTAC)
-- Orden de creación: Catálogos -> Maestras -> Transaccionales -> Auditoría
-- ==============================================================================

CREATE DATABASE IF NOT EXISTS sigtac_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_0900_ai_ci;

USE sigtac_db;
-- ==============================================================================
-- 0. LIMPIEZA PREVIA (ORDEN INVERSO DE DEPENDENCIAS)
-- ==============================================================================
DROP TABLE IF EXISTS bitacora_auditoria;
DROP TABLE IF EXISTS historial_estado_cama;
DROP TABLE IF EXISTS solicitud_limpieza;
DROP TABLE IF EXISTS asignacion_cama;
DROP TABLE IF EXISTS triaje_sintoma;
DROP TABLE IF EXISTS triaje;
DROP TABLE IF EXISTS signos_vitales;
DROP TABLE IF EXISTS episodio_emergencia;
DROP TABLE IF EXISTS cama;
DROP TABLE IF EXISTS paciente;
DROP TABLE IF EXISTS usuario;
DROP TABLE IF EXISTS empleado;
DROP TABLE IF EXISTS sintoma;
DROP TABLE IF EXISTS nivel_triaje;
DROP TABLE IF EXISTS tipo_cama;
DROP TABLE IF EXISTS area;
DROP TABLE IF EXISTS estado_cama;
DROP TABLE IF EXISTS estado_episodio;
DROP TABLE IF EXISTS seguro;
DROP TABLE IF EXISTS cargo;
DROP TABLE IF EXISTS rol;

-- ==============================================================================
-- 1. NIVEL 1: TABLAS DE CATÁLOGO
-- ==============================================================================

CREATE TABLE rol (
    id_rol INT AUTO_INCREMENT,
    nombre_rol VARCHAR(50) NOT NULL,
    
    CONSTRAINT PK_rol PRIMARY KEY (id_rol),
    CONSTRAINT UN_rol_nombre UNIQUE (nombre_rol)
) ENGINE=InnoDB;

CREATE TABLE cargo (
    id_cargo INT AUTO_INCREMENT,
    nombre_cargo VARCHAR(100) NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    
    CONSTRAINT PK_cargo PRIMARY KEY (id_cargo)
) ENGINE=InnoDB;

CREATE TABLE seguro (
    id_seguro INT AUTO_INCREMENT,
    nombre_seguro VARCHAR(100) NOT NULL,
    
    CONSTRAINT PK_seguro PRIMARY KEY (id_seguro),
    CONSTRAINT UN_seguro_nombre UNIQUE (nombre_seguro)
) ENGINE=InnoDB;

CREATE TABLE estado_episodio (
    id_estado_ep INT AUTO_INCREMENT,
    nombre_estado_episodio VARCHAR(50) NOT NULL,
    
    CONSTRAINT PK_estado_ep PRIMARY KEY (id_estado_ep),
    CONSTRAINT UN_estado_ep_nombre UNIQUE (nombre_estado_episodio)
) ENGINE=InnoDB;

CREATE TABLE estado_cama (
    id_estado_cama INT AUTO_INCREMENT,
    nombre_estado_cama VARCHAR(50) NOT NULL,
    
    CONSTRAINT PK_estado_cama PRIMARY KEY (id_estado_cama),
    CONSTRAINT UN_estado_cama_nombre UNIQUE (nombre_estado_cama)
) ENGINE=InnoDB;

CREATE TABLE area (
    id_area INT AUTO_INCREMENT,
    nombre_area VARCHAR(100) NOT NULL,
    piso VARCHAR(20) NOT NULL,
    
    CONSTRAINT PK_area PRIMARY KEY (id_area),
    CONSTRAINT UN_area_nombre UNIQUE (nombre_area)
) ENGINE=InnoDB;

CREATE TABLE tipo_cama (
    id_tipo_cama INT AUTO_INCREMENT,
    nombre_tipo_cama VARCHAR(100) NOT NULL,
    nivel_min INT NOT NULL COMMENT 'Nivel mínimo (1-5) que admite esta cama',
    
    CONSTRAINT PK_tipo_cama PRIMARY KEY (id_tipo_cama),
    CONSTRAINT UN_tipo_cama_nombre UNIQUE (nombre_tipo_cama),
    CONSTRAINT CH_tipo_cama_nivel CHECK (nivel_min BETWEEN 1 AND 5)
) ENGINE=InnoDB;

CREATE TABLE nivel_triaje (
    id_nivel INT AUTO_INCREMENT,
    numero INT NOT NULL COMMENT 'Escala numérica del 1 al 5',
    color VARCHAR(20) NOT NULL,
    tiempo_max_min INT NOT NULL COMMENT 'Tiempo máximo de espera normado',
    
    CONSTRAINT PK_nivel_triaje PRIMARY KEY (id_nivel),
    CONSTRAINT UN_nivel_triaje_numero UNIQUE (numero),
    CONSTRAINT CH_nivel_triaje_tiempo CHECK (tiempo_max_min >= 0)
) ENGINE=InnoDB;

CREATE TABLE sintoma (
    id_sintoma INT AUTO_INCREMENT,
    nombre_sintoma VARCHAR(200) NOT NULL,
    peso_clinico DECIMAL(5,2) NOT NULL,
    
    CONSTRAINT PK_sintoma PRIMARY KEY (id_sintoma),
    CONSTRAINT UN_sintoma_nombre UNIQUE (nombre_sintoma)
) ENGINE=InnoDB;

-- ==============================================================================
-- 2. NIVEL 2: TABLAS MAESTRAS
-- ==============================================================================

CREATE TABLE empleado (
    id_empleado INT AUTO_INCREMENT,
    dni VARCHAR(15) NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    colegiatura VARCHAR(20) NULL,
    id_cargo INT NOT NULL,
    
    CONSTRAINT PK_empleado PRIMARY KEY (id_empleado),
    CONSTRAINT UN_empleado_dni UNIQUE (dni),
    CONSTRAINT FK_empleado_cargo FOREIGN KEY (id_cargo) REFERENCES cargo(id_cargo) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE usuario (
    id_usuario INT AUTO_INCREMENT,
    id_empleado INT NOT NULL,
    id_rol INT NOT NULL,
    hash_clave VARCHAR(255) NOT NULL,
    
    CONSTRAINT PK_usuario PRIMARY KEY (id_usuario),
    CONSTRAINT UN_usuario_empleado UNIQUE (id_empleado),
    CONSTRAINT FK_usuario_empleado FOREIGN KEY (id_empleado) REFERENCES empleado(id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT FK_usuario_rol FOREIGN KEY (id_rol) REFERENCES rol(id_rol) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE paciente (
    id_paciente INT AUTO_INCREMENT,
    dni VARCHAR(15) NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    fecha_nac DATE NOT NULL,
    sexo CHAR(1) NOT NULL,
    id_seguro INT NOT NULL,
    estado_registro BOOLEAN DEFAULT TRUE COMMENT 'TRUE=Activo, FALSE=Anulado',
    
    CONSTRAINT PK_paciente PRIMARY KEY (id_paciente),
    CONSTRAINT UN_paciente_dni UNIQUE (dni),
    CONSTRAINT CH_paciente_sexo CHECK (sexo IN ('M', 'F')),
    CONSTRAINT CH_paciente_estado CHECK (estado_registro IN (0, 1)),
    CONSTRAINT FK_paciente_seguro FOREIGN KEY (id_seguro) REFERENCES seguro(id_seguro) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE cama (
    id_cama INT AUTO_INCREMENT,
    codigo VARCHAR(20) NOT NULL,
    id_area INT NOT NULL,
    id_tipo_cama INT NOT NULL,
    id_estado_cama INT NOT NULL,
    
    CONSTRAINT PK_cama PRIMARY KEY (id_cama),
    CONSTRAINT UN_cama_codigo UNIQUE (codigo),
    CONSTRAINT FK_cama_area FOREIGN KEY (id_area) REFERENCES area(id_area) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT FK_cama_tipo FOREIGN KEY (id_tipo_cama) REFERENCES tipo_cama(id_tipo_cama) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT FK_cama_estado FOREIGN KEY (id_estado_cama) REFERENCES estado_cama(id_estado_cama) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ==============================================================================
-- 3. NIVEL 3: TABLAS TRANSACCIONALES
-- ==============================================================================

CREATE TABLE episodio_emergencia (
    id_episodio INT AUTO_INCREMENT,
    id_paciente INT NOT NULL,
    fecha_ingreso DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_alta DATETIME NULL,
    motivo_consulta TEXT NOT NULL,
    id_estado_ep INT NOT NULL,
    estado_registro BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT PK_episodio_emergencia PRIMARY KEY (id_episodio),
    CONSTRAINT CH_episodio_fechas CHECK (fecha_alta IS NULL OR fecha_alta >= fecha_ingreso),
    CONSTRAINT FK_episodio_paciente FOREIGN KEY (id_paciente) REFERENCES paciente(id_paciente) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT FK_episodio_estado FOREIGN KEY (id_estado_ep) REFERENCES estado_episodio(id_estado_ep) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE signos_vitales (
    id_si INT AUTO_INCREMENT,
    id_episodio INT NOT NULL,
    pa_sis INT NOT NULL,
    pa_dia INT NOT NULL,
    fc INT NOT NULL,
    fr INT NOT NULL,
    temp DECIMAL(4,2) NOT NULL,
    sato2 INT NOT NULL,
    
    CONSTRAINT PK_signos_vitales PRIMARY KEY (id_si),
    CONSTRAINT CH_sv_presion CHECK (pa_sis > pa_dia),
    CONSTRAINT CH_sv_saturacion CHECK (sato2 BETWEEN 0 AND 100),
    CONSTRAINT FK_signos_episodio FOREIGN KEY (id_episodio) REFERENCES episodio_emergencia(id_episodio) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE triaje (
    id_triaje INT AUTO_INCREMENT,
    id_episodio INT NOT NULL,
    id_nivel INT NOT NULL,
    id_empleado INT NOT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado_registro BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT PK_triaje PRIMARY KEY (id_triaje),
    CONSTRAINT FK_triaje_episodio FOREIGN KEY (id_episodio) REFERENCES episodio_emergencia(id_episodio) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT FK_triaje_nivel FOREIGN KEY (id_nivel) REFERENCES nivel_triaje(id_nivel) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT FK_triaje_empleado FOREIGN KEY (id_empleado) REFERENCES empleado(id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE triaje_sintoma (
    id_triaje INT NOT NULL,
    id_sintoma INT NOT NULL,
    
    CONSTRAINT PK_triaje_sintoma PRIMARY KEY (id_triaje, id_sintoma),
    CONSTRAINT FK_ts_triaje FOREIGN KEY (id_triaje) REFERENCES triaje(id_triaje) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FK_ts_sintoma FOREIGN KEY (id_sintoma) REFERENCES sintoma(id_sintoma) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE asignacion_cama (
    id_asignacion INT AUTO_INCREMENT,
    id_episodio INT NOT NULL,
    id_cama INT NOT NULL,
    id_empleado INT NOT NULL,
    fecha_asignacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_liberacion DATETIME NULL,
    estado_registro BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT PK_asignacion_cama PRIMARY KEY (id_asignacion),
    CONSTRAINT CH_asignacion_fechas CHECK (fecha_liberacion IS NULL OR fecha_liberacion >= fecha_asignacion),
    CONSTRAINT FK_asig_episodio FOREIGN KEY (id_episodio) REFERENCES episodio_emergencia(id_episodio) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT FK_asig_cama FOREIGN KEY (id_cama) REFERENCES cama(id_cama) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT FK_asig_empleado FOREIGN KEY (id_empleado) REFERENCES empleado(id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE solicitud_limpieza (
    id_solicitud INT AUTO_INCREMENT,
    id_cama INT NOT NULL,
    id_empleado INT NULL,
    fecha_solicitud DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_atencion DATETIME NULL,
    
    CONSTRAINT PK_solicitud_limpieza PRIMARY KEY (id_solicitud),
    CONSTRAINT CH_limpieza_fechas CHECK (fecha_atencion IS NULL OR fecha_atencion >= fecha_solicitud),
    CONSTRAINT FK_limpieza_cama FOREIGN KEY (id_cama) REFERENCES cama(id_cama) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT FK_limpieza_empleado FOREIGN KEY (id_empleado) REFERENCES empleado(id_empleado) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ==============================================================================
-- 4. NIVEL 4: DOMINIO DE HISTORIAL Y AUDITORÍA
-- ==============================================================================

CREATE TABLE historial_estado_cama (
    id_historial INT AUTO_INCREMENT,
    id_cama INT NOT NULL,
    id_estado_cama INT NOT NULL,
    fecha_cambio DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT PK_historial_estado_cama PRIMARY KEY (id_historial),
    CONSTRAINT FK_historial_cama FOREIGN KEY (id_cama) REFERENCES cama(id_cama) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FK_historial_estado FOREIGN KEY (id_estado_cama) REFERENCES estado_cama(id_estado_cama) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

CREATE TABLE bitacora_auditoria (
    id_bitacora INT AUTO_INCREMENT,
    id_usuario INT NOT NULL,
    tabla_afectada VARCHAR(100) NOT NULL,
    accion VARCHAR(50) NOT NULL,
    fecha_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT PK_bitacora_auditoria PRIMARY KEY (id_bitacora),
    CONSTRAINT FK_auditoria_usuario FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;
