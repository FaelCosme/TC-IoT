from machine import Pin, I2C
from logger import log


class OledDisplay:
    """Controla o display OLED SSD1306 128x64 via I2C.

    Se o display não for encontrado na inicialização,
    todos os métodos tornam-se no-ops (sem erro).
    """

    def __init__(self, sda_pin, scl_pin):
        try:
            i2c = I2C(1, sda=Pin(sda_pin), scl=Pin(scl_pin), freq=400_000)
            from ssd1306 import SSD1306_I2C
            self.oled = SSD1306_I2C(128, 64, i2c)
            self.ok = True
        except Exception as e:
            log("WARN", "OLED não encontrado: {}".format(e))
            self.ok = False

    def show(self, temp, umid, status="OK", count=0):
        """Exibe leitura de sensores, status MQTT e contador de publicações."""
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
        """Exibe até 3 linhas de texto livre (útil para status e erros)."""
        if not self.ok:
            return
        self.oled.fill(0)
        self.oled.text(line1, 0, 0)
        self.oled.text(line2, 0, 16)
        self.oled.text(line3, 0, 32)
        self.oled.show()
