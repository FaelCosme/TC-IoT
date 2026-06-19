"""
Mini Projeto - Sistema de Monitoramento com MQTT (Versão Refatorada)
Disciplina: Tecnologias de Comunicação para IoT – IMD0907
Hardware: BitDogLab (Raspberry Pi Pico W)
Linguagem: MicroPython

Funcionalidades:
  - Simula leitura de temperatura e umidade
  - Publica via MQTT com QoS 1 (usando umqtt.robust)
  - Matriz WS2812: indicador de força de sinal Wi-Fi
  - Display OLED SSD1306: exibe dados e status
  - LED RGB: pisca ao publicar
  - Timer para publicações periódicas
  - Reconexão automática Wi-Fi e MQTT
"""

# ─────────────────────────────────────────────
#  IMPORTAÇÕES
# ─────────────────────────────────────────────
import network
import time
import random
from machine import Pin, I2C, Timer
from umqtt.robust import MQTTClient
import neopixel

# ─────────────────────────────────────────────
#  CONFIGURAÇÃO (centralizada)
# ─────────────────────────────────────────────
CONFIG = {
    "wifi": {
        "ssid": "Rafael",
        "password": "12345678"
    },
    "mqtt": {
        "broker": "10.238.23.112",
        "port": 1883,
        "client_id": "bitdoglab_01",
        "keepalive": 60,
        "qos": 1,
        "topics": {
            "temp": b"casa/sala/temperatura",
            "umid": b"casa/sala/umidade"
        }
    },
    "publish_interval_s": 5,
    "pins": {
        "led_r": 13,
        "led_g": 11,
        "led_b": 12,
        "matrix": 7,
        "sda": 14,
        "scl": 15
    }
}

# ─────────────────────────────────────────────
#  CLASSE LED RGB (active low)
# ─────────────────────────────────────────────
class RGBLed:
    def __init__(self, r_pin, g_pin, b_pin):
        self.r = Pin(r_pin, Pin.OUT, value=1)
        self.g = Pin(g_pin, Pin.OUT, value=1)
        self.b = Pin(b_pin, Pin.OUT, value=1)

    def set(self, r=False, g=False, b=False):
        self.r.value(0 if r else 1)
        self.g.value(0 if g else 1)
        self.b.value(0 if b else 1)

    def off(self):
        self.set()

    def blink(self, r=False, g=False, b=False, ms=120):
        self.set(r, g, b)
        time.sleep_ms(ms)
        self.off()

# ─────────────────────────────────────────────
#  CLASSE MATRIZ WS2812 (5x5)
# ─────────────────────────────────────────────
class Matrix5x5:
    def __init__(self, pin):
        self.np = neopixel.NeoPixel(Pin(pin), 25)
        self._last_rssi = None
        self.clear()

    def _idx(self, row, col):
        # Serpentine layout
        if row % 2 == 0:
            return row * 5 + col
        else:
            return row * 5 + (4 - col)

    def clear(self):
        self.np.fill((0, 0, 0))
        self.np.write()

    def show_wifi(self, rssi):
        """Desenha ícone de Wi-Fi com barras conforme RSSI."""
        if rssi == self._last_rssi:
            return
        self._last_rssi = rssi
        self.clear()

        if rssi >= -55:
            bars = 4
        elif rssi >= -65:
            bars = 3
        elif rssi >= -75:
            bars = 2
        else:
            bars = 1

        green = (0, 30, 0)
        # Barra central (sempre acesa)
        self.np[self._idx(4, 2)] = green

        if bars >= 2:
            for pos in [(4,1), (3,1), (4,3), (3,3)]:
                self.np[self._idx(*pos)] = green
        if bars >= 3:
            for pos in [(4,0), (3,0), (2,0), (4,4), (3,4), (2,4)]:
                self.np[self._idx(*pos)] = green
        if bars >= 4:
            for pos in [(1,0), (1,4)]:
                self.np[self._idx(*pos)] = green

        self.np.write()

    def connecting_animation(self):
        for frame in range(10):
            self.clear()
            lit = (frame * 3) % 25
            for i in range(lit):
                self.np[i] = (15, 15, 0)
            self.np.write()
            time.sleep_ms(200)

    def error(self):
        self.clear()
        red = (30, 0, 0)
        for i in range(5):
            self.np[self._idx(i, i)] = red
            self.np[self._idx(i, 4 - i)] = red
        self.np.write()

    def flash_green(self):
        self.np.fill((0, 20, 0))
        self.np.write()
        time.sleep_ms(80)
        self.clear()
        # Restaura ícone se houver RSSI salvo
        if self._last_rssi is not None:
            self.show_wifi(self._last_rssi)

