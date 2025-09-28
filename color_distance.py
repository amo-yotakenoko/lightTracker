import cv2
import numpy as np
def find_marker(frame_bgr, bgr_color):
   
    # RGBモード: 単純な色差の絶対値の和
    frame_int = frame_bgr.astype(np.int16)
    bgr_color_arr = np.array(bgr_color, dtype=np.int16)
    distance_map = np.sum(np.abs(frame_int - bgr_color_arr), axis=2).astype(np.uint16)
    _min_dist, _max_dist, min_loc, _max_loc = cv2.minMaxLoc(distance_map)
    marker_pos=np.array(min_loc, dtype=np.float32)
    
    gy, gx = np.gradient( cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32))
    height, width = frame_bgr.shape[:2]
    for i in range(100):
        x, y = int(marker_pos[0]), int(marker_pos[1])

        # 勾配方向に向かって移動（距離が小さくなる方向）
        dx = gx[y, x]/10
        dy = gy[y, x]/10

        if(np.hypot(dx, dy)<1):
            # print(f"break {i} {dx} {dy}")
            break

     
            
        cv2.line(frame_bgr, (x, y), (int(x + dx ), int(y + dy )), (255, 255, 0), 1)

        # 新しい位置
        marker_pos[0] += dx
        marker_pos[1] += dy
        
        # フレーム範囲内に収めるようにクリッピング
        marker_pos[0] = np.clip(marker_pos[0], 0, width - 1)
        marker_pos[1] = np.clip(marker_pos[1], 0, height - 1)
    
    
    return marker_pos