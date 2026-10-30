"""
Inicio de sesión: la marca, el documento, la contraseña y «Ingresar», en una tarjeta centrada (docs/diseno/BRIEF.md §1).

La vista no valida nada: el documento lo valida el DAO (DocumentoIdentidad) y la clave, bcrypt. Si el login falla,
AuthController lanza AutenticacionError con un mensaje genérico, que no dice si el documento existe ni si la cuenta
está bloqueada.
"""
import customtkinter as ctk

from controllers.auth_controller import AuthController
from models.excepciones import ConexionBDError, SigtacError
from views import tema
from views.componentes import BotonPrimario, CamposDocumento, Marca, campo_texto, etiqueta_campo, mostrar_error

TEXTO_INGRESAR = "Ingresar"
TEXTO_VERIFICANDO = "Verificando…"
AVISO_PROTOTIPO = "Prototipo académico — no validado clínicamente"


class LoginView(ctk.CTkFrame):
    """
    Pantalla de inicio de sesión. No sabe qué se muestra después: al iniciar sesión llama a `al_iniciar(sesion)`
    y main.py decide (así esta vista no depende de la ventana principal).
    """

    def __init__(self, padre, auth: AuthController, al_iniciar):
        super().__init__(padre, fg_color=tema.COLOR_FONDO, corner_radius=0)
        self._auth = auth
        self._al_iniciar = al_iniciar
        self._verificando = False

        # La tarjeta toma el ancho de su contenido (el documento) y queda en el centro de la ventana
        tarjeta = ctk.CTkFrame(self, fg_color=tema.COLOR_SUPERFICIE, corner_radius=tema.RADIO_TARJETA, border_width=1,
                               border_color=tema.COLOR_BORDE)
        tarjeta.place(relx=0.5, rely=0.5, anchor="center")
        contenido = ctk.CTkFrame(tarjeta, fg_color="transparent")
        contenido.pack(padx=tema.ESPACIO_2, pady=tema.ESPACIO_2)

        Marca(contenido).pack(anchor="w", pady=(0, tema.ESPACIO_2))

        self._documento = CamposDocumento(contenido)
        self._documento.pack(fill="x", pady=(0, tema.ESPACIO_2))

        etiqueta_campo(contenido, "Contraseña").pack(anchor="w", pady=(0, tema.ESPACIO_MINIMO))
        self._clave = campo_texto(contenido, show="•")
        self._clave.pack(fill="x")

        self._boton = BotonPrimario(contenido, TEXTO_INGRESAR, self.ingresar)
        self._boton.pack(fill="x", pady=tema.ESPACIO_2)

        ctk.CTkLabel(contenido, text=AVISO_PROTOTIPO, font=tema.fuente("pequena"),
                     text_color=tema.COLOR_TEXTO_SECUNDARIO).pack()

        # Enter ingresa desde cualquiera de los dos campos que se escriben
        for campo in (self._documento.campo_numero, self._clave):
            campo.bind("<Return>", self.ingresar, add="+")
        self.after_idle(self._documento.enfocar)

    def ingresar(self, _evento=None):
        if self._verificando:  # un segundo Enter mientras bcrypt verifica no inicia otro intento
            return
        tipo, numero = self._documento.valores()
        self._ocupado(True)
        try:
            sesion = self._auth.iniciar_sesion(tipo.value, numero, self._clave.get())
        except ConexionBDError as error:
            # No es un problema de los datos: se conservan para reintentar
            self._ocupado(False)
            mostrar_error(self, error)
            return
        except (SigtacError, ValueError) as error:
            self._ocupado(False)
            mostrar_error(self, error)
            self._clave.delete(0, "end")
            self._clave.focus_set()
            return
        self._al_iniciar(sesion)

    def _ocupado(self, ocupado: bool):
        """Mientras se verifica (bcrypt tarda ~0.3 s) el botón se deshabilita y dice que espera."""
        if not ocupado:
            # Durante la verificación Tk no atiende el teclado: un Enter pulsado entonces quedó en cola. Se atiende
            # ahora, todavía «ocupado», para que no inicie otro intento con la contraseña ya borrada.
            self.update()
        self._verificando = ocupado
        self._boton.configure(state="disabled" if ocupado else "normal",
                              text=TEXTO_VERIFICANDO if ocupado else TEXTO_INGRESAR)
        if ocupado:
            self.update_idletasks()  # que el cambio se vea antes de la espera
