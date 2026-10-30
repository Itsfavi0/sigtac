"""
Datos de un paciente: los campos para escribirlos (registrar, editar, identificar) y su ficha para leerlos. Triaje y
pacientes los muestran igual.
"""
import customtkinter as ctk

from views import formato, tema
from views.componentes.campos import campo_en_rejilla, leer_campo, leer_opcion, limpiar_al_corregir, lista_en_rejilla
from views.componentes.documento import ETIQUETAS
from views.componentes.foco import marcar_error

# Lo que ve el usuario → el código del modelo (Paciente.SEXOS_VALIDOS)
SEXOS = {"Mujer": "F", "Varón": "M"}


class CamposPaciente(ctk.CTkFrame):
    """
    Nombres, apellidos y fecha de nacimiento; con `con_sexo_y_seguro`, también el sexo y el seguro (al identificar a
    un NN esos dos ya se conocen). No valida los nombres ni la fecha: eso lo hace el modelo. Solo lee lo escrito
    (la fecha como dd/mm/aaaa, las opciones elegidas) y marca el campo que no se puede leer.
    """

    def __init__(self, padre, con_sexo_y_seguro: bool = True):
        super().__init__(padre, fg_color="transparent")
        self.con_sexo_y_seguro = con_sexo_y_seguro
        self._seguros = {}  # nombre → id_seguro
        self.nombres = campo_en_rejilla(self, "Nombres", 0, 0)
        self.apellidos = campo_en_rejilla(self, "Apellidos", 0, 1)
        self.fecha_nac = campo_en_rejilla(self, "Fecha de nacimiento", 1, 0, "dd/mm/aaaa")
        self.sexo = self.seguro = None
        if con_sexo_y_seguro:
            self.sexo = lista_en_rejilla(self, "Sexo", list(SEXOS), 1, 1)
            self.seguro = lista_en_rejilla(self, "Seguro", [], 2, 0)
        self.grid_columnconfigure((0, 1), weight=1, uniform="paciente")
        limpiar_al_corregir(*self._marcables())

    @property
    def entradas(self) -> tuple[ctk.CTkEntry, ...]:
        """Los campos que se escriben, para que la pantalla les asocie Enter."""
        return self.nombres, self.apellidos, self.fecha_nac

    def cargar_seguros(self, seguros: list[dict]):
        """El catálogo de PacienteController.listar_seguros(): [{"id_seguro": 1, "nombre_seguro": "EsSalud"}, ...]."""
        self._seguros = {s["nombre_seguro"]: s["id_seguro"] for s in seguros}
        if self.seguro is not None:
            self.seguro.configure(values=list(self._seguros))

    def fijar(self, paciente):
        """Escribe los datos de un paciente (para editarlos)."""
        self.limpiar()
        self.nombres.insert(0, paciente.nombres)
        self.apellidos.insert(0, paciente.apellidos)
        self.fecha_nac.insert(0, formato.fecha_numerica(paciente.fecha_nac))
        if self.con_sexo_y_seguro:
            self.sexo.set(next(texto for texto, codigo in SEXOS.items() if codigo == paciente.sexo))
            nombre = next((n for n, i in self._seguros.items() if i == paciente.id_seguro), "")
            self.seguro.set(nombre)

    def valores(self) -> dict:
        """
        Los datos listos para el controlador: nombres, apellidos, fecha_nac (date) y, si los tiene, sexo ('M'/'F') e
        id_seguro. Un dato que no se puede leer marca su campo y lanza ValueError con lo que hay que corregir.
        """
        datos = {
            "nombres": self.nombres.get(),
            "apellidos": self.apellidos.get(),
            "fecha_nac": leer_campo(self.fecha_nac, lambda texto: formato.leer_fecha(texto, "La fecha de nacimiento")),
        }
        if self.con_sexo_y_seguro:
            datos["sexo"] = leer_opcion(self.sexo, SEXOS, "Elija el sexo del paciente.")
            datos["id_seguro"] = leer_opcion(self.seguro, self._seguros, "Elija el seguro del paciente.")
        return datos

    def limpiar(self):
        for campo in self.entradas:
            campo.delete(0, "end")
            campo._activate_placeholder()  # CustomTkinter solo lo vuelve a mostrar al perder el foco
        if self.con_sexo_y_seguro:
            self.sexo.set("")
            self.seguro.set("")
        self.limpiar_errores()

    def limpiar_errores(self):
        for campo in self._marcables():
            marcar_error(campo, False)

    def enfocar(self):
        self.nombres.focus_set()

    def _marcables(self) -> list:
        """Los campos que valores() puede marcar: la fecha y, si están, el sexo y el seguro."""
        return [c for c in (self.fecha_nac, self.sexo, self.seguro) if c is not None]


class FichaPaciente(ctk.CTkFrame):
    """
    El paciente encontrado: su nombre completo y una línea con edad, sexo, seguro y si está dado de baja. La
    ficha ampliada (pacientes) agrega el documento y la fecha de nacimiento.
    """

    def __init__(self, padre, ampliada: bool = False):
        super().__init__(padre, fg_color="transparent")
        self._ampliada = ampliada
        self._nombre = ctk.CTkLabel(self, text="", font=tema.fuente("fuerte"), text_color=tema.COLOR_TEXTO, anchor="w")
        self._nombre.pack(anchor="w")
        self._documento = ctk.CTkLabel(self, text="", font=tema.fuente("normal"), text_color=tema.COLOR_TEXTO,
                                       anchor="w")
        if ampliada:
            self._documento.pack(anchor="w")
        self._datos = ctk.CTkLabel(self, text="", font=tema.fuente("pequena"), text_color=tema.COLOR_TEXTO_SECUNDARIO,
                                   anchor="w")
        self._datos.pack(anchor="w")

    def mostrar(self, paciente):
        datos = [f"{paciente.calcular_edad()} años", formato.SEXO[paciente.sexo]]
        if paciente.nombre_seguro:
            datos.append(paciente.nombre_seguro)
        if not paciente.activo:
            datos.append("Dado de baja")
        self._nombre.configure(text=f"{paciente.nombres} {paciente.apellidos}")
        self._datos.configure(text=" · ".join(datos))
        documento = paciente.documento
        texto = formato.SIN_DOCUMENTO if documento is None else f"{ETIQUETAS[documento.tipo]} {documento.numero}"
        self._documento.configure(text=f"{texto} · nació el {formato.fecha_numerica(paciente.fecha_nac)}")

    @property
    def nombre(self) -> str:
        return self._nombre.cget("text")

    @property
    def datos(self) -> str:
        return self._datos.cget("text")

    @property
    def documento(self) -> str:
        return self._documento.cget("text")
