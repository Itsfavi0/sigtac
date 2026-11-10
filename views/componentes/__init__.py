"""Piezas de interfaz compartidas por las pantallas: una sola forma de hacer cada cosa."""
from views.componentes.botones import BotonPrimario, BotonSecundario
from views.componentes.campos import campo_texto, casilla, etiqueta_campo, lista_opciones
from views.componentes.cubierta import Cubierta
from views.componentes.desplazable import Desplazable
from views.componentes.documento import CamposDocumento
from views.componentes.errores import confirmar, mostrar_error, mostrar_info, pedir_ruta_pdf
from views.componentes.foco import marcar_error, marcar_foco
from views.componentes.marca import Marca
from views.componentes.matriz import MatrizCamas
from views.componentes.nivel import InsigniaNivel, texto_nivel
from views.componentes.paciente import CamposPaciente, FichaPaciente
from views.componentes.periodo import CamposPeriodo
from views.componentes.seleccion import ListaSeleccion
from views.componentes.selector import Selector
from views.componentes.tabla import TablaDatos
from views.componentes.tarjetas import Tarjeta, TarjetaCama, TarjetaKPI

__all__ = ["BotonPrimario", "BotonSecundario", "CamposDocumento", "CamposPaciente", "CamposPeriodo", "Cubierta",
           "Desplazable",
           "FichaPaciente", "InsigniaNivel", "ListaSeleccion", "Marca", "MatrizCamas", "Selector", "TablaDatos",
           "Tarjeta", "TarjetaCama", "TarjetaKPI", "campo_texto", "casilla", "confirmar", "etiqueta_campo",
           "lista_opciones", "marcar_error", "marcar_foco", "mostrar_error", "mostrar_info", "pedir_ruta_pdf",
           "texto_nivel"]
