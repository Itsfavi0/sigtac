-- ==============================================================================
-- SIGTAC: usuario de base de datos para la aplicación (mínimo privilegio)
-- ==============================================================================
-- Ejecutar UNA vez, conectado como root (o como otro usuario administrador).
-- No borra ni modifica datos: solo crea el usuario y le da permisos.
--
-- Antes de ejecutar:
--   1. Reemplaza <una_clave_segura> por una clave propia (en las DOS sentencias donde aparece).
--   2. NO guardes este archivo con tu clave real: es un archivo versionado.
--      Escribe la clave solo en la pestaña de Workbench y en tu .env.
--
-- Permisos y motivo:
--   SELECT  -> leer (login, pacientes, camas, reportes)
--   INSERT  -> registrar pacientes, triajes, asignaciones y auditoría
--   UPDATE  -> estados de cama, baja lógica (estado_registro) y bloqueo de login
--   Sin DELETE: RN-11, el sistema nunca borra físicamente.
--   Sin DROP/CREATE/ALTER: solo los necesitan schema.sql y seed.sql, que ejecuta un administrador.
-- ==============================================================================

-- 'localhost': el usuario solo puede conectarse desde este mismo equipo.
CREATE USER IF NOT EXISTS 'sigtac_app'@'localhost' IDENTIFIED BY '<una_clave_segura>';

-- Si el usuario ya existía (por ejemplo, de un intento anterior), esto fija la clave indicada.
ALTER USER 'sigtac_app'@'localhost' IDENTIFIED BY '<una_clave_segura>';

-- Permisos solo sobre las tablas de sigtac_db, no sobre el resto del servidor.
GRANT SELECT, INSERT, UPDATE ON sigtac_db.* TO 'sigtac_app'@'localhost';

-- Comprobación: debe mostrar exactamente
--   GRANT USAGE ON *.* TO `sigtac_app`@`localhost`
--   GRANT SELECT, INSERT, UPDATE ON `sigtac_db`.* TO `sigtac_app`@`localhost`
-- (USAGE significa "puede conectarse", sin ningún permiso global.)
SHOW GRANTS FOR 'sigtac_app'@'localhost';
