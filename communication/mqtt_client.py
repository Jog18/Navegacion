"""
Cliente MQTT para comunicación con el ESP32 del robot.

Envía comandos de control (PWM motores y ángulo servo) al ESP32
mediante el protocolo MQTT. El ESP32 se suscribe al topic de comandos
y ejecuta las acciones sobre los motores.

Topics:
    robot/cmd   → Comandos de control (Python → ESP32)
    robot/status ← Estado del robot (ESP32 → Python)
"""

import json
import threading
import paho.mqtt.client as mqtt


class MQTTClient:
    """
    Cliente MQTT para enviar comandos al ESP32 y recibir estado.

    Formato del mensaje en 'robot/cmd':
        {
            "left_pwm": int,        # PWM motor izquierdo [0-255]
            "right_pwm": int,       # PWM motor derecho [0-255]
            "servo": float,         # Ángulo servo dirección (grados)
            "action": str           # "move" | "stop"
        }
    """

    def __init__(self, broker="localhost", port=1883,
                 topic_cmd="robot/cmd", topic_status="robot/status"):
        """
        Args:
            broker: Dirección IP o hostname del broker MQTT.
            port: Puerto del broker MQTT.
            topic_cmd: Topic para enviar comandos al ESP32.
            topic_status: Topic para recibir estado del ESP32.
        """
        self.broker = broker
        self.port = port
        self.topic_cmd = topic_cmd
        self.topic_status = topic_status

        self._connected = False
        self._lock = threading.Lock()
        self._on_status_callback = None

        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

    @property
    def connected(self):
        """Retorna True si está conectado al broker."""
        with self._lock:
            return self._connected

    def set_status_callback(self, callback):
        """
        Registra un callback para recibir mensajes de estado del ESP32.

        Args:
            callback: Función que recibe un dict con el estado.
        """
        self._on_status_callback = callback

    def connect(self):
        """Conecta al broker MQTT en un hilo separado (no bloqueante)."""
        try:
            self._client.connect(self.broker, self.port, keepalive=60)
            self._client.loop_start()
        except Exception as e:
            print(f"[MQTT] Error al conectar: {e}")
            with self._lock:
                self._connected = False

    def disconnect(self):
        """Desconecta del broker MQTT."""
        self.send_stop()
        self._client.loop_stop()
        self._client.disconnect()
        with self._lock:
            self._connected = False

    def send_command(self, left_pwm, right_pwm, servo_angle):
        """
        Envía un comando de movimiento al ESP32.

        Args:
            left_pwm: PWM motor izquierdo [0-255].
            right_pwm: PWM motor derecho [0-255].
            servo_angle: Ángulo del servo de dirección (grados).
        """
        if not self.connected:
            return

        payload = {
            "left_pwm": int(left_pwm),
            "right_pwm": int(right_pwm),
            "servo": round(float(servo_angle), 1),
            "action": "move",
        }
        self._publish(self.topic_cmd, payload)

    def send_stop(self):
        """Envía comando de parada al ESP32."""
        if not self.connected:
            return

        payload = {
            "left_pwm": 0,
            "right_pwm": 0,
            "servo": 90.0,
            "action": "stop",
        }
        self._publish(self.topic_cmd, payload)

    def _publish(self, topic, payload):
        """Publica un mensaje JSON en el topic indicado."""
        try:
            msg = json.dumps(payload)
            self._client.publish(topic, msg, qos=1)
        except Exception as e:
            print(f"[MQTT] Error al publicar: {e}")

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback al conectar con el broker."""
        if rc == 0:
            print(f"[MQTT] Conectado al broker {self.broker}:{self.port}")
            with self._lock:
                self._connected = True
            # Suscribirse al topic de estado del ESP32
            client.subscribe(self.topic_status, qos=1)
        else:
            print(f"[MQTT] Error de conexión, código: {rc}")
            with self._lock:
                self._connected = False

    def _on_disconnect(self, client, userdata, flags, rc, properties=None):
        """Callback al desconectar del broker."""
        print(f"[MQTT] Desconectado (rc={rc})")
        with self._lock:
            self._connected = False

    def _on_message(self, client, userdata, msg):
        """Callback al recibir un mensaje del ESP32."""
        try:
            data = json.loads(msg.payload.decode())
            if self._on_status_callback:
                self._on_status_callback(data)
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            print(f"[MQTT] Error al decodificar mensaje: {e}")
