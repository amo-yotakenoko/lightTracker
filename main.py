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
import settings
import estimation
import chAruco_calibration



load_dotenv()
print("環境変数読み込み")
if settings.mode=="serialSync":
    arduino_controller.initialize()


camera_ids=[0,1,2]
marker_id_to_color_id=[-1] *30



cameras = []
threadings=[]
camera_done_events = []


# ウィンドウ位置をずらす設定
x_offset = 0  # 画面左からの開始位置
y_offset = 0  # 画面上からの開始位置
x_spacing = 640 # ウィンドウ幅想定
y_spacing = 300 # ウィンドウ高さ想定

print("カメラ初期化")
for idx, camera_id in enumerate(camera_ids):
        print(f"{camera_id}")
            # ウィンドウ位置を計算（横に並べる例）
        x = x_offset + (idx % 3) * x_spacing
        y = y_offset + (idx // 3) * y_spacing

        print(" cam = camera.Camera(marker_id_to_color_id)")
        cam = camera.Camera(marker_id_to_color_id,camera_id =camera_id)
        
        cameras.append(cam)
        print("cap=cv2.VideoCapture(camera_id)")
        

        threadings.append(threading.Thread(target=cam.detect_markers,
                                      daemon=True,
                                        args=(f"{camera_id}",
                
                   (x,y),)))
        


print("estimation thread")


threadings.append(threading.Thread(target=estimation.estimation,
                                daemon=True,
                                args=(cameras,)))



if settings.mode=="serialSync":
    # マーカー更新ループのスレッドを追加
    threadings.append(threading.Thread(target=marker_update.run_marker_tracking_loop, 
                                    daemon=True,
                                    args=(cameras, marker_id_to_color_id)))


print("スレッドスタート")
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

