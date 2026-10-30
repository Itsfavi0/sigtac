from unittest.mock import MagicMock

import customtkinter as ctk
import pytest

from controllers.auth_controller import AuthController
from models.documento import TipoDocumento
from models.excepciones import AutenticacionError, ConexionBDError
from views import login_view
from views.componentes import Marca
from views.login_view import AVISO_PROTOTIPO, TEXTO_INGRESAR, TEXTO_VERIFICANDO, LoginView

CLAVE = "Clave#Prueba1"


@pytest.fixture
def errores(monkeypatch):
    """Reemplaza mostrar_error (un diálogo bloquearía la prueba) y anota los errores mostrados."""
    mostrados = []
    monkeypatch.setattr(login_view, "mostrar_error", lambda ventana, error: mostrados.append(error))
    return mostrados


@pytest.fixture
def pantalla(raiz_tk):
    """El login con un AuthController falso y el callback al_iniciar espiado."""
    auth = MagicMock(spec=AuthController)
    al_iniciar = MagicMock()
    vista = LoginView(raiz_tk, auth, al_iniciar)
    return vista, auth, al_iniciar


def escribir(vista, numero="12345678", clave=CLAVE):
    vista._documento.fijar(TipoDocumento.DNI, numero)
    vista._clave.delete(0, "end")
    vista._clave.insert(0, clave)


def todos_los_textos(widget) -> list[str]:
    textos = []
    for hijo in widget.winfo_children():
        if isinstance(hijo, (ctk.CTkLabel, ctk.CTkButton)):
            textos.append(hijo.cget("text"))
        textos.extend(todos_los_textos(hijo))
    return textos


def test_muestra_la_marca_los_campos_el_boton_y_el_aviso(pantalla):
    vista, _, _ = pantalla
    textos = todos_los_textos(vista)
    for texto in ("SIGTAC", "Documento de identidad", "Contraseña", TEXTO_INGRESAR, AVISO_PROTOTIPO):
        assert texto in textos
    assert any(isinstance(w, Marca) for w in vista.winfo_children()[0].winfo_children()[0].winfo_children())


def test_la_contrasena_no_se_ve(pantalla):
    vista, _, _ = pantalla
    assert vista._clave.cget("show") == "•"


def test_login_correcto_entrega_la_sesion(pantalla, errores):
    vista, auth, al_iniciar = pantalla
    sesion = object()
    auth.iniciar_sesion.return_value = sesion
    escribir(vista)
    vista.ingresar()
    auth.iniciar_sesion.assert_called_once_with("DNI", "12345678", CLAVE)  # el código del tipo, no la etiqueta
    al_iniciar.assert_called_once_with(sesion)
    assert errores == []


def test_login_fallido_muestra_el_mensaje_y_borra_la_contrasena(pantalla, errores):
    vista, auth, al_iniciar = pantalla
    error = AutenticacionError(AuthController.MENSAJE_FALLO)
    auth.iniciar_sesion.side_effect = error
    escribir(vista)
    vista.ingresar()
    assert errores == [error]
    assert vista._clave.get() == ""                              # se vuelve a escribir la clave
    assert vista._documento.valores() == (TipoDocumento.DNI, "12345678")  # el documento se conserva
    al_iniciar.assert_not_called()
    assert vista._boton.cget("state") == "normal" and vista._boton.cget("text") == TEXTO_INGRESAR


def test_sin_conexion_muestra_su_mensaje_y_conserva_la_contrasena(pantalla, errores):
    vista, auth, al_iniciar = pantalla
    error = ConexionBDError("No se pudo conectar con la base de datos.")
    auth.iniciar_sesion.side_effect = error
    escribir(vista)
    vista.ingresar()
    assert errores == [error]
    assert vista._clave.get() == CLAVE  # no es un error de los datos: se puede reintentar tal cual
    al_iniciar.assert_not_called()
    assert vista._boton.cget("state") == "normal"


def test_un_documento_invalido_se_muestra_como_error(pantalla, errores):
    vista, auth, _ = pantalla
    auth.iniciar_sesion.side_effect = ValueError("El DNI debe tener 8 dígitos.")
    escribir(vista, numero="123")
    vista.ingresar()
    assert [str(e) for e in errores] == ["El DNI debe tener 8 dígitos."]


def test_mientras_verifica_el_boton_queda_deshabilitado(pantalla, errores):
    vista, auth, _ = pantalla
    estado_durante = {}

    def verificar(*_):
        estado_durante.update(estado=vista._boton.cget("state"), texto=vista._boton.cget("text"))
        raise AutenticacionError(AuthController.MENSAJE_FALLO)

    auth.iniciar_sesion.side_effect = verificar
    escribir(vista)
    vista.ingresar()
    assert estado_durante == {"estado": "disabled", "texto": TEXTO_VERIFICANDO}


def test_no_inicia_otro_intento_mientras_verifica(pantalla):
    vista, auth, _ = pantalla
    vista._verificando = True
    vista.ingresar()
    auth.iniciar_sesion.assert_not_called()


def test_enter_ingresa_desde_los_dos_campos(pantalla):
    vista, _, _ = pantalla
    for campo in (vista._documento.campo_numero, vista._clave):
        assert campo._entry.bind("<Return>")  # tiene una acción asociada
