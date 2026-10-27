"""
Punto de entrada de SIGTAC. Se ejecuta con el .venv activado:

    python main.py

Necesita el .env con las credenciales de la BD (ver .env.example). Si faltan o MySQL no responde, el
error se muestra al intentar iniciar sesión.
"""
import customtkinter as ctk

from controllers.auth_controller import AuthController, Sesion
from utils.logging_config import configurar_logging
from views import tema
from views.app_principal import AppPrincipal
from views.login_view import LoginView


class Aplicacion:
    """
    Ventana única de la aplicación: muestra el login o la pantalla principal y cambia entre ellos.

    Las pantallas no se crean entre sí: reciben un callback (al_iniciar, al_cerrar) y es esta clase la que
    decide qué mostrar después. Así LoginView no depende de AppPrincipal ni al revés.
    """

    def __init__(self, ventana: ctk.CTk, auth: AuthController):
        self._ventana = ventana
        self._auth = auth
        self._pantalla = None

    def mostrar_login(self):
        self._ventana.title(tema.TITULO_VENTANA)
        self._cambiar(LoginView(self._ventana, self._auth, al_iniciar=self.mostrar_principal))

    def mostrar_principal(self, sesion: Sesion):
        self._cambiar(AppPrincipal(self._ventana, self._auth, sesion, al_cerrar=self.mostrar_login))

    def salir(self):
        """Al cerrar la ventana también se cierra la sesión."""
        self._auth.cerrar_sesion()
        self._ventana.destroy()

    def _cambiar(self, pantalla):
        if self._pantalla is not None:
            self._pantalla.destroy()
        self._pantalla = pantalla
        pantalla.pack(fill="both", expand=True)


def main():
    configurar_logging()
    tema.aplicar()
    ventana = ctk.CTk()
    ventana.minsize(*tema.TAMANO_MINIMO)
    aplicacion = Aplicacion(ventana, AuthController())
    ventana.protocol("WM_DELETE_WINDOW", aplicacion.salir)
    aplicacion.mostrar_login()
    ventana.mainloop()


if __name__ == "__main__":
    main()
