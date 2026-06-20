# ─────────────────────────────────────────────
#  sensor.py — Sensor simulado de temperatura e umidade
#
#  Para usar um sensor real (ex: DHT22), basta criar
#  uma nova classe com o mesmo método read() e
#  substituir em monitor_system.py — sem alterar
#  nenhum outro arquivo.
# ─────────────────────────────────────────────

import random


class SimulatedSensor:
    """Simula leituras de temperatura e umidade com variação aleatória.

    Limites:
      Temperatura: 18.0 – 40.0 °C
      Umidade:     30.0 – 90.0 %
    """

    TEMP_MIN = 18.0
    TEMP_MAX = 40.0
    UMID_MIN = 30.0
    UMID_MAX = 90.0

    def __init__(self, temp_init=25.0, umid_init=60.0):
        self.temp = temp_init
        self.umid = umid_init

    def read(self):
        """Retorna (temperatura, umidade) com pequena variação aleatória."""
        self.temp += random.uniform(-0.3, 0.3)
        self.umid += random.uniform(-0.5, 0.5)
        self.temp = max(self.TEMP_MIN, min(self.TEMP_MAX, self.temp))
        self.umid = max(self.UMID_MIN, min(self.UMID_MAX, self.umid))
        return round(self.temp, 2), round(self.umid, 2)