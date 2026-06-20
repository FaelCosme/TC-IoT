# ─────────────────────────────────────────────
#  main.py — Ponto de entrada
#  Este é o único arquivo que o Pico W executa
#  automaticamente ao iniciar.
# ─────────────────────────────────────────────

from config import CONFIG
from monitor_system import MonitorSystem

system = MonitorSystem(CONFIG)
system.startup()
system.run()