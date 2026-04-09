/*
 * Control de Motor DC con ESP32
 *
 * Controla dirección y velocidad (PWM) de un motor DC
 * usando un driver tipo puente H (L298N, L293D, TB6612, etc.)
 *
 * Conexiones ESP32:
 *   - IN1 (dirección):  GPIO 1
 *   - IN2 (dirección):  GPIO 3
 *   - ENA (PWM velocidad): GPIO 21
 *
 * Control:
 *   - Enviar velocidad por Serial: valor entre -255 y 255
 *     Positivo = avance, Negativo = retroceso, 0 = frenar
 */

// ===================== PINES =====================
const int PIN_IN1 = 1;   // Dirección motor
const int PIN_IN2 = 3;   // Dirección motor
const int PIN_ENA = 21;  // PWM velocidad

// ===================== PWM ESP32 =====================
const int PWM_FREQ       = 1000;  // 1 kHz
const int PWM_RESOLUTION = 8;     // 8 bits -> 0-255

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
    Serial.println("=== Control Motor DC - ESP32 ===");
    Serial.println("Pines: IN1=GPIO1, IN2=GPIO3, ENA=GPIO21");
    Serial.println("Enviar valor -255 a 255 por Serial");
    Serial.println("  Positivo = Avance");
    Serial.println("  Negativo = Retroceso");
    Serial.println("  0        = Frenar");

    setupMotor();
}

// ===================== LOOP =====================

void loop() {
    if (Serial.available()) {
        String input = Serial.readStringUntil('\n');
        input.trim();

        if (input.length() == 0) return;

        int pwm = input.toInt();
        pwm = constrain(pwm, -255, 255);

        setMotor(pwm);

        // Mostrar estado actual
        if (pwm > 0) {
            Serial.printf("Avance   | PWM: %d\n", pwm);
        } else if (pwm < 0) {
            Serial.printf("Retroceso| PWM: %d\n", -pwm);
        } else {
            Serial.println("Motor detenido");
        }
    }
}
