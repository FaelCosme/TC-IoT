import network
import time
from umqtt.robust import MQTTClient
from logger import log


class NetworkManager:
    """Gerencia conexões Wi-Fi e MQTT com reconexão automática.

    Reconexão Wi-Fi usa backoff exponencial com cap em 30s.
    Reconexão MQTT verifica conexão via ping() antes de recriar.
    Publica 'online'/'offline' no tópico de availability para o HA.
    """

    def __init__(self, wifi_config, mqtt_config):
        self.wifi_ssid = wifi_config["ssid"]
        self.wifi_pass = wifi_config["password"]
        self.mqtt_broker = mqtt_config["broker"]
        self.mqtt_port = mqtt_config["port"]
        self.mqtt_client_id = mqtt_config["client_id"]
        self.mqtt_keepalive = mqtt_config.get("keepalive", 60)
        self.mqtt_qos = mqtt_config.get("qos", 1)
        self.mqtt_topics = mqtt_config["topics"]
        self.wlan = None
        self.mqtt = None

    # ── Propriedades para os tópicos ──────────

    @property
    def topic_temp(self):
        return self.mqtt_topics["temp"]

    @property
    def topic_umid(self):
        return self.mqtt_topics["umid"]

    @property
    def topic_rssi(self):
        return self.mqtt_topics["rssi"]

    @property
    def topic_pub_count(self):
        return self.mqtt_topics["pub_count"]

    @property
    def topic_availability(self):
        return self.mqtt_topics["availability"]

    # ── Wi-Fi ─────────────────────────────────

    def connect_wifi(self, max_attempts=20, matrix=None):
        """Conecta ao Wi-Fi. Exibe animação na matriz durante a espera."""
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(False)  # reset para limpar estado anterior
        time.sleep_ms(500)
        self.wlan.active(True)
        if self.wlan.isconnected():
            return self.wlan

        log("INFO", "Conectando Wi-Fi: {}".format(self.wifi_ssid))
        self.wlan.connect(self.wifi_ssid, self.wifi_pass)

        if matrix:
            matrix.connecting_animation()

        attempts = 0
        while not self.wlan.isconnected() and attempts < max_attempts:
            time.sleep(2)  # 2s entre tentativas — mais tempo para o roteador responder
            attempts += 1

        if self.wlan.isconnected():
            log("INFO", "Wi-Fi OK - IP: {}".format(self.wlan.ifconfig()[0]))
            return self.wlan

        raise RuntimeError("Falha Wi-Fi após {} tentativas".format(max_attempts))

    def ensure_wifi(self, matrix=None):
        """Garante Wi-Fi ativo; reconecta com backoff exponencial se necessário."""
        if self.wlan and self.wlan.isconnected():
            return self.wlan
        log("WARN", "Wi-Fi perdido, reconectando...")
        for attempt in range(5):
            try:
                return self.connect_wifi(max_attempts=5, matrix=matrix)
            except Exception as e:
                delay = min(2 ** attempt, 30)  # cap em 30s
                log("ERR", "Tentativa {}/5 falhou: {} — aguardando {}s".format(
                    attempt + 1, e, delay))
                time.sleep(delay)
        raise RuntimeError("Não foi possível reconectar Wi-Fi")

    # ── MQTT ──────────────────────────────────

    def connect_mqtt(self):
        """Cria e conecta cliente MQTT.

        Configura Last Will Testament (LWT) para que o HA marque o
        dispositivo como 'offline' automaticamente se a conexão cair.
        Publica 'online' no tópico de availability após conectar.
        """
        if self.mqtt:
            try:
                self.mqtt.disconnect()
            except Exception:
                pass  # ignora erros ao fechar conexão morta

        self.mqtt = MQTTClient(
            self.mqtt_client_id,
            self.mqtt_broker,
            port=self.mqtt_port,
            keepalive=self.mqtt_keepalive
        )

        # LWT: broker publica 'offline' automaticamente se o cliente sumir
        self.mqtt.set_last_will(
            self.topic_availability,
            b"offline",
            retain=True,
            qos=1
        )

        self.mqtt.connect()

        # Anuncia que está online (retained = HA recebe mesmo após reconectar)
        self.mqtt.publish(self.topic_availability, b"online", retain=True, qos=1)

        log("INFO", "MQTT conectado ao broker: {}".format(self.mqtt_broker))
        return self.mqtt

    def ensure_mqtt(self):
        """Verifica conexão com ping(); reconecta se necessário."""
        if self.mqtt:
            try:
                self.mqtt.ping()
                return self.mqtt
            except Exception:
                log("WARN", "MQTT sem resposta ao ping, reconectando...")
        return self.connect_mqtt()

    def publish(self, topic, payload, qos=None, retain=False):
        """Publica payload em um tópico MQTT."""
        if qos is None:
            qos = self.mqtt_qos
        self.mqtt.publish(topic, payload, retain=retain, qos=qos)

    def publish_offline(self):
        """Publica 'offline' no tópico de availability antes de desligar."""
        if self.mqtt:
            try:
                self.mqtt.publish(
                    self.topic_availability, b"offline", retain=True, qos=1)
            except Exception:
                pass

    def get_rssi(self):
        """Retorna o RSSI atual do Wi-Fi ou -100 se desconectado."""
        if self.wlan:
            return self.wlan.status('rssi')
        return -100
