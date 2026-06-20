# ─────────────────────────────────────────────
#  hardware/rgb_led.py — Controle do LED RGB
# ─────────────────────────────────────────────

import time
from machine import Pin


class RGBLed:
    """Controla o LED RGB cátodo-comum da BitDogLab.

    Blink não-bloqueante via blink_start() + tick().
    Blink bloqueante via blink() — use apenas no startup.
    """

    def __init__(self, r_pin, g_pin, b_pin):
        self.r = Pin(r_pin, Pin.OUT, value=1)
        self.g = Pin(g_pin, Pin.OUT, value=1)
        self.b = Pin(b_pin, Pin.OUT, value=1)
        self._blink_until = None  # ticks_ms em que o blink termina

    def set(self, r=False, g=False, b=False):
        """Liga canais individualmente (True = aceso)."""
        self.r.value(0 if r else 1)
        self.g.value(0 if g else 1)
        self.b.value(0 if b else 1)

    def off(self):
        """Desliga todos os canais."""
        self.set()

    def blink_start(self, r=False, g=False, b=False, ms=120):
        """Inicia blink não-bloqueante. Chame tick() no loop principal."""
        self.set(r, g, b)
        self._blink_until = time.ticks_add(time.ticks_ms(), ms)

    def tick(self):
        """Deve ser chamado a cada iteração do loop principal.
        Desliga o LED após o tempo configurado em blink_start().
        """
        if self._blink_until is not None:
            if time.ticks_diff(self._blink_until, time.ticks_ms()) <= 0:
                self.off()
                self._blink_until = None

    def blink(self, r=False, g=False, b=False, ms=120):
        """Blink bloqueante — use apenas fora do loop crítico (ex: startup)."""
        self.set(r, g, b)
        time.sleep_ms(ms)
        self.off()