import cv2
import numpy as np
import time
import os
import marker_update
import threading
import camera
from dotenv import load_dotenv
import os

load_dotenv()

marker_update.marker_initialize()


camera_ids=[0,1]
marker_id_to_color={}

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

		cap=cv2.VideoCapture(camera_id)
		done_event = threading.Event()
		camera_done_events.append(done_event)
		threadings.append(threading.Thread(target=camera.camera_worker,
									  daemon=True,
									    args=(f"{camera_id}",
				   cap,
				   marker_update_event,
				   done_event,
				   marker_id_to_color,
				   (x,y),)))

for t in threadings:
	t.start()


active_marker_offset=0


time.sleep(2)
print("start")
while True:


	marker_update.update_leds(active_marker_offset,marker_id_to_color)
	active_marker_offset+=1

	# print(f"LED {active_marker_id} ON")



	marker_update_event.set()


	for event in camera_done_events:
		event.wait()
	
	for event in camera_done_events:
		event.clear()


	marker_update_event.clear()
	


	
	



