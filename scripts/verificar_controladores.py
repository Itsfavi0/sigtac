"""
Verificación contra MySQL real de la Fase 4: los controladores (admisión, triaje, camas, limpieza,
reportes y administración) y el SQL nuevo de los DAO (historial en bloque, FOR UPDATE, reportes,
cuentas de usuario y bitácora), incluido el login real con una cuenta creada por el administrador.

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
        # El nombre de una base no puede ir como parámetro (%s); BD_TEMPORAL es una constante del script.
        admin.cursor().execute("DROP DATABASE IF EXISTS " + BD_TEMPORAL)
        admin.close()
        print(f"\nBase {BD_TEMPORAL} eliminada.")

    fallas = [d for d, ok in resultados if not ok]
    print(f"\n{len(resultados) - len(fallas)} de {len(resultados)} comprobaciones correctas.")
    return 1 if fallas else 0


def ejecutar_flujo(otra_pc):
    from controllers.admin_controller import AdminController
    from controllers.auth_controller import AuthController, Sesion
    from controllers.cama_controller import CamaController
    from controllers.paciente_controller import PacienteController
    from controllers.reporte_controller import ReporteController
    from controllers.triaje_controller import TriajeController
    from dao.cama_dao import CamaDAO
    from dao.db_connection import ConexionBD
    from dao.episodio_dao import EpisodioDAO
    from dao.usuario_dao import UsuarioDAO
    from models.estados import EstadoCama, EstadoEpisodio
    from models.estrategias import ReglaManchester
    from models.excepciones import (AutenticacionError, CamaEstadoInvalidoError, RegistroDuplicadoError,
                                    ReglaNegocioError, UsuarioSinPermisoError)
    from models.permisos import Rol

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

    # ------------------------------------------------------------------ Referir y fuga
    print("\n--- Referir y registrar una fuga (cama_controller)")
    comprobar("referir un episodio sin triaje se rechaza (nn3 espera triaje)",
              "falta el triaje" in str(lanza(ReglaNegocioError, camas.referir,
                                             EpisodioDAO.listar_por_paciente(nn3.id_paciente)[0].id_episodio)))
    comprobar("referir sin cama: el NN reclasificado pasa a REFERIDO con fecha de egreso de MySQL",
              camas.referir(ep_nn.id_episodio) is None and estado_ep(ep_nn.id_episodio) == "REFERIDO"
              and valor("SELECT fecha_alta IS NOT NULL FROM episodio_emergencia WHERE id_episodio = %s",
                        (ep_nn.id_episodio,)) == 1)
    asig_ana = valor("SELECT id_asignacion FROM asignacion_cama WHERE id_episodio = %s AND fecha_liberacion IS NULL "
                     "AND estado_registro = TRUE", (ep_ana.id_episodio,))
    comprobar("fuga con cama reservada: FUGADO, la cama 7 vuelve a DISPONIBLE y la asignación se anula",
              camas.registrar_fuga(ep_ana.id_episodio) is None and estado_ep(ep_ana.id_episodio) == "FUGADO / ABANDONO"
              and estado_cama(7) == "DISPONIBLE"
              and valor("SELECT estado_registro FROM asignacion_cama WHERE id_asignacion = %s", (asig_ana,)) == 0)
    ep_otra = EpisodioDAO.listar_por_paciente(4)[0].id_episodio
    triajes.registrar(ep_otra, SIGNOS, [7])
    camas.asignar(ep_otra, 6)
    camas.ocupar(6)
    id_sol_ref = camas.referir(ep_otra)
    comprobar("referir con cama ocupada: REFERIDO, cama 6 EN LIMPIEZA con su solicitud (RN-07)",
              id_sol_ref and estado_ep(ep_otra) == "REFERIDO" and estado_cama(6) == "EN LIMPIEZA"
              and valor("SELECT id_cama FROM solicitud_limpieza WHERE id_solicitud = %s", (id_sol_ref,)) == 6)
    comprobar("los cierres quedan en la bitácora (UPDATE episodio_emergencia)",
              all(bitacora("episodio_emergencia", "UPDATE", e) == 1 for e in (ep_nn.id_episodio, ep_ana.id_episodio)))
    comprobar("un episodio referido no se vuelve a cerrar", lanza(ReglaNegocioError, camas.registrar_fuga, ep_otra))
    ind = reportes.indicadores(hoy - timedelta(days=1), hoy)
    estancia_altas = valor("SELECT AVG(TIMESTAMPDIFF(MINUTE, fecha_ingreso, fecha_alta)) FROM episodio_emergencia "
                           "WHERE estado_registro = TRUE AND id_estado_ep = 4")
    comprobar(f"la estancia promedio ({ind.estancia_min}) solo cuenta las altas médicas",
              ind.estancia_min == round(float(estancia_altas), 1))

    # ------------------------------------------------------------------ Fuera de servicio
    print("\n--- Fuera de servicio")
    comprobar("una cama con limpieza pendiente no sale de servicio",
              "limpieza pendiente" in str(lanza(ReglaNegocioError, camas.poner_fuera_de_servicio, 6, "Colchón roto")))
    con_paciente = valor("SELECT id_cama FROM asignacion_cama WHERE fecha_liberacion IS NULL AND estado_registro = TRUE "
                         "ORDER BY id_cama LIMIT 1")
    comprobar(f"una cama con paciente (cama {con_paciente}) no sale de servicio",
              "paciente asignado" in str(lanza(ReglaNegocioError, camas.poner_fuera_de_servicio, con_paciente, "Falla")))
    camas.poner_fuera_de_servicio(3, "Monitor de signos con falla")
    comprobar("poner_fuera_de_servicio: cama 3 FUERA DE SERVICIO, motivo en la bitácora, ya no figura disponible",
              estado_cama(3) == "FUERA DE SERVICIO"
              and "Monitor de signos" in valor("SELECT CAST(detalles_json AS CHAR) FROM bitacora_auditoria WHERE "
                                               "tabla_afectada = 'cama' AND id_registro_afectado = 3 "
                                               "ORDER BY id_bitacora DESC LIMIT 1")
              and 3 not in [c.id_cama for c in CamaDAO.listar_disponibles()])
    comprobar("no se saca dos veces", lanza(ReglaNegocioError, camas.poner_fuera_de_servicio, 3, "Otra vez"))
    camas.volver_a_servicio(3)
    comprobar("volver_a_servicio: cama 3 DISPONIBLE", estado_cama(3) == "DISPONIBLE")
    comprobar("una cama disponible no 'vuelve' a servicio", lanza(CamaEstadoInvalidoError, camas.volver_a_servicio, 3))

    # ------------------------------------------------------------------ Editar, baja y reactivación
    print("\n--- Editar, dar de baja y reactivar pacientes")
    pacientes_admin = PacienteController(admin)
    editado = pacientes.actualizar_datos(nuevo.id_paciente, "Ana", "Torres Vega de Ríos", date(1990, 4, 2), "F", 1)
    comprobar("actualizar_datos guarda el cambio y audita solo los nombres de los campos",
              editado.apellidos == "Torres Vega de Ríos"
              and valor("SELECT apellidos FROM paciente WHERE id_paciente = %s", (nuevo.id_paciente,)) == "Torres Vega de Ríos"
              and "Torres" not in valor("SELECT CAST(detalles_json AS CHAR) FROM bitacora_auditoria WHERE "
                                        "tabla_afectada = 'paciente' AND accion = 'UPDATE' AND id_registro_afectado = %s",
                                        (nuevo.id_paciente,)))
    comprobar("un enfermero no da de baja pacientes", lanza(UsuarioSinPermisoError, pacientes.dar_de_baja, nuevo.id_paciente))
    comprobar("no se da de baja a Rosa, que sigue en emergencia",
              "episodio abierto" in str(lanza(ReglaNegocioError, pacientes_admin.dar_de_baja, 1)))
    pacientes_admin.dar_de_baja(nuevo.id_paciente)  # su episodio terminó en fuga
    comprobar("dar_de_baja: estado_registro = FALSE y ANULAR en la bitácora",
              valor("SELECT estado_registro FROM paciente WHERE id_paciente = %s", (nuevo.id_paciente,)) == 0
              and bitacora("paciente", "ANULAR", nuevo.id_paciente) == 1)
    comprobar("un paciente dado de baja no se edita",
              lanza(ReglaNegocioError, pacientes.actualizar_datos, nuevo.id_paciente, "Ana", "Torres", date(1990, 4, 2), "F", 1))
    comprobar("registrar su documento otra vez pide la reactivación",
              "reactivación" in str(lanza(ReglaNegocioError, pacientes.registrar, "DNI", "72345678", "Ana", "Torres",
                                          date(1990, 4, 2), "F", 2)))
    comprobar("reactivar: vuelve a estar activo, con REACTIVAR en la bitácora",
              pacientes_admin.reactivar(nuevo.id_paciente).activo
              and valor("SELECT estado_registro FROM paciente WHERE id_paciente = %s", (nuevo.id_paciente,)) == 1
              and bitacora("paciente", "REACTIVAR", nuevo.id_paciente) == 1)
    comprobar("un NN fusionado no se reactiva",
              "sin identificar" in str(lanza(ReglaNegocioError, pacientes_admin.reactivar, nn2.id_paciente)))

    # ------------------------------------------------------------------ Administración de cuentas
    print("\n--- Cuentas de usuario y login real (admin_controller + auth_controller)")
    cuentas, auth = AdminController(admin), AuthController()
    CLAVE, CLAVE_NUEVA = "Guardia2026x", "Turno2026noche"
    comprobar("un jefe de guardia no administra cuentas", lanza(UsuarioSinPermisoError, AdminController(jefe).listar_cuentas))
    sin_cuenta = [e["id_empleado"] for e in cuentas.listar_empleados_sin_cuenta()]
    comprobar(f"empleados sin cuenta: solo el 5, activo ({sin_cuenta})", sin_cuenta == [5])
    comprobar("una clave débil no se acepta", lanza(ValueError, cuentas.crear_cuenta, 5, Rol.MEDICO, "12345678"))
    nueva = cuentas.crear_cuenta(5, Rol.MEDICO, CLAVE)
    comprobar("crear_cuenta: la BD guarda un hash bcrypt, no la clave",
              nueva.rol is Rol.MEDICO and nueva.activo
              and valor("SELECT hash_clave FROM usuario WHERE id_usuario = %s", (nueva.id_usuario,)).startswith("$2b$12$"))
    comprobar("ni la clave ni el hash llegan a la bitácora",
              valor("SELECT COUNT(*) FROM bitacora_auditoria WHERE tabla_afectada = 'usuario' AND "
                    "(CAST(detalles_json AS CHAR) LIKE %s OR CAST(detalles_json AS CHAR) LIKE %s)",
                    ("%" + CLAVE + "%", "%$2b$%")) == 0)
    comprobar("una segunda cuenta para el mismo empleado se rechaza (UNIQUE)",
              lanza(RegistroDuplicadoError, cuentas.crear_cuenta, 5, Rol.MEDICO, CLAVE))
    sesion = auth.iniciar_sesion("DNI", "55555555", CLAVE)
    comprobar("login real con la cuenta nueva: sesión de Médico con sus permisos",
              sesion.nombre_rol == "Médico de Emergencia" and sesion.puede("gestion_camas") and not sesion.puede("reportes"))
    cuentas.cambiar_rol(nueva.id_usuario, Rol.JEFE_GUARDIA)
    comprobar("cambiar_rol: el siguiente login ya tiene el rol nuevo",
              auth.iniciar_sesion("DNI", "55555555", CLAVE).nombre_rol == "Jefe de Guardia")
    cuentas.desactivar(nueva.id_usuario)
    comprobar("una cuenta desactivada no inicia sesión",
              lanza(AutenticacionError, auth.iniciar_sesion, "DNI", "55555555", CLAVE))
    cuentas.activar(nueva.id_usuario)
    comprobar("al reactivarla vuelve a entrar", auth.iniciar_sesion("DNI", "55555555", CLAVE).activa)
    for _ in range(5):
        lanza(AutenticacionError, auth.iniciar_sesion, "DNI", "55555555", "ClaveEquivocada1")
    comprobar("5 intentos fallidos bloquean la cuenta, incluso con la clave correcta",
              UsuarioDAO.buscar_cuenta(nueva.id_usuario).bloqueada
              and lanza(AutenticacionError, auth.iniciar_sesion, "DNI", "55555555", CLAVE))
    cuentas.desbloquear(nueva.id_usuario)
    comprobar("desbloquear: entra sin esperar los 15 minutos", auth.iniciar_sesion("DNI", "55555555", CLAVE).activa)
    cuentas.restablecer_clave(nueva.id_usuario, CLAVE_NUEVA)
    comprobar("restablecer_clave: la clave anterior deja de servir y la nueva funciona",
              lanza(AutenticacionError, auth.iniciar_sesion, "DNI", "55555555", CLAVE)
              and auth.iniciar_sesion("DNI", "55555555", CLAVE_NUEVA).activa)
    comprobar("el administrador no puede desactivarse a sí mismo",
              "otro administrador" in str(lanza(ReglaNegocioError, cuentas.desactivar, 1)))
    registros = cuentas.bitacora(hoy, hoy, tabla="usuario")
    comprobar(f"la bitácora del día muestra las {len(registros)} operaciones sobre cuentas, la más reciente primero",
              len(registros) == 6 and registros[0]["detalles"] == {"clave_restablecida": True})
    auth.cerrar_sesion()

    lector.close()
    ConexionBD().cerrar_conexion()


if __name__ == "__main__":
    raise SystemExit(main())
