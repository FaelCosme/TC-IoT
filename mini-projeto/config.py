CONFIG = {
    "wifi": {
        "ssid": "SEU SSID", # SSID da sua rede Wi-Fi modifique conforme necessário
        "password": "SUA_SENHA" # Senha da sua rede Wi-Fi modifique conforme necessário
    },
    "mqtt": {
        "broker": "SEU_IP_BROKER", # Modifique para o IP do seu broker MQTT
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
    "publish_interval_s": 10, # Intervalo de publicação em segundos
    "pins": {
        "led_r":  13,
        "led_g":  11,
        "led_b":  12,
        "matrix":  7,
        "sda":    14,
        "scl":    15
    }
}
