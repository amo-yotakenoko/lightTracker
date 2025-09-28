import serial
import os
import colorsys
import random

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
    arduino.write(bytes([index, r, g, b]))


    

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


# def update_leds(active_marker_offset, marker_id_to_color):
#     marker_id_to_color.clear()
#     # for i in range(3):
   
#     marker_id=active_marker_offset%30

#     marker_id_to_color[marker_id]=(0,255,0)

#     for marker_id,rgb in marker_id_to_color.items():
#         # print(f"LED {marker_id} {rgb}")
#         led_set(marker_id,rgb)

#     led_show()



from collections import defaultdict

led_last_used = {}

def update_leds(active_marker_offset, marker_id_to_color):
    global led_last_used
    marker_id_to_color.clear()

    colors = []
    color_length = 3
    for i in range(color_length):
        h = i / color_length
        r, g, b = colorsys.hsv_to_rgb(h, 1, 1)
        colors.append((int(r * 255), int(g * 255), int(b * 255)))

    # 1. オフセット値ごとにLEDをグループ化
    offset_to_leds = defaultdict(list)
    for led_id, offset in led_last_used.items():
        offset_to_leds[offset].append(led_id)

    # 2. 未使用のLEDと、使用済みのLEDの優先順位リストを作成
    all_leds = set(range(30))
    used_leds = set(led_last_used.keys())
    unused_leds = list(all_leds - used_leds)
    random.shuffle(unused_leds)  # 未使用LEDはランダム

    # 優先順位リストの作成
    candidate_leds = list(unused_leds)

    # offsetが小さい順（古い順）に並べ、同じ古さのLEDはシャッフルして追加
    sorted_offsets = sorted(offset_to_leds.keys())
    for offset in sorted_offsets:
        led_group = offset_to_leds[offset]
        random.shuffle(led_group)
        candidate_leds.extend(led_group)

    # 3. 点灯するLEDを選択
    leds_to_light = candidate_leds[:color_length]

    # 4. 選択したLEDの最終使用時刻を更新
    for led_id in leds_to_light:
        led_last_used[led_id] = active_marker_offset
        # 履歴が溜まりすぎないように、一定数を超えたら古いものから削除
        if len(led_last_used) > 30:
            oldest_led = min(led_last_used, key=led_last_used.get)
            del led_last_used[oldest_led]

    # 5. LEDを点灯
    for i, led_id in enumerate(leds_to_light):
        marker_id_to_color[led_id] = colors[i]

    for marker_id, rgb in marker_id_to_color.items():
        led_set(marker_id, rgb)

    led_show()



# def update_leds(active_marker_offset, marker_id_to_color):
#     marker_id_to_color.clear()
    
#     # それぞれに赤、緑、青を割り当てる
#     colors = [ (255, 0, 0),(0, 255, 0),(0, 0, 255),]
#             #   (0, 255, 255),(255, 0, 255),(255, 255, 0),]

#     for i,color in enumerate(colors):
#         marker_id_to_color[active_marker_offset%10+i*10] = color
    

#     for marker_id,rgb in marker_id_to_color.items():
#         # print(f"LED {marker_id} {rgb}")
#         led_set(marker_id,rgb)

#     led_show()
