/*
 * Control de Motor DC + Servo Dirección con ESP32 via MQTT
 *
 * Recibe comandos JSON por MQTT para controlar velocidad (PWM)
 * de un motor DC y dirección con un servomotor.
 *
 * Conexiones ESP32:
 *   - IN1 (dirección motor): GPIO 1
 *   - IN2 (dirección motor): GPIO 3
 *   - ENA (PWM velocidad):   GPIO 21
 *   - Servo dirección:       GPIO 5
 *
 * Topic MQTT de comandos: robot/cmd
 * Formato JSON:
 *   {"action":"move", "pwm":150, "servo":90}   -> avance recto
 *   {"action":"move", "pwm":-100, "servo":60}   -> retroceso girando izquierda
 *   {"action":"stop"}                            -> frenar y centrar servo
 *
 * Topic MQTT de estado: robot/status
 * Formato JSON: {"status":"ok", "wifi_rssi":-55, "uptime_s":120}
 *
 * Dependencias (instalar desde Arduino Library Manager):
 *   - PubSubClient (by Nick O'Leary)
 *   - ArduinoJson  (by Benoit Blanchon)
 *   - ESP32Servo
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <ESP32Servo.h>

// ===================== CONFIGURACION WiFi / MQTT =====================
const char* WIFI_SSID     = "HOME-CDD7";
const char* WIFI_PASSWORD = "C552C1813411A8DC";

const char* MQTT_BROKER   = "10.0.0.5";  // IP del broker (la PC)
const int   MQTT_PORT     = 1883;
const char* TOPIC_CMD     = "robot/cmd";
const char* TOPIC_STATUS  = "robot/status";

// ===================== PINES MOTOR =====================
const int PIN_IN1   = 1;   // Direccion motor
const int PIN_IN2   = 3;   // Direccion motor
const int PIN_ENA   = 21;  // PWM velocidad

// ===================== PIN SERVO =====================
const int PIN_SERVO = 5;

// ===================== PWM ESP32 =====================
const int PWM_FREQ       = 1000;  // 1 kHz
const int PWM_RESOLUTION = 8;     // 8 bits -> 0-255

// ===================== SERVO =====================
Servo servoDirection;
const int SERVO_CENTER = 90;
const int SERVO_MIN    = 45;
const int SERVO_MAX    = 135;

// ===================== OBJETOS GLOBALES =====================
WiFiClient   espClient;
PubSubClient mqttClient(espClient);

unsigned long lastStatusTime = 0;
const unsigned long STATUS_INTERVAL = 2000;  // Enviar estado cada 2 s

// ===================== FUNCIONES MOTOR =====================

void setupMotor() {
    pinMode(PIN_IN1, OUTPUT);
    pinMode(PIN_IN2, OUTPUT);

    ledcAttach(PIN_ENA, PWM_FREQ, PWM_RESOLUTION);

    stopMotor();
}

void motorForward(int speed) {
    digitalWrite(PIN_IN1, HIGH);
    digitalWrite(PIN_IN2, LOW);
    ledcWrite(PIN_ENA, constrain(speed, 0, 255));
}

void motorBackward(int speed) {
    digitalWrite(PIN_IN1, LOW);
    digitalWrite(PIN_IN2, HIGH);
    ledcWrite(PIN_ENA, constrain(speed, 0, 255));
}

void stopMotor() {
    digitalWrite(PIN_IN1, LOW);
    digitalWrite(PIN_IN2, LOW);
    ledcWrite(PIN_ENA, 0);
    servoDirection.write(SERVO_CENTER);
}

void setServo(int angle) {
    angle = constrain(angle, SERVO_MIN, SERVO_MAX);
    servoDirection.write(angle);
}

void setMotor(int pwm) {
    if (pwm > 0) {
        motorForward(pwm);
    } else if (pwm < 0) {
        motorBackward(-pwm);
    } else {
        stopMotor();
    }
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
        int pwm        = doc["pwm"]   | 0;
        int servoAngle = doc["servo"] | SERVO_CENTER;

        pwm = constrain(pwm, -255, 255);
        servoAngle = constrain(servoAngle, SERVO_MIN, SERVO_MAX);

        setMotor(pwm);
        setServo(servoAngle);

        Serial.printf("[CMD] PWM:%d  Servo:%d\n", pwm, servoAngle);
    }
}

// ===================== CONEXION WiFi =====================

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

// ===================== RECONEXION MQTT =====================

void reconnectMQTT() {
    while (!mqttClient.connected()) {
        Serial.print("Conectando a MQTT...");
        String clientId = "ESP32Motor-" + String(random(0xffff), HEX);

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
    doc["status"]    = "ok";
    doc["wifi_rssi"] = WiFi.RSSI();
    doc["uptime_s"]  = millis() / 1000;

    char buffer[128];
    serializeJson(doc, buffer);
    mqttClient.publish(TOPIC_STATUS, buffer);
}

// ===================== SETUP =====================

void setup() {
    Serial.begin(115200);
    Serial.println("\n=== Control Motor DC + Servo - ESP32 MQTT ===");
    Serial.println("Pines: IN1=GPIO1, IN2=GPIO3, ENA=GPIO21, SERVO=GPIO5");

    setupMotor();

    servoDirection.attach(PIN_SERVO);
    servoDirection.write(SERVO_CENTER);

    setupWiFi();

    mqttClient.setServer(MQTT_BROKER, MQTT_PORT);
    mqttClient.setCallback(mqttCallback);
    mqttClient.setBufferSize(512);
}

// ===================== LOOP =====================

void loop() {
    if (!mqttClient.connected()) {
        reconnectMQTT();
    }
    mqttClient.loop();

    // Enviar estado periodicamente
    if (millis() - lastStatusTime > STATUS_INTERVAL) {
        sendStatus();
        lastStatusTime = millis();
    }
}
