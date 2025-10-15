import cv2
import numpy as np
import time
import os
import marker_update
import threading
import camera
from dotenv import load_dotenv
import os
import arduino_controller
from arduino_controller import led_set, led_show, led_clear

load_dotenv()

arduino_controller.initialize()


camera_ids=[0]
marker_id_to_color_id=[-1] *30



cameras = []
threadings=[]
marker_update_event = threading.Event()
camera_done_events = []


# ウィンドウ位置をずらす設定
x_offset = 50  # 画面左からの開始位置
y_offset = 50  # 画面上からの開始位置
x_spacing = 700 # ウィンドウ幅想定
y_spacing = 300 # ウィンドウ高さ想定

for idx, camera_id in enumerate(camera_ids):
            # ウィンドウ位置を計算（横に並べる例）
        x = x_offset + (idx % 3) * x_spacing
        y = y_offset + (idx // 3) * y_spacing

        cam = camera.Camera(marker_id_to_color_id)
        cameras.append(cam)
        cap=cv2.VideoCapture(camera_id)
        done_event = threading.Event()
        camera_done_events.append(done_event)
        threadings.append(threading.Thread(target=cam.detect_markers,
                                      daemon=True,
                                        args=(f"{camera_id}",
                   cap,
                   (x,y),)))


# マーカー更新ループのスレッドを追加
# threadings.append(threading.Thread(target=marker_update.run_marker_tracking_loop, 
#                                   daemon=True,
#                                   args=(cameras, marker_id_to_color_id)))


for t in threadings:
    t.start()


print("start")
try:
    # すべてのスレッドが終了するのを待つ
    # Ctrl+Cで終了できるように、joinにタイムアウトを設定してループする
    while any(t.is_alive() for t in threadings):
        for t in threadings:
            t.join(0.1)
except KeyboardInterrupt:
    led_clear()
    print("\nExiting...")

