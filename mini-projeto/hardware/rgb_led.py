# ─────────────────────────────────────────────
#  hardware/rgb_led.py — Controle do LED RGB
#  BitDogLab: LED RGB cátodo-comum
#  Pinos: R=13, G=11, B=12
#  Lógica invertida: value(0) = aceso, value(1) = apagado
# ─────────────────────────────────────────────

import time
from machine import Pin


class RGBLed:
    """Controla o LED RGB cátodo-comum da BitDogLab.

    Lógica invertida: value(1) = apagado, value(0) = aceso.
    Normalmente DESLIGADO.
    Pisca verde ao publicar, vermelho em erro.
    """

    def __init__(self, r_pin, g_pin, b_pin):
        self.r = Pin(r_pin, Pin.OUT, value=0)
        self.g = Pin(g_pin, Pin.OUT, value=0)
        self.b = Pin(b_pin, Pin.OUT, value=0)
        self._blink_until = None

    def off(self):
        """Apaga todos os canais."""
        self.r.value(0)
        self.g.value(0)
        self.b.value(0)

    def _on(self, r=False, g=False, b=False):
        """Liga canais individualmente (uso interno)."""
        self.r.value(1 if r else 0)
        self.g.value(1 if g else 0)
        self.b.value(1 if b else 0)

    def blink(self, r=False, g=False, b=False, ms=200):
        """Blink bloqueante — pisca e apaga. Use só no startup."""
        self._on(r, g, b)
        time.sleep_ms(ms)
        self.off()

    def blink_start(self, r=False, g=False, b=False, ms=200):
        """Inicia blink não-bloqueante. Chame tick() no loop principal."""
        self._on(r, g, b)
        self._blink_until = time.ticks_add(time.ticks_ms(), ms)

    def tick(self):
        """Chame a cada iteração do loop — apaga após o tempo do blink."""
        if self._blink_until is not None:
            if time.ticks_diff(self._blink_until, time.ticks_ms()) <= 0:
                self.off()
                self._blink_until = None
