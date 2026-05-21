# main.py — Pipeline End-to-End (P5, P6, P7) — versión actualizada
# Usa interpolación bilineal para mapeo píxel → coordenadas cartesianas
# Robot: MyCobot 280 | Puerto: /dev/ttyUSB0 | Baud: 1_000_000

import time
import threading
import cv2 as cv
import numpy as np
import ipywidgets.widgets as widgets
from IPython.display import display
from pymycobot.mycobot import MyCobot

# =========================
# CONEXION ROBOT
# =========================
mc = MyCobot("/dev/ttyUSB0", 1000000)
g_speed = 50

# =========================
# POSE VISION (COORDENADAS)
# =========================
vision_coords = [144.9, -37.4, 290.1, -172.11, -2.96, -45.23]

# =========================
# POSICION SEGURA GENERAL
# =========================
ALL_COLORS_UP = [20.83, -32.69, -1.75, -59.06, -6.06, -44.91]

# =========================
# POSICIONES POR COLOR
# =========================
YELLOW_UP   = [68.9,   -53.78, -1.75, -38.05,  0.87, -44.91]
YELLOW_DOWN = [68.9,   -80.85, -1.75, -16.69,  1.75, -44.82]

RED_UP   = [85.42, -51.76, -1.75, -38.84, 2.98, -45.0]
RED_DOWN = [81.56, -79.18, -1.75, -28.65, 3.6,  -44.91]

GREEN_UP   = [101.16, -47.81, -1.75, -44.12, 2.46, -45.43]
GREEN_DOWN = [99.4,   -77.08, -1.75, -35.94, 2.72, -45.52]

BLUE_UP   = [112.93, -45.87,  -1.75, -50.09, 2.37, -44.91]
BLUE_DOWN = [115.22, -40.86, -90.43,  43.06, 2.9,  -44.91]

# =========================
# PUNTOS DE CALIBRACION
# =========================
calibration_points = [
    {"pixel": (47,  54),  "coords": [226.0,  61.1, 115.6, -167.94, -0.39, -46.92]},  # arriba izquierda
    {"pixel": (558, 49),  "coords": [225.8, -65.3, 118.4, -170.47, -5.34, -48.55]},  # arriba derecha
    {"pixel": (60,  417), "coords": [151.8,  62.1, 116.1, -176.6,   2.38, -44.06]},  # abajo izquierda
    {"pixel": (558, 420), "coords": [156.7, -60.8, 121.6, -177.83,  1.76, -51.28]},  # abajo derecha
    {"pixel": (280, 214), "coords": [207.5,   4.2, 113.0,  179.83,  3.06, -47.14]},  # centro
]

# =========================
# VARIABLES GLOBALES
# =========================
current_cx   = 280
current_cy   = 214
detected_color = "AMARILLO"
model = "Start"

# =========================
# PIXEL → COORDS (interpolación bilineal)
# =========================
def pixel_to_coords(px, py):
    px = max(47, min(px, 558))
    py = max(49, min(py, 420))
    tx = (px - 47) / (558 - 47)
    ty = (py - 49) / (420 - 49)
    tl = calibration_points[0]["coords"]
    tr = calibration_points[1]["coords"]
    bl = calibration_points[2]["coords"]
    br = calibration_points[3]["coords"]
    result = []
    for i in range(6):
        top    = tl[i] + tx * (tr[i] - tl[i])
        bottom = bl[i] + tx * (br[i] - bl[i])
        result.append(top + ty * (bottom - top))
    return result

# =========================
# MOVER Y ESPERAR
# =========================
def move_slow(angles, speed=25):
    mc.send_angles(angles, speed)
    while True:
        current = mc.get_angles()
        if current and len(current) >= 6:
            if sum(abs(current[i] - angles[i]) for i in range(6)) < 8:
                break
        time.sleep(0.1)
    time.sleep(0.3)

# =========================
# IR AL PIXEL
# =========================
def mover_robot_al_pixel(px, py):
    target_coords = pixel_to_coords(px, py)
    print("PIXEL:", px, py)
    print("COORDS:", target_coords)
    mc.send_coords(target_coords, 20, 0)
    while True:
        current = mc.get_coords()
        if current and len(current) >= 6:
            if sum(abs(current[i] - target_coords[i]) for i in range(6)) < 15:
                break
        time.sleep(0.1)

# =========================
# ENCENDER ROBOT
# =========================
mc.power_on()
time.sleep(2)
print("Moviendo robot a posicion vision...")
mc.send_coords(vision_coords, 20, 0)
time.sleep(5)
print("Robot listo")

# =========================
# FUNCIONES SLIDERS
# =========================
def on_slider_S1(angle): mc.send_angle(1, angle, g_speed)
def on_slider_S2(angle): mc.send_angle(2, angle, g_speed)
def on_slider_S3(angle): mc.send_angle(3, angle, g_speed)
def on_slider_S4(angle): mc.send_angle(4, angle, g_speed)
def on_slider_S5(angle): mc.send_angle(5, angle, g_speed)
def on_slider_S6(angle): mc.send_angle(6, angle, g_speed)
def on_slider_S7(angle): mc.set_gripper_value(int(angle), g_speed)

# =========================
# BOTONES
# =========================
button_reset    = widgets.Button(description='Reset',        button_style='info')
button_power_on = widgets.Button(description='Power_on',     button_style='success')
button_power_off= widgets.Button(description='Power_off',    button_style='danger')
button_go_cube  = widgets.Button(description='Go_To_Cube',   button_style='warning')
button_close    = widgets.Button(description='Close_Camera', button_style='danger')
output = widgets.Output()

