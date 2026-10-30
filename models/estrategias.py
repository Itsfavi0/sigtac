import operator
from abc import ABC, abstractmethod
from dataclasses import dataclass

from models.excepciones import SignosVitalesIncompletosError

# Comparaciones que usan las reglas; la clave es también el símbolo que se muestra en el criterio
_OPERADORES = {"<": operator.lt, ">": operator.gt, "≥": operator.ge}

# Criterio del nivel 5: ninguna condición de los niveles más urgentes se cumplió
SIN_CRITERIOS = "Ningún criterio de los niveles 1 a 4"


@dataclass(frozen=True)
class Clasificacion:
    """Nivel que calcula una estrategia y los criterios que lo decidieron (las condiciones cumplidas en ese nivel)."""
    nivel: int
    criterios: tuple[str, ...]


def condicion(etiqueta: str, valor, simbolo: str, umbral, unidad: str = "") -> tuple[bool, str]:
    """
    Una condición de una regla: si se cumple y su texto («SatO₂ 89 % < 90 %»). El umbral se escribe una sola
    vez, así el texto que ve el profesional no puede quedar distinto del valor que decide. Los números se muestran
    sin ceros de sobra (8.5, no 8.50), aunque lleguen como Decimal.
    """
    texto = f"{etiqueta} {float(valor):g}{unidad} {simbolo} {float(umbral):g}{unidad}"
    return _OPERADORES[simbolo](valor, umbral), texto


#INTERFAZ ABSTRACTA STRATEGY
class EstrategiaTriaje(ABC):
    """Interfaz que define el contrato para cualquier algoritmo de triaje"""

    @abstractmethod
    def evaluar(self, signos_vitales: dict, sintomas: list) -> Clasificacion:
        """
        Recibe un diccionario de signos vitales y una lista de objetos Sintoma.
        Retorna el nivel de triaje calculado (1 al 5) y los criterios que lo decidieron.
        Lanza SignosVitalesIncompletosError si falta algún signo vital que el
        algoritmo necesita: un dato no medido nunca se asume como normal.
        """

    def clasificar(self, signos_vitales: dict, sintomas: list) -> int:
        """Solo el nivel de triaje (1 al 5), para quien no necesita los criterios."""
        return self.evaluar(signos_vitales, sintomas).nivel

    @abstractmethod
    def justificar(self) -> str:
        """Retorna la norma técnica o protocolo en el que se basó la decisión."""
        pass

    @staticmethod
    def _exigir_signos(signos_vitales: dict, *claves: str) -> None:
        """Verifica que cada signo vital requerido exista y no sea None."""
        faltantes = [c for c in claves if signos_vitales.get(c) is None]
        if faltantes:
            raise SignosVitalesIncompletosError(
                f"No se puede clasificar: faltan los signos vitales {', '.join(faltantes)}."
            )

    @staticmethod
    def _decidir(*niveles: tuple[int, list[tuple[bool, str]]]) -> Clasificacion:
        """
        Recorre los niveles del más urgente al menos urgente: el primero con alguna condición cumplida es el
        nivel, y sus condiciones cumplidas son los criterios. Si no se cumple ninguna, el nivel es 5.
        """
        for nivel, condiciones in niveles:
            criterios = tuple(texto for cumple, texto in condiciones if cumple)
            if criterios:
                return Clasificacion(nivel, criterios)
        return Clasificacion(5, (SIN_CRITERIOS,))


#ESCALA MANCHESTER
class ReglaManchester(EstrategiaTriaje):
    """Implementación basada en el Sistema Manchester (t niveles)."""

    def evaluar(self, signos_vitales: dict, sintomas: list) -> Clasificacion:
        # 1. Sumamos el peso clínico de todos los síntomas (ej. Dolor torácico = 8.5)
        peso_total = sum(s.peso_clinico for s in sintomas)

        # 2. Extraemos los signos vitales clave (obligatorios: sin valores por defecto)
        self._exigir_signos(signos_vitales, 'sato2', 'pa_sis')
        sato2 = signos_vitales['sato2']
        pa_sis = signos_vitales['pa_sis']

        # 3. Lógica de clasificación estricta (Prioriza signos de shock)
        return self._decidir(
            (1, [condicion("Peso de los síntomas", peso_total, "≥", 10),        # Nivel I (Rojo)
                 condicion("SatO₂", sato2, "<", 90, " %"),
                 condicion("PA sistólica", pa_sis, "<", 80, " mmHg")]),
            (2, [condicion("Peso de los síntomas", peso_total, "≥", 7),         # Nivel II (Naranja)
                 condicion("PA sistólica", pa_sis, ">", 180, " mmHg")]),
            (3, [condicion("Peso de los síntomas", peso_total, "≥", 4)]),       # Nivel III (Amarillo)
            (4, [condicion("Peso de los síntomas", peso_total, "≥", 1)]),       # Nivel IV (Verde)
        )                                                                       # si no, Nivel V (Azul)

    def justificar(self) -> str:
        return "Clasificación sugerida aplicando las guías del Emergency Triage: Manchester Triage System."

#NORMA TÉCNICA MINSA
class ReglaMINSA(EstrategiaTriaje):
    """Implementación basada en la NTS N.º 042-MINSA/DGSP-V.01."""

    def evaluar(self, signos_vitales: dict, sintomas: list) -> Clasificacion:
        peso_total = sum(s.peso_clinico for s in sintomas)
        self._exigir_signos(signos_vitales, 'temp', 'fc')
        temp = signos_vitales['temp']
        fc = signos_vitales['fc']

        # Lógica MINSA: Suele ser más conservadora con la fiebre alta
        return self._decidir(
            (1, [condicion("Peso de los síntomas", peso_total, "≥", 9),
                 condicion("FC", fc, ">", 130, " lpm")]),
            (2, [condicion("Peso de los síntomas", peso_total, "≥", 6)]),
            (3, [condicion("Peso de los síntomas", peso_total, "≥", 3),
                 condicion("Temperatura", temp, "≥", 39.5, " °C")]),          # Fiebre muy alta asegura Nivel III
            (4, [condicion("Peso de los síntomas", peso_total, "≥", 1)]),
        )

    def justificar(self) -> str:
        return "Clasificación calculada según la Norma Técnica de Salud NTS N.º 042-MINSA/DGSP-V.01."
