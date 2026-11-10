from unittest.mock import MagicMock

import customtkinter as ctk
import pytest

from controllers.auth_controller import AuthController
from main import Aplicacion


def crear(raiz) -> Aplicacion:
    return Aplicacion(raiz, MagicMock(spec=AuthController))


def test_cambiar_construye_la_nueva_y_despues_quita_la_anterior(raiz_tk):
    aplicacion = crear(raiz_tk)
    anterior = ctk.CTkFrame(raiz_tk)
    aplicacion._cambiar(lambda: anterior)
    vivas_al_construir = []

    def construir():
        vivas_al_construir.append(anterior.winfo_exists())
        return ctk.CTkFrame(raiz_tk)

    aplicacion._cambiar(construir)
    assert vivas_al_construir == [True]  # mientras se construye, la anterior sigue
    assert not anterior.winfo_exists()
    assert aplicacion._pantalla.winfo_manager() == "pack"


def test_si_la_nueva_no_se_puede_construir_la_anterior_sigue(raiz_tk):
    aplicacion = crear(raiz_tk)
    anterior = ctk.CTkFrame(raiz_tk)
    aplicacion._cambiar(lambda: anterior)

    def falla():
        raise ValueError("no se pudo")

    with pytest.raises(ValueError):
        aplicacion._cambiar(falla)
    assert aplicacion._pantalla is anterior and anterior.winfo_manager() == "pack"


def test_el_cambio_se_hace_bajo_la_cubierta_de_toda_la_ventana(raiz_tk, monkeypatch):
    aplicacion = crear(raiz_tk)
    assert aplicacion._cubierta._area is raiz_tk
    anterior = ctk.CTkFrame(raiz_tk)
    aplicacion._cambiar(lambda: anterior)
    nueva = ctk.CTkFrame(raiz_tk)
    vistas = []

    def cambiar(cambio):
        vistas.append(aplicacion._pantalla)  # al entrar: aún la anterior
        cambio()
        vistas.append(aplicacion._pantalla)

    monkeypatch.setattr(aplicacion._cubierta, "cambiar", cambiar)
    aplicacion._cambiar(lambda: nueva)
    assert vistas == [anterior, nueva]


def test_salir_cierra_la_sesion_quita_la_cubierta_y_cierra_la_ventana():
    ventana = MagicMock()
    aplicacion = Aplicacion(ventana, MagicMock(spec=AuthController))
    aplicacion._cubierta = MagicMock()
    aplicacion.salir()
    aplicacion._auth.cerrar_sesion.assert_called_once()
    aplicacion._cubierta.quitar.assert_called_once()
    ventana.destroy.assert_called_once()
