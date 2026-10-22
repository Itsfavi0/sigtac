"""
Verificación contra MySQL real de la Fase 4: los cinco controladores (admisión, triaje,
camas, limpieza y reportes) y el SQL nuevo de los DAO (historial en bloque, FOR UPDATE, reportes).

Crea la base sigtac_scratch_tmp, carga schema.sql y seed.sql, ejecuta el flujo completo y elimina
la base al terminar. No toca sigtac_db. Se ejecuta con el .venv activado:

    python scripts/verificar_controladores.py

Necesita una cuenta de administrador de MySQL (sigtac_app no puede crear bases) y el cliente mysql
(variable MYSQL_CLI si no está en la ruta por defecto de Windows).

La clave de administrador se toma de la variable de entorno SIGTAC_ADMIN_PWD si existe (solo para
este proceso) o se pide con getpass. No se muestra, no se guarda y no se escribe en ningún archivo.
"""
import getpass
import os
import subprocess
import sys
import threading
import time
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import mysql.connector  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

BD_TEMPORAL = "sigtac_scratch_tmp"
MYSQL_CLI = os.getenv("MYSQL_CLI", r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe")
ESPERA = 1.5  # segundos que la "otra PC" mantiene su bloqueo

resultados = []


def comprobar(descripcion, condicion):
    resultados.append((descripcion, bool(condicion)))
    print(f"[{'OK' if condicion else 'FALLA'}] {descripcion}")


def uno(conexion, sql, params=()):
    cursor = conexion.cursor()
    cursor.execute(sql, params)
    fila = cursor.fetchone()
    cursor.close()
    return fila


def cargar_script(nombre, usuario, clave, host, puerto):
    texto = (RAIZ / "db_scripts" / nombre).read_text(encoding="utf-8").replace("sigtac_db", BD_TEMPORAL)
    entorno = dict(os.environ, MYSQL_PWD=clave)  # solo para este subproceso
    proceso = subprocess.run(
        [MYSQL_CLI, "-h", host, "-P", str(puerto), "-u", usuario, "--default-character-set=utf8mb4"],
        input=texto.encode("utf-8"), env=entorno, capture_output=True,
    )
    comprobar(f"{nombre} se carga sin errores", proceso.returncode == 0)
    if proceso.returncode != 0:
        print(proceso.stderr.decode("utf-8", "replace"))
        raise SystemExit(1)


def lanza(tipo, funcion, *args, **kwargs):
    try:
        funcion(*args, **kwargs)
    except tipo as e:
        return str(e) or True
    return False


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # la consola de Windows (cp1252) no imprime "→"
    load_dotenv(RAIZ / ".env")
    host = os.getenv("DB_HOST", "localhost")
    puerto = int(os.getenv("DB_PORT", "3306"))
    usuario = os.getenv("SIGTAC_ADMIN_USER") or input("Usuario administrador de MySQL [root]: ").strip() or "root"
    clave = os.getenv("SIGTAC_ADMIN_PWD") or getpass.getpass(f"Clave de {usuario} (no se muestra): ")

    admin = mysql.connector.connect(host=host, port=puerto, user=usuario, password=clave, autocommit=True)
    if uno(admin, "SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = %s", (BD_TEMPORAL,))[0]:
        print(f"La base {BD_TEMPORAL} ya existe: no se toca. Elimínala a mano si sobró de otra verificación.")
        return 1
    print("Servidor:", uno(admin, "SELECT VERSION()")[0])

    def otra_pc(autocommit=True):
        return mysql.connector.connect(host=host, port=puerto, user=usuario, password=clave,
                                       database=BD_TEMPORAL, autocommit=autocommit)

    try:
        cargar_script("schema.sql", usuario, clave, host, puerto)
        cargar_script("seed.sql", usuario, clave, host, puerto)
        os.environ.update(DB_HOST=host, DB_PORT=str(puerto), DB_USER=usuario, DB_PASS=clave, DB_NAME=BD_TEMPORAL)
        ejecutar_flujo(otra_pc)
    finally:
        admin.cursor().execute(f"DROP DATABASE IF EXISTS {BD_TEMPORAL}")
        admin.close()
        print(f"\nBase {BD_TEMPORAL} eliminada.")

    fallas = [d for d, ok in resultados if not ok]
    print(f"\n{len(resultados) - len(fallas)} de {len(resultados)} comprobaciones correctas.")
    return 1 if fallas else 0


def ejecutar_flujo(otra_pc):
    from controllers.auth_controller import Sesion
    from controllers.cama_controller import CamaController
    from controllers.paciente_controller import PacienteController
    from controllers.reporte_controller import ReporteController
    from controllers.triaje_controller import TriajeController
    from dao.db_connection import ConexionBD
    from dao.episodio_dao import EpisodioDAO
    from dao.triaje_dao import TriajeDAO
    from models.estados import EstadoCama, EstadoEpisodio
    from models.estrategias import ReglaManchester
    from models.excepciones import (CamaEstadoInvalidoError, ReglaNegocioError, UsuarioSinPermisoError)

    # Usuarios del seed: 1 admin, 2 jefe de guardia (médico), 3 enfermero de triaje, 4 limpieza
    admin = Sesion(1, 1, "Administrador", "Admin", "Sistema")
    jefe = Sesion(2, 2, "Jefe de Guardia", "Héctor", "Salazar")
    enfermero = Sesion(3, 3, "Enfermero de Triaje", "Favio", "Brañez")
    limpieza = Sesion(4, 4, "Personal de Limpieza", "Renzo", "Moya")
    pacientes, triajes = PacienteController(enfermero), TriajeController(enfermero, ReglaManchester())
    camas, camas_limpieza = CamaController(jefe), CamaController(limpieza)
    lector = otra_pc()

    def valor(sql, params=()):
        return uno(lector, sql, params)[0]

    def estado_cama(id_cama):
        return valor("SELECT e.nombre_estado_cama FROM cama c JOIN estado_cama e ON c.id_estado_cama = e.id_estado_cama "
                     "WHERE c.id_cama = %s", (id_cama,))

    def estado_ep(id_episodio):
        return valor("SELECT e.nombre_estado_episodio FROM episodio_emergencia ep JOIN estado_episodio e "
                     "ON ep.id_estado_ep = e.id_estado_ep WHERE ep.id_episodio = %s", (id_episodio,))

    def bitacora(tabla, accion, id_registro):
        return valor("SELECT COUNT(*) FROM bitacora_auditoria WHERE tabla_afectada = %s AND accion = %s "
                     "AND id_registro_afectado = %s", (tabla, accion, id_registro))

    def en_paralelo(sentencias):
        """La 'otra PC' bloquea y escribe en su transacción; confirma tras ESPERA segundos."""
        listo = threading.Event()

        def trabajar():
            con = otra_pc(autocommit=False)
            cur = con.cursor(buffered=True)
            for sql, params in sentencias:
                cur.execute(sql, params)
            listo.set()
            time.sleep(ESPERA)
            con.commit()
            con.close()

        hilo = threading.Thread(target=trabajar)
        hilo.start()
        listo.wait()
        return hilo

    SIGNOS = {"pa_sis": 120, "pa_dia": 80, "fc": 85, "fr": 18, "temp": 37.0, "sato2": 97}

    # ------------------------------------------------------------------ Admisión
    print("\n--- Admisión (paciente_controller)")
    nuevo = pacientes.registrar("DNI", "72345678", "Ana", "Torres Vega", date(1990, 4, 2), "F", 2)
    comprobar("registrar devuelve el paciente con id y nombre del seguro",
              nuevo.id_paciente and nuevo.nombre_seguro.startswith("SIS"))
    comprobar("el registro queda en la bitácora (INSERT paciente)", bitacora("paciente", "INSERT", nuevo.id_paciente) == 1)
    comprobar("un documento ya registrado se rechaza",
              lanza(ReglaNegocioError, pacientes.registrar, "DNI", "72345678", "Ana", "Torres", date(1990, 4, 2), "F", 2))
    ep_ana = pacientes.abrir_episodio(nuevo.id_paciente, "Dolor abdominal intenso desde la mañana")
    comprobar("abrir_episodio: EN ESPERA DE TRIAJE, fecha de ingreso de MySQL",
              ep_ana.estado == EstadoEpisodio.EN_ESPERA_TRIAJE and ep_ana.fecha_ingreso is not None)
    comprobar("no se abre un segundo episodio al mismo paciente",
              lanza(ReglaNegocioError, pacientes.abrir_episodio, nuevo.id_paciente, "Otra consulta"))
    comprobar("tampoco a un paciente del seed que ya está en emergencia (Carlos, episodio 2)",
              lanza(ReglaNegocioError, pacientes.abrir_episodio, 2, "Otra consulta"))
    comprobar("un enfermero no tiene permiso de reportes",
              lanza(UsuarioSinPermisoError, ReporteController(enfermero).estado_actual))

    print("\n--- Dos PCs admiten a la misma paciente a la vez (FOR UPDATE)")
    hilo = en_paralelo([
        ("SELECT id_paciente FROM paciente WHERE id_paciente = 4 FOR UPDATE", ()),
        ("INSERT INTO episodio_emergencia (id_paciente, motivo_consulta, id_estado_ep) VALUES (4, 'Admitida en la otra PC', 1)", ()),
    ])
    inicio = time.monotonic()
    error = lanza(ReglaNegocioError, pacientes.abrir_episodio, 4, "Admitida en esta PC")
    esperado = time.monotonic() - inicio
    hilo.join()
    comprobar(f"esta PC esperó el bloqueo de la otra ({esperado:.1f} s)", esperado >= ESPERA * 0.8)
    comprobar("y luego vio el episodio que abrió la otra: lo rechaza", error and "episodio abierto" in error)
    comprobar("la paciente 4 tiene un solo episodio", valor("SELECT COUNT(*) FROM episodio_emergencia WHERE id_paciente = 4") == 1)

    print("\n--- Pacientes NN")
    nn = pacientes.registrar_no_identificado("M", 50, 4)
    ep_nn = pacientes.abrir_episodio(nn.id_paciente, "Traído inconsciente por bomberos")
    comprobar("el NN aparece en listar_no_identificados",
              nn.id_paciente in [p.id_paciente for p in pacientes.listar_no_identificados()])
    comprobar("identificar con el documento de Rosa pide fusionar",
              "fusione" in str(lanza(ReglaNegocioError, pacientes.identificar, nn.id_paciente, "DNI", "70123456",
                                     "Rosa", "Mendoza", date(1959, 5, 14))))
    identificado = pacientes.identificar(nn.id_paciente, "DNI", "73456789", "Jorge", "Paredes Ruiz", date(1975, 8, 9))
    comprobar("identificar guarda el documento y audita IDENTIFICAR",
              identificado.identificado and valor("SELECT num_documento FROM paciente WHERE id_paciente = %s",
                                                  (nn.id_paciente,)) == "73456789"
              and bitacora("paciente", "IDENTIFICAR", nn.id_paciente) == 1)
    nn2 = pacientes.registrar_no_identificado("F", 30, 4)
    comprobar("fusionar un NN sin episodios con Rosa (que está en emergencia) mueve 0 episodios",
              pacientes.fusionar(nn2.id_paciente, 1) == 0)
    comprobar("el NN fusionado queda dado de baja y auditado (FUSIONAR)",
              valor("SELECT estado_registro FROM paciente WHERE id_paciente = %s", (nn2.id_paciente,)) == 0
              and bitacora("paciente", "FUSIONAR", nn2.id_paciente) == 1)
    nn3 = pacientes.registrar_no_identificado("M", 40, 4)
    pacientes.abrir_episodio(nn3.id_paciente, "Hallado en la vía pública")
    comprobar("no se fusiona un NN con episodio abierto con Rosa, que también tiene uno abierto",
              "Ambos" in str(lanza(ReglaNegocioError, pacientes.fusionar, nn3.id_paciente, 1)))

    # ------------------------------------------------------------------ Historial en bloque
    print("\n--- Historial en bloque (EpisodioDAO.listar_por_estado / listar_por_paciente)")
    uno_a_uno = EpisodioDAO.buscar_por_id(1)
    en_bloque = [e for e in EpisodioDAO.listar_por_estado(EstadoEpisodio.EN_ATENCION) if e.id_episodio == 1][0]
    comprobar("el episodio 1 cargado en bloque tiene el mismo historial que con buscar_por_id",
              [(t.id_triaje, t.nivel_final, [s.id_sintoma for s in t.sintomas]) for t in en_bloque.triajes]
              == [(t.id_triaje, t.nivel_final, [s.id_sintoma for s in t.sintomas]) for t in uno_a_uno.triajes]
              and [s.a_diccionario() for s in en_bloque.signos_vitales]
              == [s.a_diccionario() for s in uno_a_uno.signos_vitales])
    comprobar("listar_por_paciente(4) devuelve el episodio de la otra PC",
              [e.motivo_consulta for e in EpisodioDAO.listar_por_paciente(4)] == ["Admitida en la otra PC"])
    comprobar("bloquear fuera de una transacción es un error", lanza(RuntimeError, EpisodioDAO.bloquear, 1))

    # ------------------------------------------------------------------ Triaje
    print("\n--- Triaje (triaje_controller)")
    cola = triajes.cola_de_triaje()
    comprobar("la cola de triaje tiene a Ana, al NN identificado y a la paciente 4, por llegada",
              {e.episodio.id_episodio for e in cola} >= {ep_ana.id_episodio, ep_nn.id_episodio}
              and [e.episodio.fecha_ingreso for e in cola] == sorted(e.episodio.fecha_ingreso for e in cola))
    comprobar("cada entrada de la cola trae su paciente", all(e.paciente is not None for e in cola))
    sugerencia = triajes.sugerir(SIGNOS, [7])  # dolor abdominal intenso (5.0) → Manchester 3
    comprobar("sugerir: Manchester propone nivel 3 para dolor abdominal", sugerencia.nivel == 3)
    id_t_ana = triajes.registrar(ep_ana.id_episodio, SIGNOS, [7])
    comprobar("el primer triaje pasa el episodio a EN ESPERA DE CAMA", estado_ep(ep_ana.id_episodio) == "EN ESPERA DE CAMA")
    comprobar("el triaje queda con sugerido = final = 3 y su síntoma",
              uno(lector, "SELECT nf.numero, ns.numero FROM triaje t JOIN nivel_triaje nf ON t.id_nivel = nf.id_nivel "
                          "JOIN nivel_triaje ns ON t.id_nivel_sugerido = ns.id_nivel WHERE t.id_triaje = %s",
                  (id_t_ana,)) == (3, 3)
              and valor("SELECT COUNT(*) FROM triaje_sintoma WHERE id_triaje = %s", (id_t_ana,)) == 1)
    comprobar("el triaje se audita con niveles y protocolo",
              "ReglaManchester" in valor("SELECT CAST(detalles_json AS CHAR) FROM bitacora_auditoria WHERE tabla_afectada "
                                         "= 'triaje' AND id_registro_afectado = %s", (id_t_ana,)))
    id_t_nn = triajes.registrar(ep_nn.id_episodio, SIGNOS, [9], nivel_final=2,
                                justificacion="Paciente traído inconsciente; se prioriza por mecanismo de lesión.")
    comprobar("una reclasificación guarda el sugerido (4) y el final (2) con su justificación",
              uno(lector, "SELECT nf.numero, ns.numero, justificacion IS NOT NULL FROM triaje t "
                          "JOIN nivel_triaje nf ON t.id_nivel = nf.id_nivel JOIN nivel_triaje ns "
                          "ON t.id_nivel_sugerido = ns.id_nivel WHERE t.id_triaje = %s", (id_t_nn,)) == (2, 4, 1))
    comprobar("una reclasificación sin justificación no llega a la BD",
              lanza(ValueError, triajes.registrar, ep_nn.id_episodio, SIGNOS, [9], nivel_final=1)
              and valor("SELECT COUNT(*) FROM triaje WHERE id_episodio = %s", (ep_nn.id_episodio,)) == 1)

    print("\n--- Otra PC da de alta un episodio mientras se registra su triaje (FOR UPDATE)")
    hilo = en_paralelo([
        ("SELECT id_episodio FROM episodio_emergencia WHERE id_episodio = 3 FOR UPDATE", ()),
        ("UPDATE episodio_emergencia SET id_estado_ep = 4, fecha_alta = NOW() WHERE id_episodio = 3", ()),
    ])
    inicio = time.monotonic()
    error = lanza(ReglaNegocioError, triajes.registrar, 3, SIGNOS, [])
    esperado = time.monotonic() - inicio
    hilo.join()
    comprobar(f"el triaje esperó el bloqueo ({esperado:.1f} s) y luego vio el alta: lo rechaza",
              esperado >= ESPERA * 0.8 and error)
    comprobar("no se guardó ni triaje ni signos vitales nuevos en el episodio 3",
              valor("SELECT COUNT(*) FROM triaje WHERE id_episodio = 3") == 1
              and valor("SELECT COUNT(*) FROM signos_vitales WHERE id_episodio = 3") == 1)

    # ------------------------------------------------------------------ Camas
    print("\n--- Camas (cama_controller)")
    cola = camas.cola_de_espera()
    niveles = [e.nivel for e in cola]
    comprobar(f"la cola de cama está ordenada por nivel ({niveles})", niveles == sorted(niveles) and None not in niveles)
    comprobar("el primero de la cola es nivel 2 (Carlos, episodio 2 o el NN reclasificado)", niveles[0] == 2)
    compatibles = [c.codigo for c in camas.camas_compatibles(2)]
    comprobar(f"camas compatibles con nivel 2: UCI y observación, no trauma shock ({compatibles})",
              compatibles == ["OBS-01", "OBS-02", "UCI-01"] or set(compatibles) == {"UCI-01", "OBS-01", "OBS-02"})
    comprobar("asignar una cama de trauma shock a un nivel 2 se rechaza",
              "compatible" in str(lanza(ReglaNegocioError, camas.asignar, 2, 2)))
    comprobar("un enfermero no puede asignar camas", lanza(UsuarioSinPermisoError, CamaController(enfermero).asignar, 2, 3))
    id_asig = camas.asignar(2, 3)
    comprobar("asignar: cama RESERVADA, episodio EN ATENCIÓN, asignación vigente, historial y bitácora",
              estado_cama(3) == "RESERVADA" and estado_ep(2) == "EN ATENCIÓN (CON CAMA)"
              and valor("SELECT cama_vigente FROM asignacion_cama WHERE id_asignacion = %s", (id_asig,)) == 3
              and valor("SELECT COUNT(*) FROM historial_estado_cama WHERE id_cama = 3") == 1
              and bitacora("asignacion_cama", "INSERT", id_asig) == 1)
    comprobar("la misma cama no se asigna a otro episodio (RN-05)",
              lanza(CamaEstadoInvalidoError, camas.asignar, ep_nn.id_episodio, 3) and estado_ep(ep_nn.id_episodio) == "EN ESPERA DE CAMA")
    comprobar("no se da de alta si el paciente aún no llegó a la cama (se deshace todo)",
              lanza(CamaEstadoInvalidoError, camas.dar_alta, 2) and estado_ep(2) == "EN ATENCIÓN (CON CAMA)"
              and estado_cama(3) == "RESERVADA")
    camas.ocupar(3)
    comprobar("ocupar: RESERVADA → OCUPADA, auditado", estado_cama(3) == "OCUPADA" and bitacora("cama", "UPDATE", 3) == 1)
    id_sol = camas.dar_alta(2)
    comprobar("dar_alta: episodio ALTA con fecha de alta, cama EN LIMPIEZA, asignación liberada, solicitud pendiente",
              estado_ep(2) == "ALTA MÉDICA"
              and valor("SELECT fecha_alta IS NOT NULL FROM episodio_emergencia WHERE id_episodio = 2") == 1
              and estado_cama(3) == "EN LIMPIEZA"
              and valor("SELECT fecha_liberacion IS NOT NULL FROM asignacion_cama WHERE id_asignacion = %s", (id_asig,)) == 1
              and valor("SELECT fecha_atencion IS NULL FROM solicitud_limpieza WHERE id_solicitud = %s", (id_sol,)) == 1)
    comprobar("un episodio dado de alta no admite triajes", lanza(ReglaNegocioError, triajes.registrar, 2, SIGNOS, []))

    print("\n--- Cancelar una reserva")
    id_asig2 = camas.asignar(ep_ana.id_episodio, 6)  # nivel 3 → observación
    camas.cancelar_asignacion(ep_ana.id_episodio)
    comprobar("cancelar: cama DISPONIBLE sin limpieza, episodio vuelve a la cola, asignación anulada",
              estado_cama(6) == "DISPONIBLE" and estado_ep(ep_ana.id_episodio) == "EN ESPERA DE CAMA"
              and valor("SELECT estado_registro FROM asignacion_cama WHERE id_asignacion = %s", (id_asig2,)) == 0
              and bitacora("asignacion_cama", "ANULAR", id_asig2) == 1)
    comprobar("después de cancelar, el episodio puede recibir otra cama", camas.asignar(ep_ana.id_episodio, 7) > 0)

    print("\n--- Limpieza")
    pendientes = [s.id_solicitud for s in camas_limpieza.solicitudes_limpieza()]
    comprobar(f"la bandeja tiene la del seed y la del alta ({pendientes})", pendientes == [1, id_sol])
    comprobar("un médico no confirma limpiezas (RN-08)", lanza(UsuarioSinPermisoError, camas.confirmar_limpieza, id_sol))
    camas_limpieza.confirmar_limpieza(id_sol)
    comprobar("confirmar_limpieza: cama DISPONIBLE, solicitud atendida por el empleado 4",
              estado_cama(3) == "DISPONIBLE"
              and valor("SELECT id_empleado FROM solicitud_limpieza WHERE id_solicitud = %s", (id_sol,)) == 4)
    comprobar("una solicitud ya atendida no se confirma dos veces",
              lanza(ReglaNegocioError, camas_limpieza.confirmar_limpieza, id_sol))

    # ------------------------------------------------------------------ Reportes
    print("\n--- Reportes (reporte_controller)")
    reportes = ReporteController(admin)
    estado = reportes.estado_actual()
    total_camas = valor("SELECT COUNT(*) FROM cama WHERE estado_registro = TRUE")
    comprobar("camas por estado suma el total de camas activas", sum(estado.camas_por_estado.values()) == total_camas)
    en_uso = valor("SELECT COUNT(*) FROM cama c JOIN estado_cama e ON c.id_estado_cama = e.id_estado_cama "
                   "WHERE e.nombre_estado_cama IN ('RESERVADA', 'OCUPADA')")
    fuera = estado.camas_por_estado[EstadoCama.FUERA_SERVICIO]
    comprobar(f"ocupación {estado.porcentaje_ocupacion} % = en uso / en servicio",
              estado.porcentaje_ocupacion == round(100 * en_uso / (total_camas - fuera), 1))
    abiertos = valor("SELECT COUNT(*) FROM episodio_emergencia ep JOIN estado_episodio e ON ep.id_estado_ep = e.id_estado_ep "
                     "WHERE ep.estado_registro = TRUE AND e.nombre_estado_episodio IN "
                     "('EN ESPERA DE TRIAJE', 'EN ESPERA DE CAMA', 'EN ATENCIÓN (CON CAMA)')")
    comprobar(f"pacientes en emergencia ({estado.pacientes_en_emergencia}) coincide con la BD",
              estado.pacientes_en_emergencia == abiertos)
    hoy = date.today()
    ind = reportes.indicadores(hoy - timedelta(days=1), hoy)
    comprobar(f"ingresos del período ({ind.ingresos}) coincide con la BD",
              ind.ingresos == valor("SELECT COUNT(*) FROM episodio_emergencia WHERE estado_registro = TRUE"))
    comprobar(f"triajes por nivel {ind.triajes_por_nivel} suma los triajes activos",
              sorted(ind.triajes_por_nivel) == [1, 2, 3, 4, 5]
              and ind.total_triajes == valor("SELECT COUNT(*) FROM triaje WHERE estado_registro = TRUE"))
    reclasificados = valor("SELECT COUNT(*) FROM triaje WHERE id_nivel <> id_nivel_sugerido")
    comprobar(f"reclasificación {ind.porcentaje_reclasificacion} % ({reclasificados} de {ind.total_triajes})",
              ind.porcentaje_reclasificacion == round(100 * reclasificados / ind.total_triajes, 1))
    comprobar(f"tiempos promedio en minutos (triaje {ind.espera_triaje_min}, cama {ind.espera_cama_min}, "
              f"estancia {ind.estancia_min})",
              all(v is not None and v >= 0 for v in (ind.espera_triaje_min, ind.espera_cama_min, ind.estancia_min)))
    comprobar("la espera de cama no cuenta la reserva cancelada",
              ind.espera_cama_min == round(float(valor(
                  "SELECT AVG(TIMESTAMPDIFF(MINUTE, ep.fecha_ingreso, a.fecha_asignacion)) FROM asignacion_cama a "
                  "JOIN episodio_emergencia ep ON a.id_episodio = ep.id_episodio WHERE a.estado_registro = TRUE")), 1))

    lector.close()
    ConexionBD().cerrar_conexion()


if __name__ == "__main__":
    raise SystemExit(main())
