import serial
import os
import colorsys

arduino = None

def marker_initialize():
    global arduino
    port = os.getenv("PORT")
    arduino = serial.Serial(port, 115200, timeout=1)

def led_set(index: int, color: tuple[int,int,int]):
    """指定したLEDの色を送信"""
    global arduino
    if arduino is None:
        raise RuntimeError("Arduino が初期化されていません")
    r, g, b = color
    arduino.write(bytes([index, int(r), int(g), int(b)]))

def led_show():
    global arduino
    if arduino is None:
        raise RuntimeError("Arduino が初期化されていません")
    arduino.write(bytes([254,0,0,0]))

def led_clear():
    global arduino
    if arduino is None:
        raise RuntimeError("Arduino が初期化されていません")
    arduino.write(bytes([255,0,0,0]))

# def update_leds(active_marker_offset):
#     marker_id_to_color={}
#     for i in range(3):
#         h=i/3
#         if(active_marker_offset%2)==0:
#             h+=(1/3)/2
#         r, g, b = colorsys.hsv_to_rgb(h, 1, 1)

#         marker_id=active_marker_offset%10+i*10

#         marker_id_to_color[marker_id]=(int(r*255),int(g*255),int(b*255))

#     for marker_id,rgb in marker_id_to_color.items():
#         # print(f"LED {marker_id} {rgb}")
#         led_set(marker_id,rgb)

#     led_show()


def update_leds(active_marker_offset, marker_id_to_color):
    marker_id_to_color.clear()
    # for i in range(3):
   
    marker_id=active_marker_offset%30

    marker_id_to_color[marker_id]=(0,255,0)

    for marker_id,rgb in marker_id_to_color.items():
        # print(f"LED {marker_id} {rgb}")
        led_set(marker_id,rgb)

    led_show()


