"""
Módulo de planeación de trayectoria.

Genera trayectorias suaves entre la posición actual del robot y el punto
destino, compatibles con la cinemática Ackermann (sin giros sobre su eje).
"""

import numpy as np


class TrajectoryPlanner:
    """Genera trayectorias suaves para robots con configuración Ackermann."""

    def __init__(self, num_points=50):
        """
        Args:
            num_points: Número de puntos de la trayectoria discretizada.
        """
        self.num_points = num_points

    def plan(self, start_x, start_y, start_theta, goal_x, goal_y, goal_theta=None):
        """
        Genera una trayectoria suave usando curvas de Bézier cúbicas.

        Las curvas de Bézier garantizan continuidad en la dirección,
        lo cual es compatible con la restricción no-holonómica de Ackermann.

        Args:
            start_x, start_y: Posición inicial.
            start_theta: Orientación inicial en radianes.
            goal_x, goal_y: Posición objetivo.
            goal_theta: Orientación objetivo (opcional, se calcula si es None).

        Returns:
            np.ndarray: Array de forma (N, 2) con los puntos [x, y] de la trayectoria.
        """
        if goal_theta is None:
            goal_theta = np.arctan2(goal_y - start_y, goal_x - start_x)

        # Distancia entre inicio y destino para escalar puntos de control
        dist = np.hypot(goal_x - start_x, goal_y - start_y)
        offset = dist / 3.0  # Factor de curvatura

        # Puntos de control de la curva de Bézier cúbica
        P0 = np.array([start_x, start_y])
        P1 = P0 + offset * np.array([np.cos(start_theta), np.sin(start_theta)])
        P3 = np.array([goal_x, goal_y])
        P2 = P3 - offset * np.array([np.cos(goal_theta), np.sin(goal_theta)])

        # Evaluación paramétrica
        t = np.linspace(0, 1, self.num_points).reshape(-1, 1)
        trajectory = (
            (1 - t) ** 3 * P0
            + 3 * (1 - t) ** 2 * t * P1
            + 3 * (1 - t) * t ** 2 * P2
            + t ** 3 * P3
        )

        return trajectory

    def plan_straight(self, start_x, start_y, goal_x, goal_y):
        """
        Genera una trayectoria en línea recta (caso simple).

        Args:
            start_x, start_y: Posición inicial.
            goal_x, goal_y: Posición objetivo.

        Returns:
            np.ndarray: Array de forma (N, 2) con los puntos [x, y].
        """
        t = np.linspace(0, 1, self.num_points).reshape(-1, 1)
        start = np.array([start_x, start_y])
        goal = np.array([goal_x, goal_y])
        return start + t * (goal - start)
