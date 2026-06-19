# Mini Projeto MQTT – BitDogLab
**Disciplina:** Tecnologias de Comunicação para IoT – IMD0907  
**Hardware:** BitDogLab (Raspberry Pi Pico W)  
**Linguagem:** MicroPython

---

## Arquivos do projeto

| Arquivo | Descrição |
|---|---|
| `main.py` | Código principal (publisher MQTT) |
| `ssd1306.py` | Driver do display OLED (inclua só se necessário) |

---

## Configuração antes de gravar

Abra o `main.py` e edite o bloco de configurações no topo:

```python
WIFI_SSID     = "SEU_WIFI"
WIFI_PASSWORD = "SUA_SENHA"
MQTT_BROKER   = "192.168.X.X"   # IP do notebook com Mosquitto
MQTT_PORT     = 1883
PUBLISH_INTERVAL_S = 5          # segundos entre publicações
```

Para descobrir o IP do seu notebook (Linux/Mac):
```bash
ip a      # ou ifconfig
```

---

## Como gravar na BitDogLab

1. Instale o **Thonny IDE** (thonny.org)
2. Conecte a BitDogLab via USB
3. No Thonny: selecione o interpretador **MicroPython (Raspberry Pi Pico)**
4. Copie `main.py` e `ssd1306.py` para a raiz da placa
5. Renomeie o arquivo principal para `main.py` — ele roda automaticamente ao ligar

> **Rodar sem USB (bateria):** Com o arquivo salvo como `main.py` na placa, basta ligar a bateria que o código inicia sozinho.

---

## Comportamento dos periféricos

### Matriz de LED 5x5 (WS2812)
| Situação | Exibição |
|---|---|
| Conectando ao Wi-Fi | Animação amarela de carregamento |
| Wi-Fi forte (≥ -55 dBm) | Ícone completo (4 barras) — verde |
| Wi-Fi médio (-56 a -65) | 3 barras |
| Wi-Fi fraco (-66 a -75) | 2 barras |
| Wi-Fi muito fraco (< -75) | 1 barra |
| Publicação MQTT bem-sucedida | Flash verde rápido |
| Erro (Wi-Fi/MQTT) | X vermelho |

### LED RGB
| Situação | Cor |
|---|---|
| Wi-Fi conectado (startup) | Verde (pisca 1x) |
| Publicação enviada | Azul (pisca 1x) |
| Erro de conexão | Vermelho (aceso) |

### Display OLED
Exibe continuamente:
- Temperatura simulada (°C)
- Umidade simulada (%)
- Status MQTT (OK / ERR)
- Contador de publicações

---

## Broker Mosquitto (notebook)

Certifique-se de que seu broker está rodando e acessível na rede local:
```bash
# Verificar status
mosquitto -v

# Subscriber para testar (em outro terminal)
mosqumosquitto_sub -h localhost -t "casa/sala/#" -v
```

---

## Tópicos MQTT publicados

| Tópico | Conteúdo | Exemplo |
|---|---|---|
| `casa/sala/temperatura` | float em string | `25.34` |
| `casa/sala/umidade` | float em string | `61.20` |

---

## Substituir simulação por sensor real (DHT11/DHT22)

Substitua a função `read_sensors()` no `main.py`:

```python
import dht
sensor = dht.DHT22(Pin(XX))   # coloque o pino correto

def read_sensors():
    sensor.measure()
    return sensor.temperature(), sensor.humidity()
```

---

## Estrutura MQTT do projeto

```
Publisher (BitDogLab)
       │
       │  MQTT Publish
       ▼
  Broker Mosquitto (Notebook)
       │
       │  MQTT Subscribe
       ▼
  Subscriber (Home Assistant / ThingSpeak / Terminal)
```
