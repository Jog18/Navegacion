# Guia Completa - Sistema de Navegacion Robot Ackermann

## Descripcion General

Este proyecto implementa un **sistema de navegacion autonoma** para un robot movil con **cinematica Ackermann** (tipo auto: ruedas delanteras que giran para dirigir). El sistema usa **vision por computadora** con una camara cenital (vista desde arriba) para detectar la posicion y orientacion del robot, calcula trayectorias suaves y envia comandos al robot fisico a traves de un **ESP32 conectado por MQTT**.

### Flujo del sistema

```
Camara cenital → Deteccion (OpenCV) → Pose del robot (x, y, theta)
                                           ↓
                                   Algoritmo Pure Pursuit
                                           ↓
                                   Comandos (PWM + servo)
                                           ↓
                                   MQTT → ESP32 → Motores
```

---

## Requisitos de Hardware

### Robot fisico
- **ESP32** (microcontrolador principal del robot)
- **2 motores DC** con driver puente H (tipo L298N o similar)
- **1 servo** para la direccion (mecanismo Ackermann)
- **2 marcadores de color** pegados al robot:
  - **Marcador frontal: color VERDE** (indica la parte delantera)
  - **Marcador trasero: color AZUL** (indica la parte posterior)
  - Deben ser visibles desde arriba, con colores saturados

### Conexiones del ESP32

| Componente         | Pin ESP32 | Funcion             |
|--------------------|-----------|---------------------|
| Motor izq. ENA     | GPIO 25   | PWM motor izquierdo |
| Motor izq. IN1     | GPIO 26   | Direccion motor izq |
| Motor izq. IN2     | GPIO 27   | Direccion motor izq |
| Motor der. ENB     | GPIO 14   | PWM motor derecho   |
| Motor der. IN3     | GPIO 12   | Direccion motor der |
| Motor der. IN4     | GPIO 13   | Direccion motor der |
| Servo direccion    | GPIO 15   | Control del servo   |

### Infraestructura
- **Camara USB o webcam** montada en posicion cenital (mirando hacia abajo) sobre el area de trabajo
- **Red WiFi** a la que se conecten tanto la PC como el ESP32
- **PC** con Python 3.10+ (Windows, Linux o macOS)

---

## Requisitos de Software

### PC (Python)

```
opencv-python >= 4.8.0
numpy >= 1.24.0
PyQt5 >= 5.15.0
matplotlib >= 3.7.0
paho-mqtt >= 2.0.0
```

### ESP32 (Arduino)

