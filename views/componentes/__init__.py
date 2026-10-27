"""Piezas de interfaz compartidas por las pantallas: una sola forma de hacer cada cosa."""
from views.componentes.documento import CamposDocumento
from views.componentes.errores import confirmar, mostrar_error, mostrar_info
from views.componentes.foco import marcar_error, marcar_foco
from views.componentes.matriz import MatrizCamas
from views.componentes.nivel import InsigniaNivel, texto_nivel
from views.componentes.tabla import TablaDatos
from views.componentes.tarjetas import TarjetaCama, TarjetaKPI

__all__ = ["CamposDocumento", "InsigniaNivel", "MatrizCamas", "TablaDatos", "TarjetaCama", "TarjetaKPI",
           "confirmar", "marcar_error", "marcar_foco", "mostrar_error", "mostrar_info", "texto_nivel"]
