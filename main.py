"""
Sistema de Navegación para Robot Móvil Ackermann con Visión por Computadora.

Punto de entrada principal de la aplicación.
El robot físico es controlado por un ESP32 mediante comunicación MQTT.

Uso:
    python main.py                              # Cámara por defecto
    python main.py --camera 1                   # Cámara específica
    python main.py --image test.png             # Imagen estática (pruebas)
    python main.py --simulate                   # Modo simulación sin cámara
    python main.py --broker 192.168.1.100       # Broker MQTT específico
    python main.py --broker 192.168.1.100 --port 1883  # Broker + puerto

Módulos:
    vision/          - Captura de cámara y detección del robot
    navigation/      - Generación de objetivo, trayectoria y Pure Pursuit
    control/         - Controlador del robot (cinemática Ackermann)
    communication/   - Cliente MQTT para enviar comandos al ESP32
    ui/              - Interfaz gráfica PyQt5
"""

import sys
import argparse
from PyQt5.QtWidgets import QApplication

from ui.main_window import MainWindow


def parse_args():
    parser = argparse.ArgumentParser(
        description="Navegación de robot Ackermann con visión por computadora"
    )
    parser.add_argument(
        "--camera", type=int, default=0,
        help="Índice de la cámara (por defecto: 0)"
    )
    parser.add_argument(
        "--image", type=str, default=None,
        help="Ruta a imagen estática en lugar de cámara"
    )
    parser.add_argument(
        "--simulate", action="store_true",
        help="Modo simulación sin cámara"
    )
    parser.add_argument(
        "--broker", type=str, default="localhost",
        help="Dirección IP del broker MQTT (por defecto: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=1883,
        help="Puerto del broker MQTT (por defecto: 1883)"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Seleccionar fuente de video
    if args.image:
        source = args.image
    elif args.simulate:
        source = -1  # Forzar modo sin cámara
    else:
        source = args.camera

    mqtt_config = {"broker": args.broker, "port": args.port}
    window = MainWindow(camera_source=source, mqtt_config=mqtt_config)
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
