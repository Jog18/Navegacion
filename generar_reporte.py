"""Genera el reporte PDF de documentacion del proyecto."""
from fpdf import FPDF


class ReportePDF(FPDF):
    def __init__(self):
        super().__init__()

    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 5, "Sistema de Navegacion Autonoma - Robot Ackermann", align="R")
        self.ln(3)
        self.set_draw_color(0, 120, 200)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")

    def titulo_seccion(self, num, titulo):
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(0, 80, 160)
        self.cell(0, 7, f"{num}. {titulo}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(0, 120, 200)
        self.line(10, self.get_y(), 80, self.get_y())
        self.ln(2)

    def subtitulo(self, texto):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(40, 40, 40)
        self.cell(0, 6, texto, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def parrafo(self, texto):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 4.5, texto)
        self.ln(1.5)

    def item(self, texto):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(30, 30, 30)
        self.cell(5, 4.5, "-")
        self.multi_cell(0, 4.5, texto)
        self.ln(0.5)

    def tabla(self, encabezados, filas, anchos=None):
        if anchos is None:
            anchos = [190 / len(encabezados)] * len(encabezados)
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(0, 80, 160)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(encabezados):
            self.cell(anchos[i], 5.5, h, border=1, fill=True, align="C")
        self.ln()
        self.set_font("Helvetica", "", 8)
        self.set_text_color(30, 30, 30)
        fill = False
        for fila in filas:
            self.set_fill_color(235, 245, 255) if fill else self.set_fill_color(255, 255, 255)
            for i, c in enumerate(fila):
                self.cell(anchos[i], 5, c, border=1, fill=True, align="C")
            self.ln()
            fill = not fill
        self.ln(2)


def generar():
    pdf = ReportePDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=18)

    pdf.add_page()

    # Titulo principal
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(0, 60, 130)
    pdf.ln(5)
    pdf.cell(0, 10, "Sistema de Navegacion Autonoma", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(0, 100, 180)
    pdf.cell(0, 8, "Robot Ackermann con Vision por Computadora", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "Documentacion Tecnica del Proyecto", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "Marzo 2026", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)

    # 1. Introduccion
    pdf.titulo_seccion("1", "Introduccion")
    pdf.parrafo(
        "Este proyecto implementa un sistema completo de navegacion autonoma para un robot "
        "con cinematica Ackermann (tipo automovil). El sistema integra vision por computadora, "
        "planificacion de trayectorias, algoritmos de seguimiento de caminos y comunicacion "
        "inalambrica para controlar un robot fisico basado en ESP32."
    )
    pdf.parrafo(
        "El robot opera dentro de un espacio de trabajo observado por una camara cenital (vista superior). "
        "Un sistema de procesamiento en PC detecta la posicion y orientacion del robot mediante "
        "marcadores de color, calcula la trayectoria optima hacia un objetivo y envia comandos "
        "de control al robot a traves del protocolo MQTT a una frecuencia de 30 Hz."
    )

    # 2. Arquitectura
    pdf.titulo_seccion("2", "Arquitectura del Sistema")
    pdf.parrafo(
        "El sistema sigue una arquitectura modular organizada en cinco componentes principales "
        "que forman un ciclo de control cerrado:"
    )

    pdf.tabla(
        ["Modulo", "Funcion Principal", "Tecnologia"],
        [
            ["vision/", "Captura de camara y deteccion del robot", "OpenCV, NumPy"],
            ["navigation/", "Generacion de objetivos y trayectorias", "Bezier, Pure Pursuit"],
            ["control/", "Maquina de estados y conversion a comandos", "Python"],
            ["communication/", "Comunicacion MQTT con ESP32", "paho-mqtt"],
            ["ui/", "Interfaz grafica con visualizacion en tiempo real", "PyQt5"],
            ["esp32/", "Firmware del robot (motor y servo)", "Arduino/C++"],
        ],
        [30, 75, 85],
    )

    pdf.subtitulo("Flujo de Control (30 Hz)")
    pdf.parrafo(
        "1) La camara captura un frame. "
        "2) El detector identifica los marcadores verde (frente) y azul (trasero) del robot "
        "mediante segmentacion HSV, obteniendo posicion (x, y) y orientacion (theta). "
        "3) El controlador ejecuta el algoritmo Pure Pursuit sobre la trayectoria Bezier planificada. "
        "4) Se calculan los comandos de actuacion (PWM del motor y angulo del servo). "
        "5) Los comandos se envian por MQTT al ESP32 en formato JSON. "
        "6) La interfaz grafica muestra la visualizacion en tiempo real."
    )

    # 3. Vision
    pdf.titulo_seccion("3", "Modulo de Vision")
    pdf.parrafo(
        "La deteccion del robot se realiza mediante segmentacion por color en el espacio HSV. "
        "El robot porta dos marcadores de al menos 3x3 cm:"
    )

    pdf.tabla(
        ["Marcador", "Color", "Rango H", "Rango S", "Rango V"],
        [
            ["Frontal", "Verde", "35-85", "80-255", "80-255"],
            ["Trasero", "Azul", "100-130", "80-255", "80-255"],
        ],
        [30, 25, 40, 45, 50],
    )

    pdf.parrafo(
        "El proceso incluye: conversion BGR a HSV, creacion de mascaras binarias, operaciones "
        "morfologicas de apertura y cierre para eliminar ruido, deteccion del contorno de mayor "
        "area para cada color, y calculo de centroides mediante momentos de imagen. "
        "La posicion del robot es el punto medio entre ambos centroides, y la orientacion se "
        "obtiene con atan2 del vector frontal-trasero."
    )

    # 4. Navegacion
    pdf.titulo_seccion("4", "Navegacion y Planificacion de Trayectorias")

    pdf.subtitulo("4.1 Generacion de Objetivos")
    pdf.parrafo(
        "El usuario define un vector de movimiento (distancia en pixeles y angulo en grados) "
        "desde la interfaz grafica. El modulo TargetGenerator proyecta este vector desde la pose "
        "actual del robot para calcular la posicion y orientacion objetivo."
    )

    pdf.subtitulo("4.2 Trayectorias Bezier Cubicas")
    pdf.parrafo(
        "Se genera una curva Bezier cubica con 80 puntos interpolados. Los puntos de control "
        "se calculan como: P0=inicio, P1=inicio + (d/3)*direccion_inicio, "
        "P2=meta - (d/3)*direccion_meta, P3=meta. Esta parametrizacion garantiza "
        "trayectorias suaves compatibles con las restricciones no-holonomicas del modelo Ackermann."
    )

    pdf.subtitulo("4.3 Algoritmo Pure Pursuit")
    pdf.parrafo(
        "El seguimiento de trayectoria utiliza el algoritmo Pure Pursuit, un metodo clasico y robusto "
        "para robots con cinematica tipo automovil. El proceso es: "
        "1) Encontrar el punto mas cercano de la trayectoria al robot. "
        "2) Buscar el punto de lookahead a una distancia configurable (30 px por defecto). "
        "3) Transformar el punto al marco local del robot. "
        "4) Calcular la curvatura: k = 2*y_local / Ld^2. "
        "5) Obtener el angulo de direccion Ackermann: delta = arctan(L*k), donde L es la distancia "
        "entre ejes (wheelbase = 50 px)."
    )

    pdf.parrafo(
        "La velocidad se adapta inversamente al angulo de direccion: a mayor giro, menor velocidad "
        "(rango 20%-100% del PWM maximo), mejorando la estabilidad en curvas."
    )

    # 5. Control
    pdf.titulo_seccion("5", "Sistema de Control")

    pdf.subtitulo("5.1 Maquina de Estados")
    pdf.tabla(
        ["Estado", "Descripcion", "Transicion"],
        [
            ["IDLE", "Sin navegacion activa", "-> NAVIGATING al recibir objetivo"],
            ["NAVIGATING", "Siguiendo trayectoria", "-> REACHED si dist < 15 px"],
            ["REACHED", "Objetivo alcanzado", "-> IDLE (automatico)"],
            ["ERROR", "Robot no detectado", "-> NAVIGATING al redetectar"],
        ],
        [35, 70, 85],
    )

    pdf.subtitulo("5.2 Conversion a Comandos de Actuacion")
    pdf.parrafo(
        "El controlador convierte las salidas del Pure Pursuit en senales para el hardware: "
        "el angulo del servo se calcula como 90 - angulo_direccion (centrado en 90, rango 45-135 grados). "
        "El PWM del motor es proporcional a la velocidad calculada. Se aplica control diferencial "
        "para compensar el deslizamiento en curvas: PWM_izq = PWM * (1 + 0.3*factor_giro), "
        "PWM_der = PWM * (1 - 0.3*factor_giro)."
    )

    # 6. Comunicacion
    pdf.titulo_seccion("6", "Comunicacion MQTT")
    pdf.parrafo(
        "La comunicacion entre el PC y el ESP32 se realiza mediante el protocolo MQTT a traves de "
        "un broker Mosquitto. Se utilizan dos topicos:"
    )

    pdf.tabla(
        ["Topico", "Direccion", "Contenido (JSON)"],
        [
            ["robot/cmd", "PC -> ESP32", "left_pwm, right_pwm, servo, action"],
            ["robot/status", "ESP32 -> PC", "status, wifi_rssi, uptime_s"],
        ],
        [40, 40, 110],
    )

    pdf.parrafo(
        "El ESP32 publica su estado cada 2 segundos e implementa reconexion automatica. "
        "La accion puede ser \"move\" (movimiento) o \"stop\" (parada de emergencia). "
        "La comunicacion es thread-safe con locks para acceso concurrente."
    )

    # 7. Hardware
    pdf.titulo_seccion("7", "Configuracion de Hardware")

    pdf.subtitulo("7.1 Componentes del Robot")
    pdf.item("Microcontrolador: ESP32 con WiFi integrado")
    pdf.item("Motor DC de traccion controlado por puente H (L298N)")
    pdf.item("Servo para direccion (cinematica Ackermann)")
    pdf.item("Marcadores de color: verde (frente) y azul (trasero), minimo 3x3 cm")

    pdf.subtitulo("7.2 Configuracion de Pines ESP32")
    pdf.tabla(
        ["Componente", "Pin GPIO", "Funcion"],
        [
            ["Motor ENA", "25", "PWM de traccion"],
            ["Motor IN1", "26", "Direccion del motor"],
            ["Motor IN2", "27", "Direccion del motor"],
            ["Servo", "13/15", "Control de direccion"],
        ],
        [55, 45, 90],
    )

    pdf.subtitulo("7.3 Infraestructura")
    pdf.item("Camara USB en posicion cenital sobre el area de trabajo (640x480 px)")
    pdf.item("Red WiFi local conectando PC y ESP32")
    pdf.item("Broker MQTT Mosquitto (puerto 1883) ejecutandose en el PC o en la red")

    # 8. Interfaz Grafica
    pdf.titulo_seccion("8", "Interfaz Grafica de Usuario")
    pdf.parrafo(
        "La aplicacion PyQt5 presenta un diseno de dos paneles: "
        "el panel izquierdo muestra el video en vivo (640x480) con superposiciones de la posicion "
        "del robot (circulo cyan), trayectoria planificada (linea naranja), objetivo (cruz roja), "
        "punto de lookahead (punto magenta) y cuadricula de coordenadas. "
        "El panel derecho contiene controles agrupados: estado del robot (X, Y, theta), "
        "vector de movimiento (distancia y angulo con botones Enviar/Detener), informacion "
        "de navegacion (distancia al objetivo, error de seguimiento), y configuracion MQTT "
        "(IP del broker, puerto, estado de conexion)."
    )

    # 9. Modos de Ejecucion
    pdf.titulo_seccion("9", "Modos de Ejecucion")
    pdf.tabla(
        ["Comando", "Modo", "Uso"],
        [
            ["python main.py", "Estandar", "Camara por defecto, broker local"],
            ["python main.py --camera 1", "Camara alternativa", "Seleccionar dispositivo"],
            ["python main.py --image foto.png", "Imagen estatica", "Pruebas de deteccion"],
            ["python main.py --simulate", "Simulacion", "Sin camara conectada"],
            ["python main.py --broker IP", "Broker remoto", "ESP32 en otra red"],
        ],
        [60, 40, 90],
    )

    # 10. Stack Tecnologico
    pdf.titulo_seccion("10", "Stack Tecnologico")
    pdf.tabla(
        ["Tecnologia", "Version", "Proposito"],
        [
            ["Python", "3.8+", "Lenguaje principal del sistema"],
            ["OpenCV", ">= 4.8.0", "Procesamiento de imagen y vision"],
            ["NumPy", ">= 1.24.0", "Calculos numericos y vectoriales"],
            ["PyQt5", ">= 5.15.0", "Interfaz grafica de usuario"],
            ["paho-mqtt", ">= 2.0.0", "Protocolo de comunicacion MQTT"],
            ["Matplotlib", ">= 3.7.0", "Visualizacion auxiliar"],
            ["Arduino/C++", "-", "Firmware del ESP32"],
            ["PubSubClient", "-", "Cliente MQTT en ESP32"],
        ],
        [45, 35, 110],
    )

    # Guardar
    pdf.output("Reporte_Navegacion_Robot_Ackermann.pdf")
    print("PDF generado: Reporte_Navegacion_Robot_Ackermann.pdf")


if __name__ == "__main__":
    generar()
