import time


def log(level, msg):
    """Exibe mensagem com nível e timestamp em ms.

    Níveis sugeridos: INFO | WARN | ERR
    """
    print("[{}][{}ms] {}".format(level, time.ticks_ms(), msg))
