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

    LED RGB:
      - Normalmente DESLIGADO
      - Pisca verde (200ms) ao publicar com sucesso
      - Pisca vermelho (500ms) em caso de erro

    Matriz WS2812:
      - Animação durante conexão Wi-Fi
      - Ícone Wi-Fi por 3s após conectar
      - Desliga e fica apagada para sempre após o startup
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
        self._publish_flag = False

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
            self.rgb.blink(r=80, ms=500)  # pisca vermelho e apaga
            self.display.message("ERRO Wi-Fi", str(e)[:16])
            raise

        # Ícone Wi-Fi por 3s, depois matriz apaga para sempre
        rssi = self.net.get_rssi()
        self.matrix.show_wifi(rssi)
        self.rgb.blink(g=80, ms=300)  # pisca verde = Wi-Fi OK, apaga
        self.display.message("Wi-Fi OK", "RSSI: {}".format(rssi))
        time.sleep(3)
        self.matrix.clear()

        # MQTT
        try:
            self.net.connect_mqtt()
        except Exception as e:
            self.rgb.blink(r=80, ms=500)  # pisca vermelho e apaga
            self.display.message("ERRO MQTT", str(e)[:16])
            raise

        self.rgb.blink(g=80, ms=300)  # pisca verde = MQTT OK, apaga
        self.display.message("Sistema OK", "Timer iniciado")
        time.sleep(1)

        # LED garantidamente apagado antes de entrar no loop
        self.rgb.off()

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
        temp, umid = 0.0, 0.0
        try:
            self.net.ensure_wifi()
            self.net.ensure_mqtt()

            temp, umid = self.sensor.read()
            rssi = self.net.get_rssi()
            self.pub_count += 1

            log("INFO", "T={:.2f}C  U={:.2f}%  RSSI={}  Pub#{}".format(
                temp, umid, rssi, self.pub_count))

            self.net.publish(self.net.topic_temp,      str(temp).encode())
            self.net.publish(self.net.topic_umid,      str(umid).encode())
            self.net.publish(self.net.topic_rssi,      str(rssi).encode())
            self.net.publish(self.net.topic_pub_count, str(self.pub_count).encode())

            # Pisca verde — apaga sozinho via tick()
            self.rgb.blink_start(g=80, ms=200)
            self.display.show(temp, umid, status="OK", count=self.pub_count)

        except Exception as e:
            log("ERR", "Erro na publicação: {}".format(e))
            self.display.show(temp, umid, status="ERR", count=self.pub_count)
            # Pisca vermelho — apaga sozinho via tick()
            self.rgb.blink_start(r=80, ms=500)

    def run(self):
        """Loop principal: publicação e tick do LED."""
        try:
            while True:
                try:
                    if self._publish_flag:
                        self._publish_flag = False
                        self._do_publish()

                    # Apaga o LED após o tempo do blink
                    self.rgb.tick()

                except Exception as e:
                    log("ERR", "Erro no loop principal: {}".format(e))
                    self.rgb.blink_start(r=80, ms=500)
                    time.sleep(5)
                    try:
                        self.net.ensure_wifi()
                    except Exception:
                        pass

                time.sleep_ms(100)

        finally:
            log("WARN", "Sistema encerrando — publicando offline")
            self.rgb.off()
            self.net.publish_offline()
