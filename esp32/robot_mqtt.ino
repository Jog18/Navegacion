/*
 * Robot Ackermann - Control por ESP32 via MQTT
 *
 * Recibe comandos JSON desde el sistema de visión por computadora
 * y controla UN motor DC y el servo de dirección.
 *
 * Topic MQTT de comandos: robot/cmd
 * Formato JSON: {"pwm":150, "servo":90.0, "action":"move"}
 *
 * Topic MQTT de estado: robot/status
 * Formato JSON: {"wifi_rssi":-55, "status":"ok", "uptime_s":120}
 *
 * Conexiones ESP32:
 *   - Motor (tracción): ENA=GPIO 25, IN1=GPIO 26, IN2=GPIO 27
 *   - Servo dirección:  GPIO 13
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
const char* WIFI_SSID     = "HOME-CDD7";
const char* WIFI_PASSWORD = "C552C1813411A8DC";

const char* MQTT_BROKER   = "10.0.0.5";  // IP del broker (la PC)
const int   MQTT_PORT    = 1883;
const char* TOPIC_CMD    = "robot/cmd";
const char* TOPIC_STATUS = "robot/status";

// ===================== PINES MOTOR =====================
const int PIN_ENA = 25;  // PWM motor
const int PIN_IN1 = 26;  // Dirección motor
const int PIN_IN2 = 27;

// ===================== PIN SERVO =====================
const int PIN_SERVO = 13;

// ===================== CANAL PWM ESP32 =====================
const int PWM_CHANNEL    = 0;
const int PWM_FREQ       = 1000;   // 1 kHz
const int PWM_RESOLUTION = 8;      // 8 bits → valores 0-255

// ===================== OBJETOS GLOBALES =====================
WiFiClient    espClient;
PubSubClient  mqttClient(espClient);
Servo         servoDirection;

unsigned long lastStatusTime  = 0;
const unsigned long STATUS_INTERVAL = 2000;  // Enviar estado cada 2 s

// ===================== FUNCIONES MOTOR =====================

void setupMotor() {
    pinMode(PIN_IN1, OUTPUT);
    pinMode(PIN_IN2, OUTPUT);

    // Configurar canal PWM
    ledcAttach(PIN_ENA, PWM_FREQ, PWM_RESOLUTION);

    stopMotor();
}

/**
 * Controla el motor de tracción.
 * @param pwm  Valor PWM: positivo = avance, negativo = retroceso.
 */
void setMotor(int pwm) {
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

void stopMotor() {
    digitalWrite(PIN_IN1, LOW);
    digitalWrite(PIN_IN2, LOW);
    ledcWrite(PIN_ENA, 0);
    servoDirection.write(90);  // Centro
}

// ===================== CALLBACK MQTT =====================

void mqttCallback(char* topic, byte* payload, unsigned int length) {
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, payload, length);

    if (error) {
        Serial.print("[MQTT] Error JSON: ");
        Serial.println(error.c_str());
        return;
    }

    const char* action = doc["action"] | "unknown";

    if (strcmp(action, "stop") == 0) {
        stopMotor();
        Serial.println("[CMD] STOP");
        return;
    }

    if (strcmp(action, "move") == 0) {
        int   pwm        = doc["pwm"]   | 0;
        float servoFloat = doc["servo"] | 90.0f;

        setMotor(pwm);

        int servoAngle = constrain((int)servoFloat, 45, 135);
        servoDirection.write(servoAngle);

        Serial.printf("[CMD] PWM:%d  Servo:%d\n", pwm, servoAngle);
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

// ===================== RECONEXIÓN MQTT =====================

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
    doc["status"]   = "ok";
    doc["wifi_rssi"] = WiFi.RSSI();
    doc["uptime_s"]  = millis() / 1000;

    char buffer[128];
    serializeJson(doc, buffer);
    mqttClient.publish(TOPIC_STATUS, buffer);
}

// ===================== SETUP & LOOP =====================

void setup() {
    Serial.begin(115200);
    Serial.println("\n=== Robot Ackermann 1-Motor - ESP32 MQTT ===");

    setupMotor();

    servoDirection.attach(PIN_SERVO);
    servoDirection.write(90);  // Centro

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
