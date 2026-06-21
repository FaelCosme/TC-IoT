import time
import neopixel
from machine import Pin


class Matrix5x5:
    """Controla a matriz de LEDs WS2812 5x5 da BitDogLab.

    Funcionalidades:
      - Ícone de sinal Wi-Fi com 1-4 barras conforme RSSI
      - Animação de conexão
      - Indicação de erro (X vermelho)
      - Flash verde ao publicar
    """

    def __init__(self, pin):
        self.np = neopixel.NeoPixel(Pin(pin), 25)
        self._last_rssi = None
        self.clear()

    def _idx(self, row, col):
        """Converte (row, col) para índice linear com layout serpentina."""
        if not (0 <= row < 5 and 0 <= col < 5):
            raise ValueError("Posição inválida: ({}, {})".format(row, col))
        if row % 2 == 0:
            return row * 5 + col
        else:
            return row * 5 + (4 - col)

    def clear(self):
        """Apaga todos os LEDs."""
        self.np.fill((0, 0, 0))
        self.np.write()


    def connecting_animation(self):
        """Animação de carregamento exibida durante a conexão Wi-Fi."""
        for frame in range(10):
            self.clear()
            lit = (frame * 3) % 25
            for i in range(lit):
                self.np[i] = (15, 15, 0)
            self.np.write()
            time.sleep_ms(200)

    def error(self):
        """Exibe X vermelho indicando erro crítico."""
        self.clear()
        red = (30, 0, 0)
        for i in range(5):
            self.np[self._idx(i, i)] = red
            self.np[self._idx(i, 4 - i)] = red
        self.np.write()

    def flash_green(self):
        """Flash verde rápido ao publicar, restaurando ícone Wi-Fi em seguida."""
        self.np.fill((0, 20, 0))
        self.np.write()
        time.sleep_ms(80)
        self.clear()
        if self._last_rssi is not None:
            self.show_wifi(self._last_rssi)
