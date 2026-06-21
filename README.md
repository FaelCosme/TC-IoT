# TC-IoT
# 🌡️ BitDogLab — Monitor IoT com MQTT + Home Assistant

Sistema de monitoramento de temperatura e umidade desenvolvido para a **BitDogLab (Raspberry Pi Pico W)** com MicroPython.
Publica dados via **MQTT (QoS 1)** e exibe em tempo real no **Home Assistant**.

> **Disciplina:** Tecnologias de Comunicação para IoT — IMD0907  
> **Professora:** Fernanda Tasso Salmoria — UFRN / Instituto Metrópole Digital

---

## 📁 Estrutura do projeto

```
bitdoglab/
├── main.py                  # Ponto de entrada — executado automaticamente pelo Pico W
├── config.py                # ⚙️  Todas as configurações (Wi-Fi, broker, pinos, intervalo)
├── logger.py                # Log centralizado com timestamp
├── monitor_system.py        # Orquestrador principal
├── network_manager.py       # Wi-Fi + MQTT com reconexão automática e LWT
├── sensor.py                # Sensor simulado (fácil substituir por DHT22)
│
├── hardware/
│   ├── rgb_led.py           # LED RGB — pisca verde (OK) ou vermelho (erro)
│   ├── matrix.py            # Matriz WS2812 5x5 — ícone Wi-Fi no startup
│   └── display.py           # Display OLED SSD1306 — exibe dados em tempo real
│
├── homeassistant/
│   ├── configuration.yaml   # Sensores MQTT para o HA
│   ├── automations.yaml     # 7 automações de alerta
│   └── dashboard.yaml       # Cartão Lovelace (gauges + gráficos)
│
└── .vscode/
    └── settings.json        # Configuração do MicroPico (ignora homeassistant/ no upload)
```

---

## 🔧 Pré-requisitos

| Componente | Versão/Detalhe |
|---|---|
| Hardware | BitDogLab (Raspberry Pi Pico W) |
| Linguagem | MicroPython |
| Editor | VS Code + extensão MicroPico |
| Broker MQTT | Mosquitto (instalado no PC) |
| Dashboard | Home Assistant (Docker) |
| Biblioteca | `umqtt.robust` (na pasta `lib/umqtt/`) |

---

## 🚀 Configuração e instalação

### 1. Mosquitto

O Mosquitto precisa escutar em `0.0.0.0` para aceitar conexões externas (Pico W e HA Docker).

Edite `mosquitto.conf`:

```
listener 1883 0.0.0.0
allow_anonymous true
```

Reinicie o Mosquitto e teste:

```bash
mosquitto_sub -h localhost -t "bitdoglab/#" -v
```

---

### 2. Configurar `config.py`

Edite as credenciais antes de enviar para a placa:

```python
CONFIG = {
    "wifi": {
        "ssid": "SUA_REDE",          # ⚠️ apenas redes 2.4GHz
        "password": "SUA_SENHA"
    },
    "mqtt": {
        "broker": "IP_DO_SEU_PC",    # ex: 192.168.0.44
        ...
    },
    "publish_interval_s": 30,        # intervalo entre publicações
    ...
}
```

---

### 3. Enviar para o Pico W (MicroPico + VS Code)

1. Conecte o Pico W via USB
2. `Ctrl+Shift+P` → **MicroPico: Connect**
3. `Ctrl+Shift+P` → **MicroPico: Upload Project to Pico**
   - As pastas `homeassistant/` e `.vscode/` são ignoradas automaticamente
4. Confirme os arquivos na placa via REPL:

```python
import os
os.listdir()
os.listdir('hardware')
os.listdir('lib/umqtt')  # deve conter simple.py e robust.py
```

5. Execute: `Ctrl+Shift+P` → **MicroPico: Run current file** (com `main.py` aberto)

---

### 4. Home Assistant (Docker)

**Integração MQTT:**
- Configurações → Integrações → Adicionar → MQTT
- Broker: `IP do seu PC` | Porta: `1883`

**Sensores:**  
Cole o conteúdo de `homeassistant/configuration.yaml` no `configuration.yaml` do HA.  
Recarregue: Ferramentas do Desenvolvedor → YAML → Recarregar toda a configuração.

