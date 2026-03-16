"""
Módulo de captura de cámara.

Gestiona la conexión con la cámara superior que observa la zona de trabajo
y proporciona frames para el procesamiento de visión artificial.
"""

import cv2
import numpy as np


class Camera:
    """Interfaz de captura de video desde cámara cenital."""

    def __init__(self, source=0, width=640, height=480):
        """
        Args:
            source: Índice de cámara o ruta de video/imagen.
            width: Ancho deseado del frame en píxeles.
            height: Alto deseado del frame en píxeles.
        """
        self.source = source
        self.width = width
        self.height = height
        self.cap = None

    def open(self):
        """Abre la conexión con la cámara."""
        self.cap = cv2.VideoCapture(self.source)
        if not self.cap.isOpened():
            raise RuntimeError(f"No se pudo abrir la cámara: {self.source}")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

    def read(self):
        """
        Captura un frame de la cámara.

        Returns:
            np.ndarray: Imagen BGR, o None si la lectura falla.
        """
        if self.cap is None:
            return None
        ret, frame = self.cap.read()
        return frame if ret else None

    def release(self):
        """Libera el recurso de cámara."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    @staticmethod
    def load_image(path):
        """
        Carga una imagen estática desde disco.

        Args:
            path: Ruta al archivo de imagen.

        Returns:
            np.ndarray: Imagen BGR.
        """
        img = cv2.imread(path)
        if img is None:
            raise FileNotFoundError(f"No se encontró la imagen: {path}")
        return img
