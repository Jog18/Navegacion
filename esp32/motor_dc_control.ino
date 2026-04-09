/*
 * Control de Motor DC + Servo Dirección con ESP32
 *
 * Controla velocidad (PWM) de un motor DC via puente H
 * y dirección con un servomotor.
 *
 * Conexiones ESP32:
 *   - IN1 (dirección motor): GPIO 1
 *   - IN2 (dirección motor): GPIO 3
 *   - ENA (PWM velocidad):   GPIO 21
 *   - Servo dirección:       GPIO 5
 *
 * Control por Serial (formato: pwm,servo):
 *   - pwm:   -255 a 255 (positivo=avance, negativo=retroceso, 0=frenar)
 *   - servo: 45 a 135 grados (90=recto)
 *   Ejemplos: "150,90"  -> avance recto
 *             "-100,60" -> retroceso girando a la izquierda
 *             "0,90"    -> frenar recto
 */

#include <ESP32Servo.h>

// ===================== PINES =====================
const int PIN_IN1   = 1;   // Dirección motor
const int PIN_IN2   = 3;   // Dirección motor
const int PIN_ENA   = 21;  // PWM velocidad
const int PIN_SERVO = 5;   // Servo dirección

// ===================== PWM ESP32 =====================
const int PWM_FREQ       = 1000;  // 1 kHz
const int PWM_RESOLUTION = 8;     // 8 bits -> 0-255

// ===================== SERVO =====================
Servo servoDirection;
const int SERVO_CENTER = 90;  // Ángulo recto
const int SERVO_MIN    = 45;  // Máximo giro a un lado
const int SERVO_MAX    = 135; // Máximo giro al otro lado

// ===================== FUNCIONES MOTOR =====================

void setupMotor() {
    pinMode(PIN_IN1, OUTPUT);
    pinMode(PIN_IN2, OUTPUT);

    // Asignar canal PWM al pin ENA
    ledcAttach(PIN_ENA, PWM_FREQ, PWM_RESOLUTION);

    stopMotor();
}

/**
 * Mueve el motor hacia adelante con la velocidad indicada.
 * @param speed  Valor PWM 0-255.
 */
void motorForward(int speed) {
    digitalWrite(PIN_IN1, HIGH);
    digitalWrite(PIN_IN2, LOW);
    ledcWrite(PIN_ENA, constrain(speed, 0, 255));
}

/**
 * Mueve el motor hacia atrás con la velocidad indicada.
 * @param speed  Valor PWM 0-255.
 */
void motorBackward(int speed) {
    digitalWrite(PIN_IN1, LOW);
    digitalWrite(PIN_IN2, HIGH);
    ledcWrite(PIN_ENA, constrain(speed, 0, 255));
}

/**
 * Frena el motor (ambos pines LOW + PWM a 0).
 */
void stopMotor() {
    digitalWrite(PIN_IN1, LOW);
    digitalWrite(PIN_IN2, LOW);
    ledcWrite(PIN_ENA, 0);
}

/**
 * Establece el ángulo del servo de dirección.
 * @param angle  45-135 grados. 90 = recto.
 */
void setServo(int angle) {
    angle = constrain(angle, SERVO_MIN, SERVO_MAX);
    servoDirection.write(angle);
}

/**
 * Controla el motor con un solo valor.
 * @param pwm  -255 a 255. Positivo=avance, Negativo=retroceso, 0=frenar.
 */
void setMotor(int pwm) {
    if (pwm > 0) {
        motorForward(pwm);
    } else if (pwm < 0) {
        motorBackward(-pwm);
    } else {
        stopMotor();
    }
}

// ===================== SETUP =====================

void setup() {
    Serial.begin(115200);
    Serial.println("=== Control Motor DC + Servo - ESP32 ===");
    Serial.println("Pines: IN1=GPIO1, IN2=GPIO3, ENA=GPIO21, SERVO=GPIO5");
    Serial.println("Formato Serial: pwm,servo");
    Serial.println("  pwm:   -255 a 255 (avance/retroceso/frenar)");
    Serial.println("  servo: 45 a 135   (90 = recto)");
    Serial.println("Ejemplos: 150,90  | -100,60 | 0,90");

    setupMotor();

    servoDirection.attach(PIN_SERVO);
    servoDirection.write(SERVO_CENTER);
}

// ===================== LOOP =====================

void loop() {
    if (Serial.available()) {
        String input = Serial.readStringUntil('\n');
        input.trim();

        if (input.length() == 0) return;

        // Parsear formato: pwm,servo
        int commaIndex = input.indexOf(',');

        int pwm = 0;
        int servoAngle = SERVO_CENTER;

        if (commaIndex > 0) {
            pwm = input.substring(0, commaIndex).toInt();
            servoAngle = input.substring(commaIndex + 1).toInt();
        } else {
            // Si solo envían un número, es solo PWM con servo recto
            pwm = input.toInt();
        }

        pwm = constrain(pwm, -255, 255);
        servoAngle = constrain(servoAngle, SERVO_MIN, SERVO_MAX);

        setMotor(pwm);
        setServo(servoAngle);

        // Mostrar estado actual
        const char* dir = (pwm > 0) ? "Avance" : (pwm < 0) ? "Retroceso" : "Detenido";
        Serial.printf("%s | PWM: %d | Servo: %d°\n", dir, abs(pwm), servoAngle);
    }
}
