# vision.py — P6: Detección de objetos por color (HSV)
# Ingeniero de Visión
# Robot: MyCobot 280 | Entorno: Ubuntu 20.04 + Jetson Nano

import cv2 as cv
import numpy as np
import threading
import ipywidgets.widgets as widgets
from IPython.display import display

# =========================
# CALIBRACION PIXEL
# =========================

PIXEL_X_MIN = 60
PIXEL_X_MAX = 532
PIXEL_Y_MIN = 80
PIXEL_Y_MAX = 416

CENTER_X = 279
CENTER_Y = 219

# Variables globales de detección
current_cx = CENTER_X
current_cy = CENTER_Y
detected_color = "AMARILLO"
model = "Start"

# =========================
# RANGOS HSV POR COLOR
# =========================

COLOR_RANGES = {
    "AZUL": (
        np.array([100, 120, 70]),
        np.array([140, 255, 255]),
        (255, 0, 0)
    ),
    "ROJO": (
        np.array([0, 120, 70]),
        np.array([10, 255, 255]),
        (0, 0, 255)
    ),
    "VERDE": (
        np.array([40, 70, 70]),
        np.array([80, 255, 255]),
        (0, 255, 0)
    ),
    "AMARILLO": (
        np.array([20, 100, 100]),
        np.array([35, 255, 255]),
        (0, 255, 255)
    ),
}

# =========================
# WIDGET IMAGEN
# =========================

imgbox = widgets.Image(
    format='jpg',
    width=640,
    height=480,
    layout=widgets.Layout(align_self='center')
)

button_close = widgets.Button(description='Close_Camera', button_style='danger')


def button_close_Callback(value):
    global model
    model = 'Exit'

button_close.on_click(button_close_Callback)


# =========================
# DETECCION (P6)
# detect_object() -> (cx_px, cy_px, color) | None
# =========================

def detect_object(frame):
    """
    Detecta el objeto de color en el frame.
    Retorna (cx, cy, color_name) o None si no hay detección.
    """
    hsv = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

    for color_name, (lower, upper, _) in COLOR_RANGES.items():
        mask = cv.inRange(hsv, lower, upper)

        # Rojo tiene dos rangos HSV
        if color_name == "ROJO":
            mask2 = cv.inRange(hsv, np.array([170, 120, 70]), np.array([180, 255, 255]))
            mask = mask + mask2

        contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if cv.contourArea(cnt) > 500:
                x, y, w, h = cv.boundingRect(cnt)
                cx = x + w // 2
                cy = y + h // 2
                return cx, cy, color_name

    return None


# =========================
# LOOP CAMARA
# =========================

def camera():
    global model, current_cx, current_cy, detected_color

    capture = cv.VideoCapture(0)
    capture.set(cv.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv.CAP_PROP_FRAME_HEIGHT, 480)

    while capture.isOpened():
        try:
            ret, img = capture.read()
            if not ret or model == 'Exit':
                break

            hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)

            for color_name, (lower, upper, box_color) in COLOR_RANGES.items():
                mask = cv.inRange(hsv, lower, upper)
                if color_name == "ROJO":
                    mask += cv.inRange(hsv, np.array([170, 120, 70]), np.array([180, 255, 255]))

                contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
                for cnt in contours:
                    if cv.contourArea(cnt) > 500:
                        x, y, w, h = cv.boundingRect(cnt)
                        cx, cy = x + w // 2, y + h // 2
                        current_cx, current_cy = cx, cy
                        detected_color = color_name

                        cv.rectangle(img, (x, y), (x+w, y+h), box_color, 2)
                        cv.circle(img, (cx, cy), 5, (255, 255, 255), -1)
                        cv.putText(img, f"{color_name} ({cx},{cy})",
                                   (x, y+20), cv.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)

            imgbox.value = cv.imencode('.jpg', img)[1].tobytes()

        except Exception as e:
            print(f"[VISION ERROR] {e}")
            break

    capture.release()


# =========================
# INICIAR CAMARA
# =========================

def start_camera():
    t = threading.Thread(target=camera)
    t.daemon = True
    t.start()
    return t
