# main.py — P7: Pipeline End-to-End
# Líder de Integración
# Máquina de estados: IDLE → DETECTANDO → CALC_IK → AGARRANDO → DEPOSITANDO
# Robot: MyCobot 280 | Puerto: /dev/ttyUSB0 | Baud: 1_000_000

import time
import threading
import ipywidgets.widgets as widgets
from IPython.display import display

from control.control import mc, init_robot, run_cycle, goto_pose, g_speed
from control.control import vision_angles
from vision.vision   import start_camera, detect_object, imgbox, button_close
from vision.vision   import current_cx, current_cy, detected_color

# =========================
# ESTADO DE LA MAQUINA
# =========================

STATE = "IDLE"

# =========================
# SLIDERS
# =========================

slider_S1 = widgets.FloatSlider(description='J1:', value=vision_angles[0], min=-168, max=168,  step=0.1)
slider_S2 = widgets.FloatSlider(description='J2:', value=vision_angles[1], min=-135, max=90,   step=0.1)
slider_S3 = widgets.FloatSlider(description='J3:', value=vision_angles[2], min=-150, max=150,  step=0.1)
slider_S4 = widgets.FloatSlider(description='J4:', value=vision_angles[3], min=-145, max=145,  step=0.1)
slider_S5 = widgets.FloatSlider(description='J5:', value=vision_angles[4], min=-165, max=165,  step=0.1)
slider_S6 = widgets.FloatSlider(description='J6:', value=vision_angles[5], min=-180, max=180,  step=0.1)
slider_S7 = widgets.IntSlider(  description='G7:', value=100,              min=30,   max=100,  step=1)

def on_s1(a): mc.send_angle(1, a, g_speed)
def on_s2(a): mc.send_angle(2, a, g_speed)
def on_s3(a): mc.send_angle(3, a, g_speed)
def on_s4(a): mc.send_angle(4, a, g_speed)
def on_s5(a): mc.send_angle(5, a, g_speed)
def on_s6(a): mc.send_angle(6, a, g_speed)
def on_s7(a): mc.set_gripper_value(int(a), g_speed)

w1 = widgets.interactive(on_s1, angle=slider_S1)
w2 = widgets.interactive(on_s2, angle=slider_S2)
w3 = widgets.interactive(on_s3, angle=slider_S3)
w4 = widgets.interactive(on_s4, angle=slider_S4)
w5 = widgets.interactive(on_s5, angle=slider_S5)
w6 = widgets.interactive(on_s6, angle=slider_S6)
w7 = widgets.interactive(on_s7, angle=slider_S7)

box_joints = widgets.VBox([w7, w6, w5, w4, w3, w2, w1])

# =========================
# BOTONES
# =========================

button_reset    = widgets.Button(description='Reset',       button_style='info')
button_power_on = widgets.Button(description='Power_on',    button_style='success')
button_power_off= widgets.Button(description='Power_off',   button_style='danger')
button_go_cube  = widgets.Button(description='Go_To_Cube',  button_style='warning')
output = widgets.Output()


def reset_joints():
    goto_pose(vision_angles, speed=20)
    mc.set_gripper_value(100, 40)
    slider_S1.value = vision_angles[0]
    slider_S2.value = vision_angles[1]
    slider_S3.value = vision_angles[2]
    slider_S4.value = vision_angles[3]
    slider_S5.value = vision_angles[4]
    slider_S6.value = vision_angles[5]
    slider_S7.value = 100


def on_button_clicked(b):
    if b.description == 'Reset':
        reset_joints()
    elif b.description == 'Power_on':
        mc.power_on()
    elif b.description == 'Power_off':
        mc.power_off()

button_reset.on_click(on_button_clicked)
button_power_on.on_click(on_button_clicked)
button_power_off.on_click(on_button_clicked)


# =========================
# PIPELINE E2E (P7)
# =========================

def pipeline():
    global STATE
    STATE = "DETECTANDO"
    print(f"[{STATE}] Buscando objeto...")

    cx, cy, color = current_cx, current_cy, detected_color

    STATE = "CALC_IK"
    print(f"[{STATE}] color={color} px=({cx},{cy})")

    STATE = "AGARRANDO"
    print(f"[{STATE}] Ejecutando pick & place...")
    run_cycle(cx, cy, color)

    STATE = "IDLE"
    print(f"[{STATE}] Ciclo completado.")


def go_cube_callback(b):
    threading.Thread(target=pipeline, daemon=True).start()

button_go_cube.on_click(go_cube_callback)

# =========================
# ARRANQUE
# =========================

init_robot()
start_camera()

# =========================
# DISPLAY
# =========================

box_buttons = widgets.VBox([
    button_reset, button_power_on, button_power_off,
    button_go_cube, button_close, output
])

box_display = widgets.HBox([box_buttons, box_joints, imgbox])
display(box_display)
