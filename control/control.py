# control.py — P5: Control de trayectorias y ciclo de agarre
# Ingeniero de Control
# Robot: MyCobot 280 | Puerto: /dev/ttyUSB0 | Baud: 1_000_000

import time
from pymycobot.mycobot import MyCobot

# =========================
# CONEXION ROBOT
# =========================

mc = MyCobot("/dev/ttyUSB0", 1000000)
g_speed = 50

# =========================
# POSES CLAVE (P5)
# =========================

vision_angles = [0.26, -22.14, -0.87, -62.22, 11.16, -45.61]

ALL_COLORS_UP = [20.83, -32.69, -1.75, -59.06, -6.06, -44.91]

YELLOW_UP   = [68.9,   -53.78, -1.75, -38.05,  0.87, -44.91]
YELLOW_DOWN = [68.9,   -80.85, -1.75, -16.69,  1.75, -44.82]

RED_UP   = [85.42, -51.76, -1.75, -38.84, 2.98, -45.0]
RED_DOWN = [81.56, -79.18, -1.75, -28.65, 3.6,  -44.91]

GREEN_UP   = [101.16, -47.81, -1.75, -44.12, 2.46, -45.43]
GREEN_DOWN = [99.4,   -77.08, -1.75, -35.94, 2.72, -45.52]

BLUE_UP   = [112.93, -45.87,  -1.75, -50.09, 2.37, -44.91]
BLUE_DOWN = [115.22, -40.86, -90.43,  43.06, 2.9,  -44.91]

COLOR_POSES = {
    "AMARILLO": (YELLOW_UP, YELLOW_DOWN),
    "ROJO":     (RED_UP,    RED_DOWN),
    "VERDE":    (GREEN_UP,  GREEN_DOWN),
    "AZUL":     (BLUE_UP,   BLUE_DOWN),
}

# =========================
# CALIBRACION PIXEL → ANGULOS
# =========================

PIXEL_X_MIN = 60
PIXEL_X_MAX = 532
PIXEL_Y_MIN = 80
PIXEL_Y_MAX = 416

CENTER_ANGLES = [9.49, -77.95, -1.31, -37.96, 12.21, -44.56]


def calcular_angulos(px, py):
    """Convierte posición en píxeles a ángulos del robot."""
    angles = CENTER_ANGLES.copy()
    px = max(50, min(px, 547))
    py = max(70, min(py, 418))
    dx = px - 267
    dy = py - 215

    angles[0] = 10.45 - (dx * 0.060)
    angles[1] = -70.04 + (dy * 0.060)
    angles[2] = -16.34 - (dx * 0.10)
    angles[3] = -29.53 + (dy * 0.11)
    angles[4] = 10.72  - (dy * 0.012)
    angles[5] = -44.73

    if px > 430 and py > 320:
        angles[2] -= 15; angles[3] += 8
    elif px < 170 and py > 320:
        angles[2] -= 10; angles[3] += 4
    elif px > 430 and py < 150:
        angles[2] -= 5;  angles[3] += 2
    elif px < 170 and py < 150:
        angles[2] -= 8;  angles[3] += 3

    angles[3] += 3
    return angles


# =========================
# GOTO POSE
# =========================

def goto_pose(angles, speed=25, threshold=8):
    """Mueve el robot y espera hasta que llegue a la pose destino."""
    mc.send_angles(angles, speed)
    while True:
        current = mc.get_angles()
        if current and len(current) >= 6:
            error = sum(abs(current[i] - angles[i]) for i in range(6))
            if error < threshold:
                break
        time.sleep(0.1)
    time.sleep(0.3)


# =========================
# PICK
# =========================

def pick(cx, cy):
    """Baja al objeto en (cx, cy) y cierra el gripper."""
    cx = max(PIXEL_X_MIN, min(cx, PIXEL_X_MAX))
    cy = max(PIXEL_Y_MIN, min(cy, PIXEL_Y_MAX))
    target = calcular_angulos(cx, cy)

    mc.set_gripper_value(100, 40)
    time.sleep(1.5)

    mc.send_angles(target, 15)
    while True:
        current = mc.get_angles()
        if current and len(current) >= 6:
            if sum(abs(current[i] - target[i]) for i in range(6)) < 8:
                break
        time.sleep(0.1)

    time.sleep(1)
    mc.set_gripper_value(30, 40)
    time.sleep(2)


# =========================
# PLACE
# =========================

def place(color):
    """Deposita el objeto en la zona correspondiente al color."""
    goto_pose(ALL_COLORS_UP, speed=25)

    if color in COLOR_POSES:
        up, down = COLOR_POSES[color]
        goto_pose(up,   speed=25)
        goto_pose(down, speed=20)
        mc.set_gripper_value(100, 40)
        time.sleep(2)
        goto_pose(up,            speed=25)
        goto_pose(ALL_COLORS_UP, speed=25)

    goto_pose(vision_angles, speed=20)


# =========================
# CICLO COMPLETO (P5)
# =========================

def run_cycle(cx, cy, color):
    """Ejecuta un ciclo completo: pick → place → volver a visión."""
    print(f"[CICLO] Iniciando → color={color} px=({cx},{cy})")
    pick(cx, cy)
    place(color)
    print(f"[CICLO] Completado")


# =========================
# INICIALIZAR ROBOT
# =========================

def init_robot():
    mc.power_on()
    time.sleep(2)
    assert mc.is_controller_connected(), "[ERROR] Robot no conectado"
    goto_pose(vision_angles, speed=20)
    mc.set_gripper_value(100, 40)
    print("[OK] Robot inicializado en pose visión")
