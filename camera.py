import cv2
import time
import numpy as np
from  color_distance import find_marker 

def camera_worker(name, cap, marker_update_event, done_event, marker_id_to_color, window_pos):
    id_to_xy = [(0,0)] * 30  # 最大30個のマーカーを想定
    i = 0
    cap.set(cv2.CAP_PROP_EXPOSURE, -8)  # 負の値が有効な場合もある
    cap.set(cv2.CAP_PROP_GAIN, 0)       # ゲインを抑えるとノイズ減少
    cap.set(cv2.CAP_PROP_BRIGHTNESS, 0) # 明るさ補正を無効に近づける

    # 右上にウィンドウを表示（x=1000, y=50 は適宜調整）
    cv2.namedWindow(name)
    cv2.moveWindow(name, window_pos[0], window_pos[1])

    while True:
        marker_update_event.wait()  # イベント待ち

        # time.sleep(0.5)  # 少し待つ（必要に応じて調整）


        if cv2.waitKey(500) & 0xFF == ord('q'):
            break

        ret, frame = cap.read()
        if not ret:
            print("カメラ読み取り失敗")
            continue

        i += 1
        # cv2.imwrite(f"{name}_{i}.jpg", frame)
        

        # print(f"{marker_id_to_color=}")
        
        for marker_id, color in marker_id_to_color.items():
            bgr_color = (color[2], color[1], color[0])
            marker_pos = find_marker(frame, bgr_color)
            
            # float配列をintタプルに変換
            marker_loc = (int(marker_pos[0]), int(marker_pos[1]))

            cv2.circle(frame, marker_loc, 5, bgr_color, 1)
            id_to_xy[marker_id] = marker_loc
        

        for i in range(len(id_to_xy)):
            if(i<len(id_to_xy)-1):
                cv2.line(frame, id_to_xy[i], id_to_xy[i+1], (255,255,255), 1)
            if marker_id_to_color:
                bgr_color = (color[2], color[1], color[0])
                cv2.circle(frame, id_to_xy[i], 2, bgr_color, 1)
                cv2.putText(frame,f"{i}", (id_to_xy[i][0] + 15, id_to_xy[i][1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.2, (255,255,255), 1)

            


        # frame_int = frame.astype(np.int16)
        # target_colors = {"Blue": np.array([255, 0, 0]), "Green": np.array([0, 255, 0]), "Red": np.array([0, 0, 255])}
        # color_data = {}
        # for name, color_val in target_colors.items():
        #     distance_map = np.sum(np.abs(frame_int - color_val), axis=2)
        #     _min_dist, _max_dist, min_loc, _max_loc = cv2.minMaxLoc(distance_map)
        #     color_data[name] = {'loc': min_loc, 'dist': _min_dist}
        #     bgr_color = tuple(map(int, color_val))
        #     cv2.circle(frame, min_loc, 10, bgr_color, 2)
        #     cv2.putText(frame, name, (min_loc[0] + 15, min_loc[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, bgr_color, 2)



        done_event.set()
        # 表示用にフレームを2倍にリサイズ
        display_frame = cv2.resize(frame, (frame.shape[1] * 2, frame.shape[0] * 2), interpolation=cv2.INTER_NEAREST)
        cv2.imshow(name, display_frame)


  

    cap.release()
    cv2.destroyWindow(name)