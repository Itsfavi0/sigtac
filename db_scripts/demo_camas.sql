-- ==============================================================================
-- SIGTAC — camas adicionales para la demostración (OPCIONAL)
--
-- seed.sql deja 8 camas, suficientes para las pruebas pero pocas para que el tablero se vea como una
-- guardia real en el proyector. Este script AGREGA 22 camas disponibles (30 en total) y por primera vez
-- camas de Hospitalización, que el seed no tiene.
--
-- No borra ni modifica nada: solo inserta. Se ejecuta UNA vez, después de seed.sql:
--     mysql -u <admin> -p < db_scripts/seed.sql
--     mysql -u <admin> -p < db_scripts/demo_camas.sql
-- Si se ejecuta dos veces, falla sin cambiar nada (los códigos de cama son únicos: UN_cama_codigo).
--
-- Solo para la base de desarrollo. scripts/verificar_controladores.py no lo usa.
-- ==============================================================================

USE sigtac_db;

-- id_area: 1 Trauma Shock, 2 UCI, 3 Observación, 4 Hospitalización A
-- id_tipo_cama: 1 Trauma Shock, 2 UCI, 3 Observación, 4 Hospitalización
-- id_estado_cama: 1 DISPONIBLE (todas: una cama ocupada necesitaría su paciente y su asignación)
INSERT INTO cama (codigo, id_area, id_tipo_cama, id_estado_cama, estado_registro) VALUES
('TRA-03', 1, 1, 1, 1), ('TRA-04', 1, 1, 1, 1),
('UCI-04', 2, 2, 1, 1), ('UCI-05', 2, 2, 1, 1), ('UCI-06', 2, 2, 1, 1),
('OBS-04', 3, 3, 1, 1), ('OBS-05', 3, 3, 1, 1), ('OBS-06', 3, 3, 1, 1), ('OBS-07', 3, 3, 1, 1),
('OBS-08', 3, 3, 1, 1), ('OBS-09', 3, 3, 1, 1), ('OBS-10', 3, 3, 1, 1),
('HOS-01', 4, 4, 1, 1), ('HOS-02', 4, 4, 1, 1), ('HOS-03', 4, 4, 1, 1), ('HOS-04', 4, 4, 1, 1),
('HOS-05', 4, 4, 1, 1), ('HOS-06', 4, 4, 1, 1), ('HOS-07', 4, 4, 1, 1), ('HOS-08', 4, 4, 1, 1),
('HOS-09', 4, 4, 1, 1), ('HOS-10', 4, 4, 1, 1);
