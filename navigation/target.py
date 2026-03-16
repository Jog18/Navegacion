"""
Módulo de generación de objetivo.

Calcula el punto destino a partir de la pose actual del robot y un
vector de movimiento definido por distancia y ángulo de rotación.
"""

import numpy as np


class TargetGenerator:
    """Genera puntos objetivo a partir de vectores de movimiento."""

    @staticmethod
    def compute_target(x, y, theta, distance, angle_deg):
        """
        Calcula el punto destino dado un vector de movimiento.

        El ángulo de rotación se aplica sobre la orientación actual del robot,
        y luego se proyecta la distancia en esa nueva dirección.

        Args:
            x: Posición X actual del robot.
            y: Posición Y actual del robot.
            theta: Orientación actual del robot en radianes.
            distance: Distancia a recorrer (en las mismas unidades que x, y).
            angle_deg: Ángulo de rotación en grados (positivo = antihorario).

        Returns:
            tuple: (target_x, target_y, target_theta)
        """
        angle_rad = np.deg2rad(angle_deg)
        target_theta = theta + angle_rad

        # Normalizar ángulo a [-pi, pi]
        target_theta = np.arctan2(np.sin(target_theta), np.cos(target_theta))

        target_x = x + distance * np.cos(target_theta)
        target_y = y + distance * np.sin(target_theta)

        return target_x, target_y, target_theta
