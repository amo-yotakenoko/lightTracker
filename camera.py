import cv2
import time
import numpy as np
from  color_distance import find_marker 
from scipy.spatial import distance
from scipy.optimize import linear_sum_assignment
import marker_update
from marker import Marker
import chArUco_detect
import chArUco_board

class Camera:

    def __init__(self, marker_id_to_color_id):
        self.marker_id_to_color_id = marker_id_to_color_id
        self.markers = []
        self.frame = None

        self.camera_position = None
        self.camera_rotation = None

        self.height, self.width = None, None
        self.cx, self.cy = None, None
        self.fx, self.fy = None, None
        self.camera_matrix = None
        self.dist_coeffs = np.zeros((5, 1))  # 歪み補正なし

        self.corners ,self.ids,self.rvec, self.tvec=None,None,None,None

    def _initialize_camera_parameters(self, cap):
        ret, self.frame = cap.read()
        if not ret:
            raise RuntimeError("カメラフレームの読み取りに失敗しました。")
        self.height, self.width = self.frame.shape[:2]
        self.cx = self.width / 2
        self.cy = self.height / 2
        self.fx = self.fy = self.width  # 仮値でOK
        self.camera_matrix = np.array([[self.fx, 0, self.cx],
                                       [0, self.fy, self.cy],
                                       [0, 0, 1]], dtype=float)

    def get_camera_pose(self):
        if self.frame is None:
            return None, None
        return chArUco_detect.get_camera_pose(self.frame, self)

    def detect_markers(self, name, cap, window_pos):
       
        cv2.namedWindow(name)
        cv2.moveWindow(name, window_pos[0], window_pos[1])

        try:
            self._initialize_camera_parameters(cap)
        except RuntimeError as e:
            print(e)
            return

        cap.set(cv2.CAP_PROP_BRIGHTNESS, 100)
        cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)

        print("カメラの姿勢を推定中...")
        while self.camera_position is None or self.camera_rotation is None:
            ret, self.frame = cap.read()
            if not ret:
                print("カメラが見つかりません。")
                break

            gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            # --- マーカー検出 ---
            self.corners, self.ids, _ = cv2.aruco.detectMarkers(gray, chArUco_board.aruco_dict)

            self.camera_position, self.camera_rotation = self.get_camera_pose()

            # 表示用にフレームを2倍にリサイズ
            display_frame = cv2.resize(self.frame, (self.frame.shape[1] * 2, self.frame.shape[0] * 2), interpolation=cv2.INTER_CUBIC)
            cv2.imshow(name, display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        print("カメラ姿勢の推定完了。")


        cap.set(cv2.CAP_PROP_EXPOSURE, -9)
        # time.sleep(1)
        while True:
            ret, self.frame = cap.read()
            if not ret:
                print("カメラ読み取り失敗")
                continue

            gray_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
            _, threshold_frame = cv2.threshold(gray_frame, 100, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(threshold_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            detect_marker_positions = []
            detect_marker_mean_colors = []
            for cnt in contours:
                M = cv2.moments(cnt)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    mask = np.zeros(self.frame.shape[:2], dtype=np.uint8)
                    cv2.drawContours(mask, [cnt], -1, 255, -1)
                    mean_color = cv2.mean(self.frame, mask=mask)
                    detect_marker_mean_colors.append(mean_color[:3])
                    cv2.circle(self.frame, (cx, cy), 1, (0, 0, 255), -1)
                    detect_marker_positions.append([cx, cy])
                    cv2.drawContours(self.frame, [cnt], -1, (0, 255, 0), 1)

            markers_positions = np.array([m.position for m in self.markers], dtype=np.float32)
            detect_marker_positions = np.array(detect_marker_positions, dtype=np.float32)

            if markers_positions.size > 0 and detect_marker_positions.size > 0:
                cost_matrix = distance.cdist(markers_positions, detect_marker_positions)
                matched_prev, matched_new = linear_sum_assignment(cost_matrix)

                max_dist = 5000
                matched_old = []
                matched_new_valid = []

                for i, j in zip(matched_prev, matched_new):
                    if cost_matrix[i, j] <= max_dist:
                        self.markers[i].update_position(detect_marker_positions[j])
                        self.markers[i].update_color(detect_marker_mean_colors[j])
                        matched_old.append(i)
                        matched_new_valid.append(j)

                to_remove = [i for i, m in enumerate(self.markers) if i not in matched_old]
                for i in sorted(to_remove, reverse=True):
                    del self.markers[i]

                for j in range(len(detect_marker_positions)):
                    if j not in matched_new_valid:
                        self.markers.append(Marker(detect_marker_positions[j], self.marker_id_to_color_id))
            elif detect_marker_positions.size > 0:
                for j in range(len(detect_marker_positions)):
                    self.markers.append(Marker(detect_marker_positions[j], self.marker_id_to_color_id))
            else:
                self.markers.clear()

            for m in self.markers:
                m.draw_info(self.frame)

            frame = cv2.aruco.drawDetectedMarkers(self.frame, self.corners, self.ids)
            cv2.drawFrameAxes(frame, self.camera_matrix, self.dist_coeffs,self.rvec, self.tvec, 25)
            display_frame = cv2.resize(self.frame, (self.frame.shape[1] * 2, self.frame.shape[0] * 2), interpolation=cv2.INTER_CUBIC)
            cv2.imshow(name, display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyWindow(name)

    def probability_update(self):
        for m in self.markers:
            m.probability_update()
