from abc import ABC, abstractmethod

from models.excepciones import SignosVitalesIncompletosError

#INTERFAZ ABSTRACTA STRATEGY
class EstrategiaTriaje(ABC):
    """Interfaz que define el contrato para cualquier algoritmo de triaje"""

    @abstractmethod
    def clasificar(self, signos_vitales : dict, sintomas : list) -> int:
        """
        Recibe un diccionario de signos vitales y una lista de objetos Sintoma.
        Retorna el nivel de triaje calculado (1 al 5).
        Lanza SignosVitalesIncompletosError si falta algún signo vital que el
        algoritmo necesita: un dato no medido nunca se asume como normal.
        """

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


#ESCALA MANCHESTER
class ReglaManchester(EstrategiaTriaje):
    """Implementación basada en el Sistema Manchester (t niveles)."""

    def clasificar(self, signos_vitales : dict, sintomas: list) -> int:
        # 1. Sumamos el peso clínico de todos los síntomas (ej. Dolor torácico = 8.5)
        peso_total = sum(s.peso_clinico for s in sintomas)

        # 2. Extraemos los signos vitales clave (obligatorios: sin valores por defecto)
        self._exigir_signos(signos_vitales, 'sato2', 'pa_sis')
        sato2 = signos_vitales['sato2']
        pa_sis = signos_vitales['pa_sis']

        # 3. Lógica de clasificación estricta (Prioriza signos de shock)
        if peso_total >= 10 or sato2 < 90 or pa_sis < 80:
            return 1  # Nivel I (Rojo)
        elif peso_total >= 7 or pa_sis > 180:
            return 2  # Nivel II (Naranja)
        elif peso_total >= 4:
            return 3  # Nivel III (Amarillo)
        elif peso_total >= 1:
            return 4  # Nivel IV (Verde)
        else:
            return 5  # Nivel V (Azul)

    def justificar(self) -> str:
        return "Clasificación sugerida aplicando las guías del Emergency Triage: Manchester Triage System."

#NORMA TÉCNICA MINSA
class ReglaMINSA(EstrategiaTriaje):
    """Implementación basada en la NTS N.º 042-MINSA/DGSP-V.01."""

    def clasificar(self, signos_vitales: dict, sintomas: list) -> int:
        peso_total = sum(s.peso_clinico for s in sintomas)
        self._exigir_signos(signos_vitales, 'temp', 'fc')
        temp = signos_vitales['temp']
        fc = signos_vitales['fc']

        # Lógica MINSA: Suele ser más conservadora con la fiebre alta
        if peso_total >= 9 or fc > 130:
            return 1
        elif peso_total >= 6:
            return 2
        elif peso_total >= 3 or temp >= 39.5:  # Fiebre muy alta asegura Nivel III
            return 3
        elif peso_total >= 1:
            return 4
        else:
            return 5

    def justificar(self) -> str:
        return "Clasificación calculada según la Norma Técnica de Salud NTS N.º 042-MINSA/DGSP-V.01."