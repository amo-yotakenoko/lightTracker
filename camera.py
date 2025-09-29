import cv2
import time
import numpy as np
from  color_distance import find_marker 
from scipy.spatial import distance
from scipy.optimize import linear_sum_assignment


class Marker:
   
    def __init__(self, position):
        self.track = []
        self.update_position(position)
        

    def update_position(self, new_position):
        self.position = new_position
        self.track.append(self.position.copy())
        if len(self.track) > 50:  # トラックの長さを50に制限
            self.track.pop(0)

    def draw_track(self, frame):
        for i in range(1, len(self.track)):
            cv2.line(frame, tuple(self.track[i - 1].astype(int)), tuple(self.track[i].astype(int)), (0, 0, 255), 1)


def camera_worker(name, cap, marker_update_event, done_event, marker_id_to_color, window_pos):
    id_to_xy = [(0,0)] * 30  # 最大30個のマーカーを想定
    i = 0
    cap.set(cv2.CAP_PROP_EXPOSURE, -8)  # 負の値が有効な場合もある
    cap.set(cv2.CAP_PROP_GAIN, 0)       # ゲインを抑えるとノイズ減少
    cap.set(cv2.CAP_PROP_BRIGHTNESS, 0) # 明るさ補正を無効に近づける

    # 右上にウィンドウを表示（x=1000, y=50 は適宜調整）
    cv2.namedWindow(name)
    cv2.moveWindow(name, window_pos[0], window_pos[1])

    markers = []

    while True:


        # time.sleep(0.5)  # 少し待つ（必要に応じて調整）



        ret, frame = cap.read()
        if not ret:
            print("カメラ読み取り失敗")
            continue

        i += 1
        

      

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, threshold_frame = cv2.threshold(gray_frame, 50, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(threshold_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        print(f"{name} {i} フレーム内の輪郭数: {len(contours)}")
        # cv2.drawContours(frame, contours, -1, (0, 100, 0), 2)
        detect_marker_positions = [] 
        for cnt in contours:
            # 輪郭を描画（緑色の線）
            cv2.drawContours(frame, [cnt], -1, (0, 255, 0), 1)

            # 輪郭のモーメントから重心を計算
            M = cv2.moments(cnt)
            if M["m00"] != 0:  # 面積がゼロでないとき
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                # 空のマスク作成（フレームと同じサイズ、単一チャンネル）
                mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    
                # 輪郭領域を白(255)で塗る
                cv2.drawContours(mask, [cnt], -1, 255, -1)  # -1 = 塗りつぶし
                
                # 輪郭内の平均色を取得
                mean_color = cv2.mean(frame, mask=mask)  # (B, G, R, A)

                # 中心にマーク（赤い小さい円）
                cv2.circle(frame, (cx, cy), 1, (0, 0, 255), -1)
                detect_marker_positions.append([cx, cy])

        # --- forループの外に移動 ---
        # markers は Marker クラスのリスト
        markers_positions = np.array([m.position for m in markers], dtype=np.float32)
        if markers_positions.size == 0:
            markers_positions = np.empty((0, 2), dtype=np.float32)
        else:
            markers_positions = np.atleast_2d(markers_positions)

        # detect_marker_positions は検出点のリスト
        detect_marker_positions = np.array(detect_marker_positions, dtype=np.float32)
        if detect_marker_positions.size == 0:
            detect_marker_positions = np.empty((0, 2), dtype=np.float32)
        else:
            detect_marker_positions = np.atleast_2d(detect_marker_positions)

        
        cost_matrix = distance.cdist(markers_positions, detect_marker_positions)

        matched_prev, matched_new = linear_sum_assignment(cost_matrix)

        max_dist = 50
        matched_old = []           # 「残存マーカー」のインデックス（過去フレームの markers リスト内でマッチしたもの）
        matched_new_valid = []     # 「残存マーカーに対応する新しい点」のインデックス（detect_marker_positions 内でマッチしたもの）

        # 残存マーカー更新
        for i, j in zip(matched_prev, matched_new):
            if cost_matrix[i, j] <= max_dist:
                markers[i].update_position( detect_marker_positions[j])
                matched_old.append(i)
                matched_new_valid.append(j)

        to_remove = []  # 削除対象のインデックス
        for i in range(len(markers)):
            if i not in matched_old:
                to_remove.append(i)
        # 逆順で削除
        for i in sorted(to_remove, reverse=True):
            del markers[i]

        # 追加：matched_new_valid に入っていない新しい点
        for j in range(len(detect_marker_positions)):
            if j not in matched_new_valid:
                markers.append(Marker(detect_marker_positions[j]))
                                



        for m in markers:
            m.draw_track(frame)
           




        # 表示用にフレームを2倍にリサイズ
        frame = cv2.resize(frame, (frame.shape[1] * 2, frame.shape[0] * 2), interpolation=cv2.INTER_NEAREST)
        cv2.imshow(name, frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break


  

    cap.release()
    cv2.destroyWindow(name)