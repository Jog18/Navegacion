"""
Interfaz gráfica principal del sistema de navegación robótica.

Muestra la imagen de la cámara con el plano cartesiano superpuesto,
la posición del robot, la trayectoria planeada, el punto objetivo
y los controles para introducir vectores de movimiento.
"""

import sys
import numpy as np
import cv2
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QGroupBox, QGridLayout,
    QStatusBar, QFrame,
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap, QFont

from vision.camera import Camera
from vision.detector import RobotDetector, RobotPose
from control.robot_controller import RobotController, RobotState


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación de navegación robótica."""

    def __init__(self, camera_source=0):
        super().__init__()
        self.setWindowTitle("Navegación Robot Ackermann - Visión por Computadora")
        self.setMinimumSize(900, 650)

        # Componentes del sistema
        self.camera = Camera(source=camera_source)
        self.detector = RobotDetector()
        self.controller = RobotController()

        # Estado actual
        self.current_pose = RobotPose(x=0, y=0, theta=0, detected=False)
        self.current_frame = None

        self._setup_ui()
        self._setup_timer()

        # Intentar abrir la cámara
        try:
            self.camera.open()
            self.statusBar().showMessage("Cámara conectada")
        except RuntimeError:
            self.statusBar().showMessage("Sin cámara - modo simulación")

    def _setup_ui(self):
        """Construye la interfaz gráfica."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # --- Panel izquierdo: Vista de cámara ---
        self.video_label = QLabel()
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: #1a1a2e; border: 2px solid #16213e;")
        main_layout.addWidget(self.video_label, stretch=3)

        # --- Panel derecho: Controles ---
        right_panel = QVBoxLayout()
        main_layout.addLayout(right_panel, stretch=1)

        # Grupo: Estado del robot
        state_group = QGroupBox("Estado del Robot")
        state_layout = QGridLayout()
        state_group.setLayout(state_layout)

        self.lbl_pos_x = QLabel("X: ---")
        self.lbl_pos_y = QLabel("Y: ---")
        self.lbl_theta = QLabel("θ: ---")
        self.lbl_state = QLabel("Estado: IDLE")
        self.lbl_detected = QLabel("Detección: ---")

        font_mono = QFont("Monospace", 10)
        for lbl in [self.lbl_pos_x, self.lbl_pos_y, self.lbl_theta,
                     self.lbl_state, self.lbl_detected]:
            lbl.setFont(font_mono)

        state_layout.addWidget(self.lbl_pos_x, 0, 0)
        state_layout.addWidget(self.lbl_pos_y, 0, 1)
        state_layout.addWidget(self.lbl_theta, 1, 0)
        state_layout.addWidget(self.lbl_state, 1, 1)
        state_layout.addWidget(self.lbl_detected, 2, 0, 1, 2)
        right_panel.addWidget(state_group)

        # Grupo: Vector de movimiento
        cmd_group = QGroupBox("Vector de Movimiento")
        cmd_layout = QGridLayout()
        cmd_group.setLayout(cmd_layout)

        cmd_layout.addWidget(QLabel("Distancia (px):"), 0, 0)
        self.input_distance = QLineEdit("100")
        cmd_layout.addWidget(self.input_distance, 0, 1)

        cmd_layout.addWidget(QLabel("Ángulo (°):"), 1, 0)
        self.input_angle = QLineEdit("0")
        cmd_layout.addWidget(self.input_angle, 1, 1)

        self.btn_send = QPushButton("Enviar Comando")
        self.btn_send.setStyleSheet(
            "QPushButton { background-color: #0f3460; color: white; padding: 8px; "
            "border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #16213e; }"
        )
        self.btn_send.clicked.connect(self._on_send_command)
        cmd_layout.addWidget(self.btn_send, 2, 0, 1, 2)

        self.btn_stop = QPushButton("Detener")
        self.btn_stop.setStyleSheet(
            "QPushButton { background-color: #e94560; color: white; padding: 8px; "
            "border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #c0392b; }"
        )
        self.btn_stop.clicked.connect(self._on_stop)
        cmd_layout.addWidget(self.btn_stop, 3, 0, 1, 2)

        right_panel.addWidget(cmd_group)

        # Grupo: Información de navegación
        nav_group = QGroupBox("Navegación")
        nav_layout = QGridLayout()
        nav_group.setLayout(nav_layout)

        self.lbl_target = QLabel("Objetivo: ---")
        self.lbl_steering = QLabel("Dirección: ---")
        self.lbl_velocity = QLabel("Velocidad: ---")
        self.lbl_cte = QLabel("Error lateral: ---")
        self.lbl_dist_goal = QLabel("Dist. objetivo: ---")

        for lbl in [self.lbl_target, self.lbl_steering, self.lbl_velocity,
                     self.lbl_cte, self.lbl_dist_goal]:
            lbl.setFont(font_mono)

        nav_layout.addWidget(self.lbl_target, 0, 0)
        nav_layout.addWidget(self.lbl_dist_goal, 1, 0)
        nav_layout.addWidget(self.lbl_steering, 2, 0)
        nav_layout.addWidget(self.lbl_velocity, 3, 0)
        nav_layout.addWidget(self.lbl_cte, 4, 0)
        right_panel.addWidget(nav_group)

        right_panel.addStretch()

        # Barra de estado
        self.setStatusBar(QStatusBar())

    def _setup_timer(self):
        """Configura el timer del ciclo de control (30 Hz)."""
        self.timer = QTimer()
        self.timer.timeout.connect(self._loop)
        self.timer.start(33)  # ~30 FPS

    def _loop(self):
        """Ciclo principal: captura → detección → control → visualización."""
        # Capturar frame
        frame = self.camera.read()
        if frame is None:
            # Modo simulación: generar frame gris
            frame = np.zeros((480, 640, 3), dtype=np.uint8) + 40
            cv2.putText(frame, "Sin camara - modo simulacion", (100, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 100), 2)

        self.current_frame = frame.copy()

        # Detectar robot
        self.current_pose = self.detector.detect(frame)

        # Actualizar control si está navegando
        nav_info = self.controller.update(self.current_pose)

        # Dibujar sobre el frame
        display = self._draw_overlay(frame, nav_info)

        # Actualizar UI
        self._update_labels(nav_info)
        self._show_frame(display)

    def _draw_overlay(self, frame, nav_info):
        """
        Dibuja el plano cartesiano, la pose, trayectoria y objetivo sobre el frame.

        Args:
            frame: Imagen BGR de la cámara.
            nav_info: NavigationInfo actual.

        Returns:
            np.ndarray: Frame con anotaciones.
        """
        display = frame.copy()
        h, w = display.shape[:2]

        # --- Plano cartesiano ---
        # Ejes centrados en la imagen
        cx, cy = w // 2, h // 2
        color_axis = (60, 60, 60)
        cv2.line(display, (0, cy), (w, cy), color_axis, 1)  # Eje X
        cv2.line(display, (cx, 0), (cx, h), color_axis, 1)  # Eje Y

        # Marcas de graduación cada 50 píxeles
        for i in range(0, w, 50):
            cv2.line(display, (i, cy - 3), (i, cy + 3), color_axis, 1)
        for j in range(0, h, 50):
            cv2.line(display, (cx - 3, j), (cx + 3, j), color_axis, 1)

        # Etiquetas de ejes
        cv2.putText(display, "X", (w - 20, cy - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 100), 1)
        cv2.putText(display, "Y", (cx + 10, 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (100, 100, 100), 1)

        # --- Posición del robot ---
        if self.current_pose.detected:
            px = int(self.current_pose.x)
            py = int(self.current_pose.y)
            theta = self.current_pose.theta

            # Cuerpo del robot
            cv2.circle(display, (px, py), 10, (0, 255, 255), 2)

            # Flecha de orientación
            arrow_len = 30
            ax = int(px + arrow_len * np.cos(theta))
            ay = int(py + arrow_len * np.sin(theta))
            cv2.arrowedLine(display, (px, py), (ax, ay), (0, 255, 255), 2, tipLength=0.3)

            # Coordenadas
            coord_text = f"({px}, {py})"
            cv2.putText(display, coord_text, (px + 15, py - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)

        # --- Trayectoria ---
        if nav_info.trajectory is not None:
            pts = nav_info.trajectory.astype(np.int32)
            for i in range(len(pts) - 1):
                cv2.line(display, tuple(pts[i]), tuple(pts[i + 1]), (255, 165, 0), 2)

        # --- Punto objetivo ---
        if nav_info.target is not None:
            tx, ty = int(nav_info.target[0]), int(nav_info.target[1])
            cv2.drawMarker(display, (tx, ty), (0, 0, 255), cv2.MARKER_CROSS, 20, 2)
            cv2.putText(display, "TARGET", (tx + 12, ty - 12),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)

        # --- Punto de lookahead ---
        if nav_info.lookahead_point is not None:
            lx, ly = int(nav_info.lookahead_point[0]), int(nav_info.lookahead_point[1])
            cv2.circle(display, (lx, ly), 6, (255, 0, 255), -1)

        # --- Vector de movimiento ---
        if self.current_pose.detected and nav_info.target is not None:
            px = int(self.current_pose.x)
            py = int(self.current_pose.y)
            tx, ty = int(nav_info.target[0]), int(nav_info.target[1])
            cv2.arrowedLine(display, (px, py), (tx, ty), (0, 200, 0), 1,
                            tipLength=0.05, line_type=cv2.LINE_AA)

        return display

    def _update_labels(self, nav_info):
        """Actualiza las etiquetas del panel de información."""
        pose = self.current_pose

        if pose.detected:
            self.lbl_pos_x.setText(f"X: {pose.x:.1f}")
            self.lbl_pos_y.setText(f"Y: {pose.y:.1f}")
            self.lbl_theta.setText(f"θ: {np.rad2deg(pose.theta):.1f}°")
            self.lbl_detected.setText("Detección: OK")
            self.lbl_detected.setStyleSheet("color: #2ecc71;")
        else:
            self.lbl_pos_x.setText("X: ---")
            self.lbl_pos_y.setText("Y: ---")
            self.lbl_theta.setText("θ: ---")
            self.lbl_detected.setText("Detección: NO")
            self.lbl_detected.setStyleSheet("color: #e74c3c;")

        self.lbl_state.setText(f"Estado: {nav_info.state.value.upper()}")

        if nav_info.target is not None:
            self.lbl_target.setText(f"Objetivo: ({nav_info.target[0]:.0f}, {nav_info.target[1]:.0f})")
            self.lbl_dist_goal.setText(f"Dist. objetivo: {nav_info.distance_to_goal:.1f} px")
            self.lbl_steering.setText(f"Dirección: {np.rad2deg(nav_info.steering):.1f}°")
            self.lbl_velocity.setText(f"Velocidad: {nav_info.velocity:.2f}")
            self.lbl_cte.setText(f"Error lateral: {nav_info.cross_track_error:.1f} px")
        else:
            self.lbl_target.setText("Objetivo: ---")
            self.lbl_dist_goal.setText("Dist. objetivo: ---")
            self.lbl_steering.setText("Dirección: ---")
            self.lbl_velocity.setText("Velocidad: ---")
            self.lbl_cte.setText("Error lateral: ---")

    def _show_frame(self, frame):
        """Convierte el frame OpenCV a QPixmap y lo muestra."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(scaled)

    def _on_send_command(self):
        """Callback del botón Enviar Comando."""
        try:
            distance = float(self.input_distance.text())
            angle = float(self.input_angle.text())
        except ValueError:
            self.statusBar().showMessage("Error: Introduce valores numéricos válidos")
            return

        if not self.current_pose.detected:
            self.statusBar().showMessage("Error: Robot no detectado")
            return

        self.controller.set_target(self.current_pose, distance, angle)
        self.statusBar().showMessage(
            f"Comando enviado: distancia={distance:.0f} px, ángulo={angle:.0f}°"
        )

    def _on_stop(self):
        """Callback del botón Detener."""
        self.controller.stop()
        self.statusBar().showMessage("Robot detenido")

    def closeEvent(self, event):
        """Limpieza al cerrar la ventana."""
        self.timer.stop()
        self.camera.release()
        event.accept()
