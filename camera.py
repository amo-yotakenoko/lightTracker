import cv2
import time
import numpy as np
from  color_distance import find_marker 
from scipy.spatial import distance
from scipy.optimize import linear_sum_assignment
import marker_update


class Marker:

   
    def __init__(self, position, marker_id_to_color_id):
        self.track = []
        self.update_position(position)
        self.color=None
        self.marker_color_id=-1
        self.marker_id_to_color_id = marker_id_to_color_id

        self.reset_probability_distribution()
        

    def reset_probability_distribution(self):
        self.probability_distribution=np.array([1/30]*30)
        

    def update_position(self, new_position):
        self.position = new_position
        self.track.append(self.position.copy())
        if len(self.track) > 50:  # トラックの長さを50に制限
            self.track.pop(0)


    def update_color(self, color):
        distances = [np.linalg.norm(c - np.array(color)) for c in marker_update.marker_bgrs]
        self.marker_color_id = np.argmin(distances)

    
    def now_probability(self):
        
        
        now_probability_distribution=np.array([0.1]*30)
        for i in range(30):
            # print(self.marker_id_to_color_id,self.marker_color_id,i,self.marker_color_id == self.marker_id_to_color_id[i])

            if self.marker_color_id == self.marker_id_to_color_id[i]:
                now_probability_distribution[i]=0.2

            # 正規化
        now_probability_distribution /= now_probability_distribution.sum()
        # print(now_probability_distribution,self.entropy())
        return now_probability_distribution

    def probability_update(self):
        
        self.probability_distribution = self.probability_distribution * self.now_probability()
        self.probability_distribution /= self.probability_distribution.sum()


    def entropy(self):
        p = self.probability_distribution
        # p = p[p > 0]  # 0の要素を除外
        return -np.sum(p * np.log2(p))
    

    def estimate_id(self):
        max_val = self.probability_distribution.max()
        max_indices = np.where(self.probability_distribution == max_val)[0]
        return max_indices.tolist()


    def draw_info(self, frame):
        for i in range(1, len(self.track)):
            cv2.line(frame, tuple(self.track[i - 1].astype(int)), tuple(self.track[i].astype(int)), (0, 0, 255), 1)
            color=(marker_update.marker_bgrs[self.marker_color_id]*255).astype(int).tolist()
            # print(f"{self.marker_color_id=} {color=}")
            # cv2.putText(frame, f"{self.marker_color_id}", (int(self.position[0])-5, int(self.position[1])-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
            entropy=self.entropy()
            if(entropy>1):
                cv2.putText(frame, f"{entropy:.3f}bit", (int(self.position[0])+10, int(self.position[1])-5), cv2.FONT_HERSHEY_SIMPLEX, 0.2,color, 1)
            ids = self.estimate_id()
            cv2.putText(frame, f"{ids}", (int(self.position[0])-20, int(self.position[1])-10), cv2.FONT_HERSHEY_SIMPLEX, 0.3,color, 1)
            



class Camera:

    def __init__(self, marker_id_to_color_id):
        self.marker_id_to_color_id = marker_id_to_color_id
        self.markers = []

    def detect_markers(self,name, cap, window_pos):
        id_to_xy = [(0,0)] * 30  # 最大30個のマーカーを想定
        i = 0
        cap.set(cv2.CAP_PROP_EXPOSURE, -9)  # 負の値が有効な場合もある
        cap.set(cv2.CAP_PROP_GAIN, 0)       # ゲインを抑えるとノイズ減少
        cap.set(cv2.CAP_PROP_BRIGHTNESS, 0) # 明るさ補正を無効に近づける

        # 右上にウィンドウを表示（x=1000, y=50 は適宜調整）
        cv2.namedWindow(name)
        cv2.moveWindow(name, window_pos[0], window_pos[1])

        while True:


            # time.sleep(0.5)  # 少し待つ（必要に応じて調整）



            ret, frame = cap.read()
            if not ret:
                print("カメラ読み取り失敗")
                continue

            i += 1
            

        

            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            threshold=100
            _, threshold_frame = cv2.threshold(gray_frame, threshold, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(threshold_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            # print(f"{name} {i} フレーム内の輪郭数: {len(contours)}")
            # cv2.drawContours(frame, contours, -1, (0, 100, 0), 2)
            detect_marker_positions = [] 
            detect_marker_mean_colors = [] 
            for cnt in contours:


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
                    
                    detect_marker_mean_colors.append(mean_color[:3])  # Aは不要なので除外
                    # 中心にマーク（赤い小さい円）
                    cv2.circle(frame, (cx, cy), 1, (0, 0, 255), -1)
                    detect_marker_positions.append([cx, cy])
                    # 輪郭を描画（緑色の線）
                    cv2.drawContours(frame, [cnt], -1, (0, 255, 0), 1)

            # --- forループの外に移動 ---
            # markers は Marker クラスのリスト
            markers_positions = np.array([m.position for m in self.markers], dtype=np.float32)
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

            max_dist = 5000
            matched_old = []           # 「残存マーカー」のインデックス（過去フレームの markers リスト内でマッチしたもの）
            matched_new_valid = []     # 「残存マーカーに対応する新しい点」のインデックス（detect_marker_positions 内でマッチしたもの）

            # 残存マーカー更新
            for i, j in zip(matched_prev, matched_new):
                if cost_matrix[i, j] <= max_dist:
                    update_marker=self.markers[i]
                    update_marker.update_position( detect_marker_positions[j])
                    update_marker.update_color( detect_marker_mean_colors[j])
                    matched_old.append(i)
                    matched_new_valid.append(j)

            to_remove = []  # 削除対象のインデックス
            for i in range(len(self.markers)):
                if i not in matched_old:
                    to_remove.append(i)
            # 逆順で削除
            for i in sorted(to_remove, reverse=True):
                del self.markers[i]

            # 追加：matched_new_valid に入っていない新しい点
            for j in range(len(detect_marker_positions)):
                if j not in matched_new_valid:
                    self.markers.append(Marker(detect_marker_positions[j], self.marker_id_to_color_id))
                                    



            for i,m in enumerate(self.markers):
                m.draw_info(frame)
                # cv2.putText(frame, f"ID:{i}", (int(m.position[0])+5, int(m.position[1])-5), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
            




            # 表示用にフレームを2倍にリサイズ
            frame = cv2.resize(frame, (frame.shape[1] * 2, frame.shape[0] * 2), interpolation=cv2.INTER_CUBIC)
            cv2.imshow(name, frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break


        cap.release()
        cv2.destroyWindow(name)


    def probability_update(self):
        # pass
        for m in self.markers:
            m.probability_update()