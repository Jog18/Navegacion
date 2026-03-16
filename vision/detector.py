"""
Módulo de detección del robot.

Detecta el robot en la imagen mediante segmentación de color HSV.
Utiliza dos marcadores de color para determinar posición (x, y) y
orientación (theta) del robot sobre el plano de trabajo.

Esquema de marcadores:
  - Marcador frontal (verde por defecto): indica la dirección del robot.
  - Marcador trasero (azul por defecto): indica la parte posterior.
  - La posición del robot es el punto medio entre ambos marcadores.
  - La orientación es el ángulo del vector trasero → frontal.
"""

import cv2
import numpy as np
from dataclasses import dataclass


@dataclass
class RobotPose:
    """Pose del robot en el plano de trabajo."""
    x: float          # Posición X en píxeles
    y: float          # Posición Y en píxeles
    theta: float      # Orientación en radianes [-pi, pi]
    detected: bool    # True si ambos marcadores fueron detectados


# Rangos HSV por defecto para los marcadores
DEFAULT_FRONT_HSV = {
    "lower": np.array([35, 80, 80]),   # Verde
    "upper": np.array([85, 255, 255]),
}
DEFAULT_REAR_HSV = {
    "lower": np.array([100, 80, 80]),  # Azul
    "upper": np.array([130, 255, 255]),
}


class RobotDetector:
    """Detecta posición y orientación del robot usando marcadores de color."""

    def __init__(self, front_hsv=None, rear_hsv=None, min_area=100):
        """
        Args:
            front_hsv: Dict con 'lower' y 'upper' (np.array) para el marcador frontal.
            rear_hsv: Dict con 'lower' y 'upper' (np.array) para el marcador trasero.
            min_area: Área mínima en píxeles para considerar un contorno válido.
        """
        self.front_hsv = front_hsv or DEFAULT_FRONT_HSV
        self.rear_hsv = rear_hsv or DEFAULT_REAR_HSV
        self.min_area = min_area

    def detect(self, frame):
        """
        Detecta la pose del robot en el frame dado.

        Args:
            frame: Imagen BGR de la cámara cenital.

        Returns:
            RobotPose: Pose detectada del robot.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        front_center = self._find_marker(hsv, self.front_hsv)
        rear_center = self._find_marker(hsv, self.rear_hsv)

        if front_center is None or rear_center is None:
            return RobotPose(x=0, y=0, theta=0, detected=False)

        # Posición = punto medio entre los dos marcadores
        x = (front_center[0] + rear_center[0]) / 2.0
        y = (front_center[1] + rear_center[1]) / 2.0

        # Orientación = ángulo del vector trasero → frontal
        dx = front_center[0] - rear_center[0]
        dy = front_center[1] - rear_center[1]
        theta = np.arctan2(dy, dx)

        return RobotPose(x=x, y=y, theta=theta, detected=True)

    def _find_marker(self, hsv_frame, hsv_range):
        """
        Encuentra el centro del marcador de color más grande.

        Args:
            hsv_frame: Imagen en espacio HSV.
            hsv_range: Dict con 'lower' y 'upper'.

        Returns:
            tuple (cx, cy) o None si no se detecta.
        """
        mask = cv2.inRange(hsv_frame, hsv_range["lower"], hsv_range["upper"])

        # Operaciones morfológicas para limpiar ruido
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return None

        # Seleccionar el contorno más grande que supere el área mínima
        largest = max(contours, key=cv2.contourArea)
        if cv2.contourArea(largest) < self.min_area:
            return None

        M = cv2.moments(largest)
        if M["m00"] == 0:
            return None

        cx = M["m10"] / M["m00"]
        cy = M["m01"] / M["m00"]
        return (cx, cy)

    def get_debug_frame(self, frame):
        """
        Genera una imagen de depuración con las máscaras de detección superpuestas.

        Args:
            frame: Imagen BGR original.

        Returns:
            np.ndarray: Imagen con anotaciones de depuración.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        debug = frame.copy()

        for hsv_range, color, label in [
            (self.front_hsv, (0, 255, 0), "Front"),
            (self.rear_hsv, (255, 0, 0), "Rear"),
        ]:
            mask = cv2.inRange(hsv, hsv_range["lower"], hsv_range["upper"])
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            cv2.drawContours(debug, contours, -1, color, 2)

            center = self._find_marker(hsv, hsv_range)
            if center is not None:
                pt = (int(center[0]), int(center[1]))
                cv2.circle(debug, pt, 8, color, -1)
                cv2.putText(debug, label, (pt[0] + 10, pt[1] - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        return debug
