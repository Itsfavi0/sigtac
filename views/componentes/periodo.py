"""
Período de días completos: los atajos (Hoy / Últimos 7 días / Este mes) y las fechas «Desde» y «Hasta» (dd/mm/aaaa).
Reportes y la bitácora de Administración lo piden igual.

- Un atajo rellena las fechas y avisa a la pantalla, que consulta. Pulsar el marcado lo vuelve a pedir (p. ej. «Hoy» en
  una pantalla abierta desde ayer).
- El atajo marcado sigue a lo escrito: ninguno si las fechas no corresponden a uno. El marcado va primero: el día 1,
  «Hoy» y «Este mes» son el mismo período, y se conserva el que eligió el usuario.
- Una fecha mal escrita, o un período que el controlador rechaza (rechazar()), queda en rojo hasta que lo escrito
  cambia: soltar el Enter que lo envió no lo corrige (como el motivo en Gestión de camas).

No valida el período (que la inicial no pase a la final, el rango de años): eso lo hace el controlador.
"""
from collections.abc import Callable
from datetime import date, timedelta

import customtkinter as ctk

from views import formato, tema
from views.componentes.campos import campo_en_rejilla, leer_campo, leer_todos
from views.componentes.foco import marcar_error
from views.componentes.selector import Selector

ATAJOS = (("hoy", "Hoy"), ("semana", "Últimos 7 días"), ("mes", "Este mes"))
FORMATO = "dd/mm/aaaa"


def periodo_de(atajo: str, hoy: date) -> tuple[date, date]:
    """Los días (desde, hasta) de un atajo, ambos incluidos: «semana» son los últimos 7 días contando hoy."""
    if atajo == "hoy":
        return hoy, hoy
    if atajo == "semana":
        return hoy - timedelta(days=6), hoy
    if atajo == "mes":
        return hoy.replace(day=1), hoy
    raise ValueError(f"Atajo de período desconocido: {atajo!r}.")


def texto_periodo(desde: date, hasta: date) -> str:
    """«Del 01/10/2026 al 15/10/2026»; un solo día, «El 15/10/2026»."""
    if desde == hasta:
        return f"El {formato.fecha_numerica(desde)}"
    return f"Del {formato.fecha_numerica(desde)} al {formato.fecha_numerica(hasta)}"


class CamposPeriodo(ctk.CTkFrame):
    """
    Las fechas van en una rejilla de `columnas` (las dos primeras celdas); la pantalla puede poner sus propios campos
    en las demás (`rejilla`, p. ej. los filtros de la bitácora). Los atajos van en `cabecera` (la de una Tarjeta, a la
    derecha) o, sin ella, en su propia fila encima de las fechas.

    `al_elegir_atajo()` se llama después de rellenar las fechas con el atajo elegido. Empieza con el atajo `inicial`
    marcado y sus fechas escritas, sin avisar.
    """

    def __init__(self, padre, al_elegir_atajo: Callable[[], None], hoy: Callable[[], date] = date.today,
                 cabecera=None, inicial: str = "mes", columnas: int = 3):
        super().__init__(padre, fg_color="transparent")
        self._al_elegir_atajo, self._hoy = al_elegir_atajo, hoy
        self._rechazado = None  # (desde, hasta) tal como se rechazaron: el rojo sigue hasta que lo escrito cambie

        self.atajos = Selector(self if cabecera is None else cabecera, ATAJOS, self._atajo_elegido, repetir=True)
        if cabecera is None:
            self.atajos.pack(anchor="w", pady=(0, tema.ESPACIO_2))
        else:
            self.atajos.pack(side="right")
        self.rejilla = ctk.CTkFrame(self, fg_color="transparent")
        self.rejilla.pack(fill="x")
        self.rejilla.grid_columnconfigure(tuple(range(columnas)), weight=1, uniform="periodo")
        self.desde = campo_en_rejilla(self.rejilla, "Desde", 0, 0, FORMATO)
        self.hasta = campo_en_rejilla(self.rejilla, "Hasta", 0, 1, FORMATO)
        for campo in self.entradas:
            campo.bind("<KeyRelease>", lambda _e: self.fechas_editadas(), add="+")

        self.atajos.elegir(inicial, avisar=False)
        self.fijar(*periodo_de(inicial, self._hoy()))

    @property
    def entradas(self) -> tuple[ctk.CTkEntry, ctk.CTkEntry]:
        """Desde y Hasta, para que la pantalla les asocie Enter (su acción principal)."""
        return self.desde, self.hasta

    def fijar(self, desde: date, hasta: date):
        """Escribe las dos fechas y quita las marcas de error. No cambia el atajo marcado."""
        for campo, dia in ((self.desde, desde), (self.hasta, hasta)):
            campo.delete(0, "end")
            campo.insert(0, formato.fecha_numerica(dia))
            marcar_error(campo, False)
        self._rechazado = None

    def leer(self) -> tuple[date, date]:
        """
        Las dos fechas escritas. Las que no se pueden leer quedan marcadas (las dos, si fallan las dos) y el ValueError
        de la primera sigue a quien llamó.
        """
        try:
            fechas = leer_todos({
                "desde": lambda: leer_campo(self.desde, lambda texto: formato.leer_fecha(texto, "La fecha inicial")),
                "hasta": lambda: leer_campo(self.hasta, lambda texto: formato.leer_fecha(texto, "La fecha final")),
            })
        except ValueError:
            self._rechazado = self._escrito()
            raise
        return fechas["desde"], fechas["hasta"]

    def rechazar(self):
        """El controlador rechazó el período (p. ej. la inicial después de la final): no se sabe cuál, se marcan ambas."""
        marcar_error(self.desde)
        marcar_error(self.hasta)
        self._rechazado = self._escrito()

    def fechas_editadas(self):
        """Al escribir en una fecha: un período rechazado pierde el rojo si cambió, y el atajo sigue a lo escrito."""
        if self._rechazado is not None and self._escrito() != self._rechazado:
            self._rechazado = None
            marcar_error(self.desde, False)
            marcar_error(self.hasta, False)
        self._marcar_atajo()

    def _atajo_elegido(self, atajo: str):
        self.fijar(*periodo_de(atajo, self._hoy()))
        self._al_elegir_atajo()

    def _marcar_atajo(self):
        try:
            escrito = (formato.leer_fecha(self.desde.get(), "Desde"), formato.leer_fecha(self.hasta.get(), "Hasta"))
        except ValueError:
            escrito = None  # a medio escribir: no se marca el campo; eso lo hace leer()
        hoy = self._hoy()
        claves = sorted((clave for clave, _ in ATAJOS), key=lambda clave: clave != self.atajos.valor)
        atajo = next((clave for clave in claves if periodo_de(clave, hoy) == escrito), None)
        if atajo is None:
            self.atajos.quitar_eleccion()
        else:
            self.atajos.elegir(atajo, avisar=False)

    def _escrito(self) -> tuple[str, str]:
        return self.desde.get(), self.hasta.get()
