import serial
import paho.mqtt.client as mqtt
import re
import json

# Configuration UART
UART_PORT = "/dev/serial0"
UART_BAUDRATE = 1200
UART_BYTE_SIZE = serial.SEVENBITS
UART_PARITY = serial.PARITY_EVEN
UART_STOP_BITS = serial.STOPBITS_ONE
# Configuration MQTT
MQTT_BROKER = "192.168.x.xx"         # ou l'IP du broker
MQTT_PORT = 1883
MQTT_TOPIC = "home/power/data"
MQTT_USER = "xxx"
MQTT_PWD = "xxx"
# Initialisation UART
ser = serial.Serial(
    port="/dev/serial0",
    baudrate=1200,
    bytesize=serial.SEVENBITS,
    parity=serial.PARITY_EVEN,
    stopbits=serial.STOPBITS_ONE,
    timeout=1
)
# --- Callback de connexion ---
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[MQTT] ✅ Connexion établie avec succès")
    else:
        print(f"[MQTT] ❌ Erreur de connexion (rc={rc})")

# --- Callback de déconnexion ---
def on_disconnect(client, userdata, rc):
    print(f"[MQTT] 🔌 Déconnecté (rc={rc})")
# Initialisation MQTT
client = mqtt.Client(client_id="rasp1")
client.username_pw_set(MQTT_USER, MQTT_PWD)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_start()
print("🟢 Lecture UART & envoi MQTT lancé...")

try:
    data = {}
    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode("utf-8").strip()
            if line.startswith("PAPP"):
                match = re.match(r"PAPP\s+(\d+)", line)
                if match:
                    data["PAPP"] = int(match.group(1))

            elif line.startswith("IINST"):
                match = re.match(r"IINST\s+(\d+)", line)
                if match:
                    data["IINST"] = int(match.group(1))

            elif line.startswith("HCHC"):
                match = re.match(r"HCHC\s+(\d+)", line)
                if match:
                    data["HCHC"] = int(match.group(1))
            elif line.startswith("HCHP"):
                match = re.match(r"HCHP\s+(\d+)", line)
                if match:
                    data["HCHP"] = int(match.group(1))
                # Envoie quand tu as les 3 (par exemple)
            elif line.startswith("PTEC"):
                match = re.match(r"PTEC\s+([a-zA-Z]+)", line)
                if match:
                    data["PTEC"] = match.group(1)
                # Envoie quand tu as les 3 (par exemple)
            if "PAPP" in data and "IINST" in data and "HCHC" in data and "HCHP" in data and "PTEC" in data:
                payload = json.dumps(data)
                result = client.publish(MQTT_TOPIC, payload=payload, qos=1)
                status = result[0]
                data.clear()
                if status == 0:
                    print(f"[MQTT] Envoyé : {payload}")
                else:
                    print(f"[MQTT] Échec d'envoi (code: {status})")
                    
except KeyboardInterrupt:
    print("🛑 Arrêt du script.")
finally:
    ser.close()
    client.loop_stop()
    client.disconnect()