# ─────────────────────────────────────────────
#  CLASSE DISPLAY OLED
# ─────────────────────────────────────────────
class OledDisplay:
    def __init__(self, sda_pin, scl_pin):
        try:
            i2c = I2C(1, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=400_000)
            from ssd1306 import SSD1306_I2C
            self.oled = SSD1306_I2C(128, 64, i2c)
            self.ok = True
        except Exception as e:
            print("OLED não encontrado:", e)
            self.ok = False

    def show(self, temp, umid, status="OK", count=0):
        if not self.ok:
            return
        self.oled.fill(0)
        self.oled.text("== BitDogLab ==", 0, 0)
        self.oled.text("Temp: {:.1f} C".format(temp), 0, 16)
        self.oled.text("Umid: {:.1f} %".format(umid), 0, 28)
        self.oled.text("MQTT: {}".format(status), 0, 42)
        self.oled.text("Pub: {}".format(count), 0, 54)
        self.oled.show()

    def message(self, line1, line2="", line3=""):
        if not self.ok:
            return
        self.oled.fill(0)
        self.oled.text(line1, 0, 0)
        self.oled.text(line2, 0, 16)
        self.oled.text(line3, 0, 32)
        self.oled.show()

# ─────────────────────────────────────────────
#  CLASSE SENSOR SIMULADO
# ─────────────────────────────────────────────
class SimulatedSensor:
    def __init__(self, temp_init=25.0, umid_init=60.0):
        self.temp = temp_init
        self.umid = umid_init

    def read(self):
        self.temp += random.uniform(-0.3, 0.3)
        self.umid += random.uniform(-0.5, 0.5)
        self.temp = max(18.0, min(40.0, self.temp))
        self.umid = max(30.0, min(90.0, self.umid))
        return round(self.temp, 2), round(self.umid, 2)

# ─────────────────────────────────────────────
#  CLASSE GERENCIADORA DE CONEXÃO (Wi-Fi + MQTT)
# ─────────────────────────────────────────────
class NetworkManager:
    def __init__(self, wifi_config, mqtt_config):
        self.wifi_ssid = wifi_config["ssid"]
        self.wifi_pass = wifi_config["password"]
        self.mqtt_broker = mqtt_config["broker"]
        self.mqtt_port = mqtt_config["port"]
        self.mqtt_client_id = mqtt_config["client_id"]
        self.mqtt_keepalive = mqtt_config.get("keepalive", 60)
        self.mqtt_qos = mqtt_config.get("qos", 1)
        self.mqtt_topics = mqtt_config["topics"]
        self.wlan = None
        self.mqtt = None

    def connect_wifi(self, max_attempts=10):
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        if self.wlan.isconnected():
            return self.wlan

        print("Conectando Wi-Fi:", self.wifi_ssid)
        self.wlan.connect(self.wifi_ssid, self.wifi_pass)

        attempts = 0
        while not self.wlan.isconnected() and attempts < max_attempts:
            time.sleep(1)
            attempts += 1

        if self.wlan.isconnected():
            print("Wi-Fi OK - IP:", self.wlan.ifconfig()[0])
            return self.wlan
        else:
            raise RuntimeError("Falha Wi-Fi")

    def ensure_wifi(self):
        if self.wlan and self.wlan.isconnected():
            return self.wlan
        print("Wi-Fi perdido, reconectando...")
        for attempt in range(5):
            try:
                return self.connect_wifi(max_attempts=5)
            except:
                time.sleep(2 ** attempt)
        raise RuntimeError("Não foi possível reconectar Wi-Fi")

    def connect_mqtt(self):
        self.mqtt = MQTTClient(
            self.mqtt_client_id,
            self.mqtt_broker,
            port=self.mqtt_port,
            keepalive=self.mqtt_keepalive
        )
        self.mqtt.connect()
        print("MQTT conectado ao broker:", self.mqtt_broker)
        return self.mqtt

    def ensure_mqtt(self):
        if self.mqtt and self.mqtt.is_connected():
            return self.mqtt
        print("MQTT desconectado, reconectando...")
        return self.connect_mqtt()

    def publish(self, topic, payload, qos=None):
        if qos is None:
            qos = self.mqtt_qos
        self.mqtt.publish(topic, payload, qos=qos)

    def get_rssi(self):
        if self.wlan:
            return self.wlan.status('rssi')
        return -100

