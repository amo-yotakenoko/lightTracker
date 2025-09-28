import cv2
import time
import numpy as np

def camera_worker(name, cap, marker_update_event, marker_id_to_color, window_pos):
    id_to_xy = [(0,0)] * 30  # 最大30個のマーカーを想定
    i = 0
    # print(cap.get(cv2.CAP_PROP_EXPOSURE))
    cap.set(cv2.CAP_PROP_EXPOSURE, -13)
    # print(cap.get(cv2.CAP_PROP_EXPOSURE))

    # 右上にウィンドウを表示（x=1000, y=50 は適宜調整）
    cv2.namedWindow(name)
    cv2.moveWindow(name, window_pos[0], window_pos[1])

    while True:
        marker_update_event.wait()  # イベント待ち

        ret, frame = cap.read()
        if not ret:
            print("カメラ読み取り失敗")
            continue

        i += 1
        # cv2.imwrite(f"{name}_{i}.jpg", frame)
        

        # print(f"{marker_id_to_color=}")
        frame_int = frame.astype(np.int16)
        for marker_id, color in marker_id_to_color.items():
            distance_map = np.sum(np.abs(frame_int - color), axis=2)
            _min_dist, _max_dist, min_loc, _max_loc = cv2.minMaxLoc(distance_map)
            cv2.circle(frame, min_loc, 5, color, 1)
            id_to_xy[marker_id] = min_loc
        

        for i in range(len(id_to_xy)):
            if(i<len(id_to_xy)-1):
                cv2.line(frame, id_to_xy[i], id_to_xy[i+1], (255,255,255), 1)
            cv2.circle(frame, id_to_xy[i], 2, color, 1)
            cv2.putText(frame,f"{i}", (id_to_xy[i][0] + 15, id_to_xy[i][1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

            


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



        cv2.imshow(name, frame)


        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyWindow(name)