def reset_joints():
    mc.send_coords(vision_coords, 20, 0)
    time.sleep(5)
    mc.set_gripper_value(100, 40)
    slider_S7.value = 100

def on_button_clicked(b):
    if b.description == 'Reset':       reset_joints()
    elif b.description == 'Power_on':  mc.power_on()
    elif b.description == 'Power_off': mc.power_off()

button_reset.on_click(on_button_clicked)
button_power_on.on_click(on_button_clicked)
button_power_off.on_click(on_button_clicked)

# =========================
# PICK AND PLACE (P5 + P7)
# =========================
def pick_cube():
    global detected_color
    print("Color:", detected_color)
    mc.set_gripper_value(100, 40)
    time.sleep(1.5)
    mover_robot_al_pixel(current_cx, current_cy)
    time.sleep(1)
    mc.set_gripper_value(30, 40)
    time.sleep(2)
    move_slow(ALL_COLORS_UP, speed=25)

    color_poses = {
        "AMARILLO": (YELLOW_UP, YELLOW_DOWN),
        "ROJO":     (RED_UP,    RED_DOWN),
        "VERDE":    (GREEN_UP,  GREEN_DOWN),
        "AZUL":     (BLUE_UP,   BLUE_DOWN),
    }
    if detected_color in color_poses:
        up, down = color_poses[detected_color]
        move_slow(up,            speed=25)
        move_slow(down,          speed=20)
        mc.set_gripper_value(100, 40)
        time.sleep(2)
        move_slow(up,            speed=25)
        move_slow(ALL_COLORS_UP, speed=25)

    mc.send_coords(vision_coords, 20, 0)
    time.sleep(5)

def go_cube_callback(b):
    threading.Thread(target=pick_cube, daemon=True).start()

button_go_cube.on_click(go_cube_callback)

# =========================
# SLIDERS
# =========================
slider_S1 = widgets.FloatSlider(description='J1:', value=0,   min=-168, max=168,  step=0.1)
slider_S2 = widgets.FloatSlider(description='J2:', value=0,   min=-135, max=90,   step=0.1)
slider_S3 = widgets.FloatSlider(description='J3:', value=0,   min=-150, max=150,  step=0.1)
slider_S4 = widgets.FloatSlider(description='J4:', value=0,   min=-145, max=145,  step=0.1)
slider_S5 = widgets.FloatSlider(description='J5:', value=0,   min=-165, max=165,  step=0.1)
slider_S6 = widgets.FloatSlider(description='J6:', value=0,   min=-180, max=180,  step=0.1)
slider_S7 = widgets.IntSlider(  description='G7:', value=100, min=30,   max=100,  step=1)

w1 = widgets.interactive(on_slider_S1, angle=slider_S1)
w2 = widgets.interactive(on_slider_S2, angle=slider_S2)
w3 = widgets.interactive(on_slider_S3, angle=slider_S3)
w4 = widgets.interactive(on_slider_S4, angle=slider_S4)
w5 = widgets.interactive(on_slider_S5, angle=slider_S5)
w6 = widgets.interactive(on_slider_S6, angle=slider_S6)
w7 = widgets.interactive(on_slider_S7, angle=slider_S7)

box_joints = widgets.VBox([w7, w6, w5, w4, w3, w2, w1])

# =========================
# CAMARA (P6)
# =========================
imgbox = widgets.Image(format='jpg', width=640, height=480,
                       layout=widgets.Layout(align_self='center'))

def button_close_Callback(value):
    global model
    model = 'Exit'

button_close.on_click(button_close_Callback)

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
            masks = {
                "AZUL":     (cv.inRange(hsv, np.array([100,120,70]),  np.array([140,255,255])), (255,0,0)),
                "ROJO":     (cv.inRange(hsv, np.array([0,120,70]),    np.array([10,255,255]))
                           + cv.inRange(hsv, np.array([170,120,70]),  np.array([180,255,255])), (0,0,255)),
                "VERDE":    (cv.inRange(hsv, np.array([40,70,70]),    np.array([80,255,255])),  (0,255,0)),
                "AMARILLO": (cv.inRange(hsv, np.array([20,100,100]),  np.array([35,255,255])),  (0,255,255)),
            }
            for color_name, (mask, box_color) in masks.items():
                contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
                for cnt in contours:
                    if cv.contourArea(cnt) > 500:
                        x, y, w, h = cv.boundingRect(cnt)
                        cx, cy = x + w // 2, y + h // 2
                        current_cx, current_cy = cx, cy
                        detected_color = color_name
                        cv.rectangle(img, (x,y), (x+w,y+h), box_color, 2)
                        cv.circle(img, (cx,cy), 5, (255,255,255), -1)
                        cv.putText(img, f"{color_name} ({cx},{cy})", (x,y+20),
                                   cv.FONT_HERSHEY_SIMPLEX, 0.7, box_color, 2)
            imgbox.value = cv.imencode('.jpg', img)[1].tobytes()
        except:
            break
    capture.release()

camera_thread = threading.Thread(target=camera)
camera_thread.daemon = True
camera_thread.start()

# =========================
# DISPLAY
# =========================
box_group1 = widgets.VBox([button_reset, button_power_on, button_power_off,
                            button_go_cube, button_close, output])
box_display = widgets.HBox([box_group1, box_joints, imgbox])
display(box_display)