# ─────────────────────────────────────────────
#  CLASSE PRINCIPAL DO SISTEMA
# ─────────────────────────────────────────────
class MonitorSystem:
    def __init__(self, config):
        self.config = config
        self.rgb = RGBLed(
            config["pins"]["led_r"],
            config["pins"]["led_g"],
            config["pins"]["led_b"]
        )
        self.matrix = Matrix5x5(config["pins"]["matrix"])
        self.display = OledDisplay(config["pins"]["sda"], config["pins"]["scl"])
        self.sensor = SimulatedSensor()
        self.net = NetworkManager(config["wifi"], config["mqtt"])
        self.pub_count = 0
        self.timer = None

    def startup(self):
        """Inicializa Wi-Fi, MQTT e timer."""
        self.matrix.clear()
        self.rgb.off()
        self.display.message("Iniciando...", "Wi-Fi")

        # Wi-Fi
        try:
            self.net.connect_wifi()
        except Exception as e:
            self.matrix.error()
            self.rgb.set(r=True)
            self.display.message("ERRO Wi-Fi", str(e))
            raise

        rssi = self.net.get_rssi()
        self.matrix.show_wifi(rssi)
        self.rgb.blink(g=True, ms=200)
        self.display.message("Wi-Fi OK", "RSSI: {}".format(rssi))
        time.sleep(1)

        # MQTT
        try:
            self.net.connect_mqtt()
        except Exception as e:
            self.matrix.error()
            self.rgb.set(r=True)
            self.display.message("ERRO MQTT", str(e))
            raise

        self.display.message("Sistema OK", "Timer iniciado")
        time.sleep(1)

        # Timer para publicações
        interval_ms = self.config["publish_interval_s"] * 1000
        self.timer = Timer()
        self.timer.init(period=interval_ms, mode=Timer.PERIODIC, callback=self._publish_callback)

    def _publish_callback(self, timer):
        """Callback do timer: lê sensores e publica."""
        try:
            # Garante conexões
            self.net.ensure_wifi()
            self.net.ensure_mqtt()

            temp, umid = self.sensor.read()
            print("T={:.2f}°C  U={:.2f}%".format(temp, umid))

            # Publica
            self.net.publish(self.config["mqtt"]["topics"]["temp"], str(temp).encode())
            self.net.publish(self.config["mqtt"]["topics"]["umid"], str(umid).encode())
            self.pub_count += 1

            # Feedback
            self.rgb.blink(b=True, ms=100)
            self.matrix.flash_green()
            self.display.show(temp, umid, status="OK", count=self.pub_count)
            print("Publicado #{} com QoS {}".format(self.pub_count, self.config["mqtt"]["qos"]))

        except Exception as e:
            print("Erro na publicação:", e)
            self.display.show(
                temp if 'temp' in locals() else 0.0,
                umid if 'umid' in locals() else 0.0,
                status="ERR", count=self.pub_count
            )
            self.rgb.set(r=True)
            time.sleep_ms(300)
            self.rgb.off()
            # Força reconexão na próxima chamada (MQTT será recriado)

    def run(self):
        """Loop principal: verifica Wi-Fi e atualiza matriz."""
        while True:
            try:
                # Verifica Wi-Fi e atualiza RSSI
                self.net.ensure_wifi()
                rssi = self.net.get_rssi()
                self.matrix.show_wifi(rssi)
            except Exception as e:
                print("Erro no loop principal:", e)
                self.matrix.error()
                self.rgb.set(r=True)
                time.sleep(5)
                try:
                    self.net.ensure_wifi()
                    self.rgb.off()
                except:
                    pass
            time.sleep_ms(1000)

# ─────────────────────────────────────────────
#  PONTO DE ENTRADA
# ─────────────────────────────────────────────
if __name__ == "__main__":
    system = MonitorSystem(CONFIG)
    system.startup()
    system.run()