Instalar desde Arduino Library Manager:
- **PubSubClient** (by Nick O'Leary) - cliente MQTT
- **ArduinoJson** (by Benoit Blanchon) - parseo de JSON
- **ESP32Servo** - control de servomotores en ESP32

---

## Instalacion Paso a Paso

### 1. Clonar/descargar el proyecto

```bash
cd ~/Desktop/proyectos/Navegacion
```

### 2. Crear entorno virtual e instalar dependencias Python

```bash
python -m venv venv

# Windows:
venv\Scripts\activate

# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Instalar un broker MQTT

El broker MQTT es el intermediario entre la PC y el ESP32. Opcion recomendada: **Mosquitto**.

**Windows:**
- Descargar desde https://mosquitto.org/download/
- Instalar y verificar que el servicio este corriendo:
  ```bash
  mosquitto -v
  ```

**Linux:**
```bash
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

El broker corre en el **puerto 1883** por defecto.

### 4. Programar el ESP32

1. Abrir `esp32/robot_mqtt.ino` en **Arduino IDE**
2. **Editar estas lineas** con tus datos:
   ```cpp
   const char* WIFI_SSID     = "TU_RED_WIFI";      // Nombre de tu red WiFi
   const char* WIFI_PASSWORD = "TU_PASSWORD";       // Contrasena WiFi
   const char* MQTT_BROKER   = "192.168.1.100";     // IP de tu PC en la red local
   ```
3. Para obtener la IP de tu PC:
   - **Windows:** `ipconfig` en CMD → buscar "IPv4 Address" de tu adaptador WiFi
   - **Linux:** `hostname -I`
4. Seleccionar la placa "ESP32 Dev Module" en Arduino IDE
5. Compilar y subir

### 5. Verificar la conexion MQTT

Puedes probar que el ESP32 se conecta correctamente:

```bash
# En una terminal, suscribirse al topic de estado:
mosquitto_sub -t "robot/status" -v

# Deberia aparecer cada 2 segundos algo como:
# robot/status {"status":"ok","wifi_rssi":-45,"uptime_s":10}
```

---

## Como Ejecutar la Aplicacion

### Modo normal (con camara)

```bash
python main.py
```

Usa la camara por defecto (indice 0).

### Seleccionar otra camara

```bash
python main.py --camera 1
```

### Modo simulacion (sin camara ni robot)

```bash
python main.py --simulate
```

Muestra una ventana gris con el mensaje "Sin camara - modo simulacion". Util para probar la interfaz.

### Con imagen estatica (pruebas de deteccion)

```bash
python main.py --image foto_test.png
```

### Especificar broker MQTT

```bash
python main.py --broker 192.168.1.100
python main.py --broker 192.168.1.100 --port 1883
```

Si no se especifica, usa `localhost:1883`.

---

## Uso de la Interfaz Grafica

La ventana tiene dos paneles:

### Panel izquierdo - Vista de camara
- Muestra el feed de la camara en tiempo real con anotaciones:
  - **Plano cartesiano** (ejes X/Y con marcas cada 50px)
  - **Circulo cyan + flecha**: posicion y orientacion del robot detectado
  - **Linea naranja**: trayectoria planificada
  - **Cruz roja "TARGET"**: punto objetivo
  - **Punto magenta**: punto de lookahead (Pure Pursuit)
  - **Flecha verde**: vector de movimiento

### Panel derecho - Controles

#### Estado del Robot
- Posicion X, Y (pixeles)
- Orientacion theta (grados)
- Estado de deteccion (OK / NO)

#### Vector de Movimiento
- **Distancia (px)**: cuanto debe avanzar el robot (en pixeles de la imagen)
- **Angulo (grados)**: rotacion respecto a la orientacion actual (positivo = antihorario)
- **Boton "Enviar Comando"**: calcula la trayectoria y comienza la navegacion
- **Boton "Detener"**: para el robot inmediatamente

#### Navegacion
- Objetivo actual, distancia restante, angulo de direccion, velocidad, error lateral

#### ESP32 - MQTT
- Campos para IP del broker y puerto
- **Boton "Conectar"**: inicia la conexion MQTT
- Indicador de estado (Conectado/Desconectado)
- Ultimo comando enviado (PWM izq, PWM der, angulo servo)

---

## Estructura del Proyecto

```
Navegacion/
├── main.py                    # Punto de entrada principal
├── requirements.txt           # Dependencias Python
├── esp32/
│   └── robot_mqtt.ino         # Firmware del ESP32 (Arduino)
├── vision/
│   ├── camera.py              # Captura de frames (webcam)
│   └── detector.py            # Deteccion del robot por color HSV
├── navigation/
│   ├── target.py              # Calculo del punto objetivo
│   ├── trajectory.py          # Generacion de trayectorias (Bezier cubica)
│   └── pure_pursuit.py        # Algoritmo de seguimiento Pure Pursuit
├── control/
│   └── robot_controller.py    # Controlador principal + maquina de estados
├── communication/
│   └── mqtt_client.py         # Cliente MQTT (PC ↔ ESP32)
└── ui/
    └── main_window.py         # Interfaz grafica PyQt5
```

---

## Funcionamiento Tecnico Detallado

### 1. Deteccion del Robot (`vision/detector.py`)

El sistema detecta el robot buscando **dos marcadores de color** en la imagen:

- Convierte el frame de BGR a espacio de color **HSV**
- Aplica mascaras de color con rangos definidos:
  - **Verde (frontal):** H=[35-85], S=[80-255], V=[80-255]
  - **Azul (trasero):** H=[100-130], S=[80-255], V=[80-255]
- Limpia ruido con operaciones morfologicas (apertura + cierre)
- Encuentra el contorno mas grande de cada color
- Calcula el centroide con momentos de imagen
- **Posicion del robot** = punto medio entre ambos marcadores
- **Orientacion (theta)** = angulo del vector trasero → frontal (`atan2`)

**Importante:** Si la iluminacion cambia, puede que necesites ajustar los rangos HSV. Puedes crear una instancia de `RobotDetector` con rangos personalizados.

### 2. Generacion de Objetivo (`navigation/target.py`)

Dado un vector de movimiento (distancia + angulo):
- Suma el angulo a la orientacion actual del robot
- Proyecta la distancia en esa nueva direccion
- Retorna `(target_x, target_y, target_theta)`

### 3. Planificacion de Trayectoria (`navigation/trajectory.py`)

Genera una **curva de Bezier cubica** entre la posicion actual y el objetivo:
- 4 puntos de control: P0 (inicio), P1 (tangente inicio), P2 (tangente destino), P3 (destino)
- Los puntos intermedios se alinean con la orientacion, garantizando continuidad
- Esto respeta la restriccion no-holonomica del Ackermann (no puede girar sobre su eje)
- Discretiza la curva en 80 puntos

### 4. Seguimiento Pure Pursuit (`navigation/pure_pursuit.py`)

Algoritmo clasico de seguimiento de trayectoria:
1. Encuentra el punto mas cercano de la trayectoria al robot
2. Busca un **punto de lookahead** a una distancia fija (30px por defecto) adelante
3. Transforma ese punto al marco local del robot
4. Calcula la **curvatura**: `kappa = 2 * local_y / Ld^2`
5. Convierte a angulo de direccion Ackermann: `delta = arctan(L * kappa)`
6. Ajusta la velocidad: mas lento en curvas cerradas (rango [0.4, 1.0])

### 5. Control del Robot (`control/robot_controller.py`)

Maquina de estados:
- **IDLE**: sin objetivo activo
- **NAVIGATING**: siguiendo trayectoria
- **REACHED**: llego al objetivo (tolerancia: 15px)
- **ERROR**: robot no detectado durante navegacion

Conversion a comandos de hardware:
- Angulo del servo = 90° - angulo_de_direccion (invertido)
- PWM diferencial: aplica un factor de 30% segun el angulo de giro
- Rango servo: [45°, 135°] (centro en 90°)

### 6. Comunicacion MQTT (`communication/mqtt_client.py`)

**Topics:**
- `robot/cmd` (PC → ESP32): comandos de control
- `robot/status` (ESP32 → PC): estado del robot

**Formato del comando:**
```json
{
    "left_pwm": 150,
    "right_pwm": 140,
    "servo": 85.0,
    "action": "move"
}
```

**Formato de parada:**
```json
{
    "left_pwm": 0,
    "right_pwm": 0,
    "servo": 90.0,
    "action": "stop"
}
```

---

## Preparacion de los Marcadores del Robot

1. Corta dos cuadrados o circulos de cartulina/papel de **al menos 3x3 cm**
2. Uno **verde puro** (frontal) y otro **azul puro** (trasero)
3. Pegalos en la parte superior del robot, separados entre si
4. Asegurate de que sean visibles desde la camara cenital
5. Evita superficies brillantes que generen reflejos

**Tip:** Si la deteccion falla, puedes usar el metodo `detector.get_debug_frame(frame)` para ver las mascaras de color y ajustar los rangos HSV.

---

## Parametros Ajustables

### En `RobotController` (`control/robot_controller.py`)

| Parametro          | Defecto | Descripcion                                |
|--------------------|---------|--------------------------------------------|
| `wheelbase`        | 50.0    | Distancia entre ejes del robot (px)        |
| `max_steering_deg` | 35.0    | Angulo maximo de giro (grados)             |
| `lookahead`        | 30.0    | Distancia de anticipacion Pure Pursuit (px)|
| `max_velocity_pwm` | 255     | PWM maximo para los motores                |
| `servo_center`     | 90.0    | Angulo central del servo                   |
| `servo_range`      | 45.0    | Rango de giro del servo (± desde centro)   |
| `goal_tolerance`   | 15.0    | Distancia para considerar "llegada" (px)   |

### En `RobotDetector` (`vision/detector.py`)

| Parametro   | Defecto             | Descripcion                              |
|-------------|---------------------|------------------------------------------|
| `front_hsv` | H[35-85] S/V[80+]  | Rango HSV para marcador verde (frontal)  |
| `rear_hsv`  | H[100-130] S/V[80+]| Rango HSV para marcador azul (trasero)   |
| `min_area`  | 100                 | Area minima de contorno para deteccion   |

---

## Solucion de Problemas

### "Robot no detectado"
- Verificar que los marcadores verde y azul son visibles en la camara
- Comprobar iluminacion (evitar sombras y reflejos)
- Ajustar los rangos HSV en `detector.py`

### "Sin camara - modo simulacion"
- Verificar que la camara esta conectada
- Probar con `--camera 1` si tienes multiples camaras
- En Linux, verificar permisos: `sudo chmod 666 /dev/video0`

### MQTT no conecta
- Verificar que Mosquitto esta corriendo: `mosquitto -v`
- Verificar que la IP del broker es correcta
- Comprobar que el firewall permite el puerto 1883
- En la aplicacion, introducir la IP correcta y hacer clic en "Conectar"

### El ESP32 no se conecta al WiFi
- Verificar SSID y contrasena en `robot_mqtt.ino`
- Abrir el monitor serial (115200 baud) para ver mensajes de diagnostico
- Asegurar que el ESP32 esta en la misma red que la PC

### El robot se mueve erraticamente
- Ajustar `wheelbase` para que coincida con el robot real (en pixeles)
- Reducir `max_velocity_pwm` para velocidades mas controladas
- Aumentar `lookahead` para trayectorias mas suaves
- Verificar que los marcadores no se confunden con otros objetos del mismo color

---

## Ciclo de Control (30 Hz)

El timer de la interfaz ejecuta el ciclo principal cada 33ms (~30 FPS):

1. **Capturar frame** de la camara
2. **Detectar robot** (posicion + orientacion via marcadores de color)
3. **Actualizar controlador** (Pure Pursuit si hay objetivo activo)
4. **Enviar comando MQTT** al ESP32 (PWM motores + angulo servo)
5. **Dibujar anotaciones** sobre el frame (trayectoria, objetivo, etc.)
6. **Actualizar interfaz** (labels, indicadores)

Al cerrar la ventana, automaticamente envia comando de parada y desconecta MQTT.
