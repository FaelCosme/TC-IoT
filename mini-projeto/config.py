# ─────────────────────────────────────────────
#  config.py — Configurações centralizadas
# ─────────────────────────────────────────────

CONFIG = {
    "wifi": {
        "ssid": "clara LINDA",
        "password": "Rafael@2017"
    },
    "mqtt": {
        "broker": "192.168.0.44",
        "port": 1883,
        "client_id": "bitdoglab_01",
        "keepalive": 60,
        "qos": 1,
        "topics": {
            "temp":         b"bitdoglab/sala/temperatura",
            "umid":         b"bitdoglab/sala/umidade",
            "rssi":         b"bitdoglab/sala/rssi",
            "pub_count":    b"bitdoglab/sala/pub_count",
            "availability": b"bitdoglab/sala/availability",
        }
    },
    "publish_interval_s": 30,
    "pins": {
        "led_r":  13,
        "led_g":  11,
        "led_b":  12,
        "matrix":  7,
        "sda":    14,
        "scl":    15
    }
}
