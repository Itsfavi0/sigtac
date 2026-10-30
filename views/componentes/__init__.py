"""Piezas de interfaz compartidas por las pantallas: una sola forma de hacer cada cosa."""
from views.componentes.botones import BotonPrimario, BotonSecundario
from views.componentes.campos import campo_texto, casilla, etiqueta_campo, lista_opciones
from views.componentes.documento import CamposDocumento
from views.componentes.errores import confirmar, mostrar_error, mostrar_info
from views.componentes.foco import marcar_error, marcar_foco
from views.componentes.marca import Marca
from views.componentes.matriz import MatrizCamas
from views.componentes.nivel import InsigniaNivel, texto_nivel
from views.componentes.selector import Selector
from views.componentes.tabla import TablaDatos
from views.componentes.tarjetas import Tarjeta, TarjetaCama, TarjetaKPI

__all__ = ["BotonPrimario", "BotonSecundario", "CamposDocumento", "InsigniaNivel", "Marca", "MatrizCamas", "Selector",
           "TablaDatos", "Tarjeta", "TarjetaCama", "TarjetaKPI", "campo_texto", "casilla", "confirmar",
           "etiqueta_campo", "lista_opciones", "marcar_error", "marcar_foco", "mostrar_error", "mostrar_info",
           "texto_nivel"]
