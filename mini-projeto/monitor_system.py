# ─────────────────────────────────────────────
#  monitor_system.py — Orquestrador principal
# ─────────────────────────────────────────────

import time
from machine import Timer

from hardware.rgb_led import RGBLed
from hardware.matrix import Matrix5x5
from hardware.display import OledDisplay
from sensor import SimulatedSensor
from network_manager import NetworkManager
from logger import log


class MonitorSystem:
    """Orquestra todos os subsistemas do monitor IoT.

    Fluxo:
      startup() → inicializa periféricos, Wi-Fi, MQTT e timer
      run()     → loop principal: publicação, tick do LED e RSSI

    O timer apenas sinaliza uma flag; toda I/O de rede ocorre
    no loop principal, evitando problemas de IRQ no MicroPython.

    Tópicos publicados (configurados em config.py):
      temperatura, umidade, rssi, pub_count, availability
    """

    def __init__(self, config):
        self.config = config
        pins = config["pins"]

        self.rgb = RGBLed(pins["led_r"], pins["led_g"], pins["led_b"])
        self.matrix = Matrix5x5(pins["matrix"])
        self.display = OledDisplay(pins["sda"], pins["scl"])
        self.sensor = SimulatedSensor()
        self.net = NetworkManager(config["wifi"], config["mqtt"])

        self.pub_count = 0
        self.timer = None
        self._publish_flag = False  # sinalizada pelo timer, consumida no loop

    def startup(self):
        """Inicializa Wi-Fi, MQTT e timer de publicação."""
        self.matrix.clear()
        self.rgb.off()
        self.display.message("Iniciando...", "Wi-Fi")

        # Wi-Fi
        try:
            self.net.connect_wifi(matrix=self.matrix)
        except Exception as e:
            self.matrix.error()
            self.rgb.set(r=True)
            self.display.message("ERRO Wi-Fi", str(e)[:16])
            raise

        rssi = self.net.get_rssi()
        self.matrix.show_wifi(rssi)
        self.rgb.blink(g=True, ms=200)
        self.display.message("Wi-Fi OK", "RSSI: {}".format(rssi))
        time.sleep(1)

        # MQTT (connect_mqtt já publica 'online' e configura LWT)
        try:
            self.net.connect_mqtt()
        except Exception as e:
            self.matrix.error()
            self.rgb.set(r=True)
            self.display.message("ERRO MQTT", str(e)[:16])
            raise

        self.display.message("Sistema OK", "Timer iniciado")
        time.sleep(1)

        # Timer: apenas seta a flag — sem I/O dentro do IRQ
        interval_ms = self.config["publish_interval_s"] * 1000
        self.timer = Timer()
        self.timer.init(
            period=interval_ms,
            mode=Timer.PERIODIC,
            callback=lambda t: setattr(self, '_publish_flag', True)
        )
        log("INFO", "Sistema iniciado. Publicando a cada {}s.".format(
            self.config["publish_interval_s"]))

    def _do_publish(self):
        """Lê sensores e publica todos os tópicos via MQTT."""
        temp, umid = 0.0, 0.0  # inicializa antes do try para uso no except
        try:
            self.net.ensure_wifi(matrix=self.matrix)
            self.net.ensure_mqtt()

            temp, umid = self.sensor.read()
            rssi = self.net.get_rssi()
            self.pub_count += 1

            log("INFO", "T={:.2f}C  U={:.2f}%  RSSI={}  Pub#{}".format(
                temp, umid, rssi, self.pub_count))

            # Publica todos os tópicos
            self.net.publish(self.net.topic_temp,      str(temp).encode())
            self.net.publish(self.net.topic_umid,      str(umid).encode())
            self.net.publish(self.net.topic_rssi,      str(rssi).encode())
            self.net.publish(self.net.topic_pub_count, str(self.pub_count).encode())

            # Feedback visual não-bloqueante
            self.rgb.blink_start(b=True, ms=100)
            self.matrix.flash_green()
            self.display.show(temp, umid, status="OK", count=self.pub_count)

        except Exception as e:
            log("ERR", "Erro na publicação: {}".format(e))
            self.display.show(temp, umid, status="ERR", count=self.pub_count)
            self.rgb.blink_start(r=True, ms=300)

    def run(self):
        """Loop principal: publicação, tick do LED e atualização do RSSI."""
        try:
            while True:
                try:
                    if self._publish_flag:
                        self._publish_flag = False
                        self._do_publish()

                    self.rgb.tick()

                    self.net.ensure_wifi(matrix=self.matrix)
                    rssi = self.net.get_rssi()
                    self.matrix.show_wifi(rssi)

                except Exception as e:
                    log("ERR", "Erro no loop principal: {}".format(e))
                    self.matrix.error()
                    self.rgb.set(r=True)
                    time.sleep(5)
                    try:
                        self.net.ensure_wifi(matrix=self.matrix)
                        self.rgb.off()
                    except Exception:
                        pass

                time.sleep_ms(100)

        finally:
            # Garante publicação de 'offline' mesmo em caso de exceção fatal
            log("WARN", "Sistema encerrando — publicando offline")
            self.net.publish_offline()