**Automações:**  
Configurações → Automações → Criar Automação → Editar YAML → cole cada bloco de `automations.yaml`.

**Dashboard:**  
Editar dashboard → 3 pontos → Editar YAML → cole o conteúdo de `dashboard.yaml` dentro de `cards:`.  
> Para os gráficos de histórico, instale o **mini-graph-card** via HACS.  
> Alternativa nativa: substitua `custom:mini-graph-card` por `type: history-graph`.

---

## 📡 Tópicos MQTT

| Tópico | Conteúdo | QoS | Retained |
|---|---|---|---|
| `bitdoglab/sala/temperatura` | Temperatura (°C) | 1 | Não |
| `bitdoglab/sala/umidade` | Umidade relativa (%) | 1 | Não |
| `bitdoglab/sala/rssi` | Sinal Wi-Fi (dBm) | 1 | Não |
| `bitdoglab/sala/pub_count` | Total de publicações | 1 | Não |
| `bitdoglab/sala/availability` | `online` / `offline` | 1 | **Sim** |

O tópico `availability` usa **LWT (Last Will Testament)**: se o Pico W perder conexão abruptamente, o broker publica `offline` automaticamente e o HA marca o dispositivo como indisponível.

---

## 🔔 Automações configuradas no HA

| Automação | Condição |
|---|---|
| 🌡️ Temperatura Alta | Temp > 30°C por 1 min |
| ❄️ Temperatura Baixa | Temp < 20°C por 1 min |
| 💧 Umidade Alta | Umidade > 80% por 2 min |
| 🏜️ Umidade Baixa | Umidade < 40% por 2 min |
| 📵 Dispositivo Offline | Sem conexão por 1 min |
| ✅ Dispositivo Online | Reconexão após > 1 min offline |
| 📶 Sinal Wi-Fi Fraco | RSSI < -80 dBm por 5 min |

---

## 💡 Comportamento do hardware

| Componente | Comportamento |
|---|---|
| **LED RGB** | Apagado normalmente · Verde (200ms) ao publicar · Vermelho (500ms) em erro |
| **Matriz WS2812** | Animação amarela durante conexão Wi-Fi → ícone de barras por 3s → apaga |
| **Display OLED** | Exibe temperatura, umidade, status MQTT e contador de publicações |

---

## 🔄 Substituir sensor simulado por DHT22

Adicione em `sensor.py`:

```python
import dht
from machine import Pin

class DHT22Sensor:
    def __init__(self, pin):
        self.sensor = dht.DHT22(Pin(pin))

    def read(self):
        self.sensor.measure()
        return self.sensor.temperature(), self.sensor.humidity()
```

Em `monitor_system.py`, troque:

```python
from sensor import SimulatedSensor
self.sensor = SimulatedSensor()
```

por:

```python
from sensor import DHT22Sensor
self.sensor = DHT22Sensor(pin=28)  # ajuste o pino
```

Nenhum outro arquivo precisa ser alterado.

---

## 🐛 Solução de problemas

| Problema | Causa provável | Solução |
|---|---|---|
| `RuntimeError: Falha Wi-Fi` | Rede 5GHz ou senha errada | Use rede 2.4GHz; verifique credenciais em `config.py` |
| `ImportError: umqtt.robust` | Arquivo faltando na placa | Instale via REPL: `import mip; mip.install('umqtt.robust')` |
| Não aparece no HA | Broker inacessível | Verifique `listener 1883 0.0.0.0` no `mosquitto.conf` |
| LED sempre aceso | Upload incompleto | Delete o arquivo na placa e faça upload novamente |
| HA mostra `unavailable` | Tópico de availability vazio | Reinicie o Pico W para republicar `online` |

---

## 📋 Subscriber Python (para testes)

Para visualizar os dados no terminal sem o HA:

```bash
pip install paho-mqtt
python subscriber.py
```

Saída esperada:
```
[14:32:01] Temp: 24.98°C  Umid: 60.44%  RSSI: -79 dBm  Pub#: 1  Status: ONLINE
[14:32:31] Temp: 24.88°C  Umid: 59.96%  RSSI: -79 dBm  Pub#: 2  Status: ONLINE
```
