"""
Módulo de control del robot.

Integra la detección visual, la generación de objetivos, la planeación
de trayectoria y el algoritmo de seguimiento Pure Pursuit en un ciclo
de control cerrado.

Adaptado para un robot con UN motor de tracción y un servo de dirección
(configuración Ackermann simplificada).
"""

import numpy as np
from dataclasses import dataclass, field
from enum import Enum

from vision.detector import RobotPose
from navigation.target import TargetGenerator
from navigation.trajectory import TrajectoryPlanner
from navigation.pure_pursuit import PurePursuitTracker


class RobotState(Enum):
    """Estados del robot en la máquina de estados de control."""
    IDLE = "idle"
    NAVIGATING = "navigating"
    REACHED = "reached"
    ERROR = "error"


@dataclass
class ControlCommand:
    """Comando de control enviado al robot (un motor + servo)."""
    steering_angle: float = 0.0    # Ángulo de dirección (rad)
    velocity:       float = 0.0    # Velocidad lineal normalizada [0, 1]
    pwm:            int   = 0      # Señal PWM motor de tracción [0-255]
    servo_angle:    float = 90.0   # Ángulo del servo de dirección (grados)


@dataclass
class NavigationInfo:
    """Información de estado durante la navegación."""
    state: RobotState = RobotState.IDLE
    pose: RobotPose = None
    target: tuple = None           # (x, y)
    trajectory: np.ndarray = None
    lookahead_point: tuple = None
    steering: float = 0.0
    velocity: float = 0.0
    cross_track_error: float = 0.0
    distance_to_goal: float = 0.0


class RobotController:
    """
    Controlador principal del robot Ackermann con un solo motor de tracción.

    Ciclo de control:
    1. Obtener pose del robot (visión).
    2. Si hay objetivo activo, calcular control Pure Pursuit.
    3. Convertir a comandos de actuador (PWM único + ángulo servo).
    """

    def __init__(self, wheelbase=50.0, max_steering_deg=35.0,
                 lookahead=30.0, max_velocity_pwm=255,
                 servo_center=90.0, servo_range=45.0):
        """
        Args:
            wheelbase: Distancia entre ejes en píxeles.
            max_steering_deg: Ángulo máximo de dirección en grados.
            lookahead: Distancia de anticipación Pure Pursuit en píxeles.
            max_velocity_pwm: Valor PWM máximo para el motor.
            servo_center: Ángulo central del servo de dirección.
            servo_range: Rango de giro del servo (±grados desde centro).
        """
        self.wheelbase = wheelbase
        self.max_steering_rad = np.deg2rad(max_steering_deg)
        self.max_velocity_pwm = max_velocity_pwm
        self.servo_center = servo_center
        self.servo_range = servo_range

        self.planner = TrajectoryPlanner(num_points=80)
        self.tracker = PurePursuitTracker(
            lookahead_distance=lookahead,
            wheelbase=wheelbase,
            max_steering=self.max_steering_rad,
        )
        self.target_gen = TargetGenerator()

        # Estado interno
        self.state = RobotState.IDLE
        self.target = None             # (x, y, theta)
        self.trajectory = None         # np.ndarray (N, 2)
        self.goal_tolerance = 15.0     # Tolerancia de llegada en píxeles

    def set_target(self, pose, distance, angle_deg):
        """
        Configura un nuevo objetivo de navegación.

        Args:
            pose: RobotPose actual.
            distance: Distancia a recorrer.
            angle_deg: Ángulo de rotación en grados.
        """
        if not pose.detected:
            self.state = RobotState.ERROR
            return

        tx, ty, ttheta = self.target_gen.compute_target(
            pose.x, pose.y, pose.theta, distance, angle_deg
        )
        self.target = (tx, ty, ttheta)
        self.trajectory = self.planner.plan(
            pose.x, pose.y, pose.theta, tx, ty, ttheta
        )
        self.state = RobotState.NAVIGATING

    def update(self, pose):
        """
        Ejecuta un paso del ciclo de control.

        Args:
            pose: RobotPose actual detectada por visión.

        Returns:
            NavigationInfo: Información completa del estado de navegación.
        """
        info = NavigationInfo(state=self.state, pose=pose)

        if self.state != RobotState.NAVIGATING:
            return info

        if not pose.detected:
            info.state = RobotState.ERROR
            return info

        info.target = (self.target[0], self.target[1])
        info.trajectory = self.trajectory

        # Distancia al objetivo
        dist_to_goal = np.hypot(self.target[0] - pose.x, self.target[1] - pose.y)
        info.distance_to_goal = dist_to_goal

        # Verificar llegada
        if dist_to_goal < self.goal_tolerance:
            self.state = RobotState.REACHED
            info.state = RobotState.REACHED
            return info

        # Calcular control Pure Pursuit
        result = self.tracker.compute_control(
            pose.x, pose.y, pose.theta, self.trajectory
        )

        info.steering = result["steering"]
        info.velocity = result["velocity"]
        info.cross_track_error = result["cross_track_error"]
        info.lookahead_point = tuple(result["lookahead_point"])

        if result["reached"]:
            self.state = RobotState.REACHED
            info.state = RobotState.REACHED

        return info

    def compute_command(self, info):
        """
        Convierte la información de navegación en un comando de actuadores.

        Args:
            info: NavigationInfo del paso actual.

        Returns:
            ControlCommand: Comando listo para enviar al hardware.
        """
        cmd = ControlCommand()

        if info.state != RobotState.NAVIGATING:
            return cmd  # Comando de parada (todo en cero)

        # --- Servo de dirección ---
        steering_deg  = np.rad2deg(info.steering)
        # Invertido según la convención mecánica del servo
        servo_angle   = self.servo_center - steering_deg
        cmd.servo_angle = float(np.clip(
            servo_angle,
            self.servo_center - self.servo_range,
            self.servo_center + self.servo_range,
        ))

        # --- Motor de tracción (PWM único) ---
        cmd.pwm      = int(np.clip(
            info.velocity * self.max_velocity_pwm,
            0,
            self.max_velocity_pwm,
        ))
        cmd.velocity        = info.velocity
        cmd.steering_angle  = info.steering

        return cmd

    def stop(self):
        """Detiene la navegación y reinicia el estado."""
        self.state = RobotState.IDLE
        self.target = None
        self.trajectory = None
