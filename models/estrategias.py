from abc import ABC, abstractmethod

#INTERFAZ ABSTRACTA STRATEGY
class EstrategiaTriaje(ABC):
    """Interfaz que define el contrato para cualquier algoritmo de triaje"""

    @abstractmethod
    def clasificar(self, signos_vitales : dict, sintomas : list) -> int:
        """
        Recibe un diccionario de signos vitales y una lista de objetos Sintoma.
        Retorna el nivel de triaje calculado (1 al 5).
        """

    @abstractmethod
    def justificar(self) -> str:
        """Retorna la norma técnica o protocolo en el que se basó la decisión."""
        pass


#ESCALA MANCHESTER
class ReglaManchester(EstrategiaTriaje):
    """Implementación basada en el Sistema Manchester (t niveles)."""

    def clasificar(self, signos_vitales : dict, sintomas: list) -> int:
        # 1. Sumamos el peso clínico de todos los síntomas (ej. Dolor torácico = 8.5)
        peso_total = sum(s.peso_clinico for s in sintomas)

        # 2. Extraemos signos vitales clave con valores por defecto seguros
        sato2 = signos_vitales.get('sato2', 100)
        pa_sis = signos_vitales.get('pa_sis', 120)

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
        temp = signos_vitales.get('temp', 37.0)
        fc = signos_vitales.get('fc', 80)

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