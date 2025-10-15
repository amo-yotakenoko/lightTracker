import numpy as np
import cv2
import marker_update
import threading

class Marker:

   
    def __init__(self, position, marker_id_to_color_id):
        self.track = []
        self._lock = threading.Lock()
        self.update_position(position)
        self.color=None
        self.marker_color_id=-1
        self.marker_id_to_color_id = marker_id_to_color_id

        self.reset_probability_distribution()
        

    def reset_probability_distribution(self):
        self.probability_distribution=np.array([1/30]*30)
        

    def update_position(self, new_position):
        with self._lock:
            self.position = new_position
            self.track.append(self.position.copy())
            if len(self.track) > 50:  # トラックの長さを50に制限
                self.track.pop(0)


    def update_color(self, color):
        with self._lock:
            distances = [np.linalg.norm(c - np.array(color)) for c in marker_update.marker_bgrs]
            self.marker_color_id = np.argmin(distances)

    
    def now_probability(self):
        with self._lock:
            return self._now_probability_unsafe()

    def _now_probability_unsafe(self):
        now_probability_distribution=np.array([0.1]*30)
        for i in range(30):
            # print(self.marker_id_to_color_id,self.marker_color_id,i,self.marker_color_id == self.marker_id_to_color_id[i])

            if self.marker_color_id == self.marker_id_to_color_id[i]:
                now_probability_distribution[i]=10

            # 正規化
        now_probability_distribution /= now_probability_distribution.sum()
        # print(now_probability_distribution,self.entropy())
        return now_probability_distribution


    def now_probability(self):
        with self._lock:
            return self._now_probability_unsafe()

    def probability_update(self):
        with self._lock:
            self.probability_distribution = self.probability_distribution * self._now_probability_unsafe()
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
            if(entropy>0):
                cv2.putText(frame, f"{entropy:.3f}bit", (int(self.position[0])+10, int(self.position[1])-5), cv2.FONT_HERSHEY_SIMPLEX, 0.2,color, 1)
            ids = self.estimate_id()
            cv2.putText(frame, f"{ids}", (int(self.position[0])-20, int(self.position[1])-10), cv2.FONT_HERSHEY_SIMPLEX, 0.3,color, 1)
