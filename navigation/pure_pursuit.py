"""
Módulo de seguimiento de trayectoria - Pure Pursuit.

Implementa el algoritmo Pure Pursuit adaptado para robots con cinemática
Ackermann. El algoritmo selecciona un punto de anticipación (lookahead)
sobre la trayectoria y calcula el ángulo de dirección necesario para
alcanzarlo siguiendo un arco circular.
"""

import numpy as np


class PurePursuitTracker:
    """
    Seguimiento de trayectoria mediante Pure Pursuit para robots Ackermann.

    El modelo cinemático Ackermann relaciona el ángulo de dirección (delta)
    con el radio de giro: delta = arctan(L / R), donde L es la distancia
    entre ejes y R es el radio de giro.
    """

    def __init__(self, lookahead_distance=30.0, wheelbase=50.0, max_steering=np.deg2rad(35)):
        """
        Args:
            lookahead_distance: Distancia de anticipación en píxeles.
            wheelbase: Distancia entre ejes del robot en píxeles (L).
            max_steering: Ángulo máximo de dirección en radianes.
        """
        self.lookahead_distance = lookahead_distance
        self.wheelbase = wheelbase
        self.max_steering = max_steering

    def compute_control(self, robot_x, robot_y, robot_theta, trajectory):
        """
        Calcula los comandos de control para seguir la trayectoria.

        Args:
            robot_x, robot_y: Posición actual del robot.
            robot_theta: Orientación actual del robot en radianes.
            trajectory: np.ndarray de forma (N, 2) con puntos [x, y].

        Returns:
            dict con:
                - steering: Ángulo de dirección en radianes.
                - velocity: Velocidad lineal sugerida.
                - lookahead_point: Punto de anticipación (x, y).
                - target_index: Índice del punto objetivo en la trayectoria.
                - cross_track_error: Error lateral respecto a la trayectoria.
                - reached: True si el robot llegó al final de la trayectoria.
        """
        # Encontrar el punto más cercano en la trayectoria
        diffs = trajectory - np.array([robot_x, robot_y])
        distances = np.linalg.norm(diffs, axis=1)
        nearest_idx = np.argmin(distances)
        cross_track_error = distances[nearest_idx]

        # Buscar el punto de lookahead a partir del más cercano
        lookahead_point = None
        target_idx = nearest_idx
        for i in range(nearest_idx, len(trajectory)):
            if distances[i] >= self.lookahead_distance:
                lookahead_point = trajectory[i]
                target_idx = i
                break

        # Si no se encontró, usar el último punto de la trayectoria
        if lookahead_point is None:
            lookahead_point = trajectory[-1]
            target_idx = len(trajectory) - 1

        # Verificar si se alcanzó el destino
        dist_to_goal = np.linalg.norm(trajectory[-1] - np.array([robot_x, robot_y]))
        reached = dist_to_goal < self.lookahead_distance * 0.5

        # Transformar el punto de lookahead al sistema de referencia del robot
        dx = lookahead_point[0] - robot_x
        dy = lookahead_point[1] - robot_y

        # Coordenadas en el marco local del robot
        local_x = dx * np.cos(robot_theta) + dy * np.sin(robot_theta)
        local_y = -dx * np.sin(robot_theta) + dy * np.cos(robot_theta)

        # Curvatura: kappa = 2 * local_y / L_d^2
        ld_sq = local_x ** 2 + local_y ** 2
        if ld_sq < 1e-6:
            steering = 0.0
        else:
            curvature = 2.0 * local_y / ld_sq
            # Ángulo de dirección Ackermann: delta = arctan(L * kappa)
            steering = np.arctan(self.wheelbase * curvature)

        # Saturar el ángulo de dirección
        steering = np.clip(steering, -self.max_steering, self.max_steering)

        # Velocidad proporcional al inverso de la curvatura (más lento en curvas)
        abs_steering = abs(steering)
        velocity = self._compute_velocity(abs_steering)

        return {
            "steering": steering,
            "velocity": velocity,
            "lookahead_point": lookahead_point,
            "target_index": target_idx,
            "cross_track_error": cross_track_error,
            "reached": reached,
        }

    def _compute_velocity(self, abs_steering):
        """
        Calcula la velocidad en función del ángulo de dirección.

        Velocidad alta en rectas, baja en curvas cerradas.

        Args:
            abs_steering: Valor absoluto del ángulo de dirección.

        Returns:
            float: Velocidad lineal normalizada [0, 1].
        """
        # Relación lineal inversa entre dirección y velocidad
        ratio = abs_steering / self.max_steering
        velocity = 1.0 - 0.6 * ratio  # Rango: [0.4, 1.0]
        return max(0.2, velocity)
