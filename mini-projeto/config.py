# ─────────────────────────────────────────────
#  config.py — Configurações centralizadas
#  Edite aqui sem precisar tocar no código principal.
#
#  BROKER: IP do PC onde o Mosquitto está rodando.
#  Certifique-se de que o Mosquitto escuta em 0.0.0.0
#  (não apenas 127.0.0.1) para aceitar conexões externas.
#  Verifique em: mosquitto.conf → listener 1883 0.0.0.0
# ─────────────────────────────────────────────

CONFIG = {
    "wifi": {
        "ssid": "Rafael",
        "password": "12345678"
    },
    "mqtt": {
        # IP do PC com Mosquitto — troque se necessário
        "broker": "10.238.23.112",
        "port": 1883,
        "client_id": "bitdoglab_01",
        "keepalive": 60,
        "qos": 1,
        "topics": {
            # Dados dos sensores
            "temp":         b"bitdoglab/sala/temperatura",
            "umid":         b"bitdoglab/sala/umidade",
            # Métricas do dispositivo
            "rssi":         b"bitdoglab/sala/rssi",
            "pub_count":    b"bitdoglab/sala/pub_count",
            # Availability — HA usa para saber se o device está online
            "availability": b"bitdoglab/sala/availability",
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