from config import CONFIG
from monitor_system import MonitorSystem

system = MonitorSystem(CONFIG)
system.startup()
system.run()
