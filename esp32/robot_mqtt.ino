/*
 * Robot Ackermann - Control por ESP32 via MQTT
 *
 * Recibe comandos JSON desde el sistema de visión por computadora
 * y controla los motores DC y el servo de dirección.
 *
 * Topic MQTT de comandos: robot/cmd
 * Formato JSON: {"left_pwm":150, "right_pwm":150, "servo":90.0, "action":"move"}
 *
 * Topic MQTT de estado: robot/status
 * Formato JSON: {"battery":12.1, "status":"ok"}
 *
 * Conexiones ESP32:
 *   - Motor izquierdo:  ENA=GPIO 25, IN1=GPIO 26, IN2=GPIO 27
 *   - Motor derecho:    ENB=GPIO 14, IN3=GPIO 12, IN4=GPIO 13
 *   - Servo dirección:  GPIO 15
 *
 * Dependencias (instalar desde Arduino Library Manager):
 *   - PubSubClient (by Nick O'Leary)
 *   - ArduinoJson (by Benoit Blanchon)
 *   - ESP32Servo
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// ===================== CONFIGURACIÓN WiFi =====================
const char* WIFI_SSID     = "TU_RED_WIFI";
const char* WIFI_PASSWORD = "TU_PASSWORD";

// ===================== CONFIGURACIÓN MQTT =====================
const char* MQTT_BROKER = "192.168.1.100";  // IP del broker (la PC)
const int   MQTT_PORT   = 1883;
const char* TOPIC_CMD    = "robot/cmd";
const char* TOPIC_STATUS = "robot/status";

// ===================== PINES MOTOR IZQUIERDO =====================
const int PIN_ENA = 25;  // PWM motor izquierdo
const int PIN_IN1 = 26;  // Dirección motor izquierdo
const int PIN_IN2 = 27;

// ===================== PINES MOTOR DERECHO =====================
const int PIN_ENB = 14;  // PWM motor derecho
const int PIN_IN3 = 12;  // Dirección motor derecho
const int PIN_IN4 = 13;

// ===================== PIN SERVO =====================
const int PIN_SERVO = 15;

// ===================== CANALES PWM ESP32 =====================
const int PWM_CHANNEL_LEFT  = 0;
const int PWM_CHANNEL_RIGHT = 1;
const int PWM_FREQ = 1000;    // 1 kHz
const int PWM_RESOLUTION = 8; // 8 bits (0-255)

// ===================== OBJETOS GLOBALES =====================
WiFiClient espClient;
PubSubClient mqttClient(espClient);
Servo servoDirection;

unsigned long lastStatusTime = 0;
const unsigned long STATUS_INTERVAL = 2000; // Enviar estado cada 2s

// ===================== FUNCIONES MOTOR =====================

void setupMotors() {
    pinMode(PIN_IN1, OUTPUT);
    pinMode(PIN_IN2, OUTPUT);
    pinMode(PIN_IN3, OUTPUT);
    pinMode(PIN_IN4, OUTPUT);

    // Configurar canales PWM en ESP32
    ledcAttach(PIN_ENA, PWM_FREQ, PWM_RESOLUTION);
    ledcAttach(PIN_ENB, PWM_FREQ, PWM_RESOLUTION);

    stopMotors();
}

void setMotorLeft(int pwm) {
    if (pwm >= 0) {
        digitalWrite(PIN_IN1, HIGH);
        digitalWrite(PIN_IN2, LOW);
    } else {
        digitalWrite(PIN_IN1, LOW);
        digitalWrite(PIN_IN2, HIGH);
        pwm = -pwm;
    }
    pwm = constrain(pwm, 0, 255);
    ledcWrite(PIN_ENA, pwm);
}

void setMotorRight(int pwm) {
    if (pwm >= 0) {
        digitalWrite(PIN_IN3, HIGH);
        digitalWrite(PIN_IN4, LOW);
    } else {
        digitalWrite(PIN_IN3, LOW);
        digitalWrite(PIN_IN4, HIGH);
        pwm = -pwm;
    }
    pwm = constrain(pwm, 0, 255);
    ledcWrite(PIN_ENB, pwm);
}

void stopMotors() {
    digitalWrite(PIN_IN1, LOW);
    digitalWrite(PIN_IN2, LOW);
    digitalWrite(PIN_IN3, LOW);
    digitalWrite(PIN_IN4, LOW);
    ledcWrite(PIN_ENA, 0);
    ledcWrite(PIN_ENB, 0);
    servoDirection.write(90); // Centro
}

// ===================== CALLBACK MQTT =====================

void mqttCallback(char* topic, byte* payload, unsigned int length) {
    // Parsear JSON
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, payload, length);

    if (error) {
        Serial.print("[MQTT] Error JSON: ");
        Serial.println(error.c_str());
        return;
    }

    const char* action = doc["action"] | "unknown";

    if (strcmp(action, "stop") == 0) {
        stopMotors();
        Serial.println("[CMD] STOP");
        return;
    }

    if (strcmp(action, "move") == 0) {
        int leftPwm  = doc["left_pwm"]  | 0;
        int rightPwm = doc["right_pwm"] | 0;
        float servo  = doc["servo"]     | 90.0;

        setMotorLeft(leftPwm);
        setMotorRight(rightPwm);

        int servoAngle = constrain((int)servo, 45, 135);
        servoDirection.write(servoAngle);

        Serial.printf("[CMD] L:%d R:%d S:%d\n", leftPwm, rightPwm, servoAngle);
    }
}

// ===================== CONEXIÓN WiFi =====================

void setupWiFi() {
    Serial.printf("Conectando a WiFi: %s", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }

    Serial.println();
    Serial.print("WiFi conectado. IP: ");
    Serial.println(WiFi.localIP());
}

// ===================== CONEXIÓN MQTT =====================

void reconnectMQTT() {
    while (!mqttClient.connected()) {
        Serial.print("Conectando a MQTT...");
        String clientId = "ESP32Robot-" + String(random(0xffff), HEX);

        if (mqttClient.connect(clientId.c_str())) {
            Serial.println(" conectado!");
            mqttClient.subscribe(TOPIC_CMD, 1);
        } else {
            Serial.printf(" error (rc=%d). Reintentando en 3s...\n",
                          mqttClient.state());
            delay(3000);
        }
    }
}

// ===================== ENVIAR ESTADO =====================

void sendStatus() {
    JsonDocument doc;
    doc["status"] = "ok";
    doc["wifi_rssi"] = WiFi.RSSI();
    doc["uptime_s"] = millis() / 1000;

    char buffer[128];
    serializeJson(doc, buffer);
    mqttClient.publish(TOPIC_STATUS, buffer);
}

// ===================== SETUP & LOOP =====================

void setup() {
    Serial.begin(115200);
    Serial.println("\n=== Robot Ackermann - ESP32 MQTT ===");

    setupMotors();

    servoDirection.attach(PIN_SERVO);
    servoDirection.write(90); // Centro

    setupWiFi();

    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);
    mqttClient.setBufferSize(512);
}

void loop() {
    if (!mqttClient.connected()) {
        reconnectMQTT();
    }
    mqttClient.loop();

    // Enviar estado periódicamente
    if (millis() - lastStatusTime > STATUS_INTERVAL) {
        sendStatus();
        lastStatusTime = millis();
    }
}
