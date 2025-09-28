import cv2
import numpy as np
import time
import os
import serial

arduino = serial.Serial('COM4', 115200, timeout=1)


def led_set(index, color):
    """指定したLEDの色を送信"""
    r, g, b = color  # タプルを展開
    arduino.write(bytes([index, r, g, b]))

def led_show():
    """1 LEDの色を送信"""
    arduino.write(bytes([254,0,0,0]))

def led_clear():
    """1 LEDの色を送信"""
    arduino.write(bytes([255,0,0,0]))




def main():
    active_marker_id=0
    """
    カメラ映像から最も明るい点と最も暗い点、そして特定の色（青、緑、赤）に
    最も近い点を検出し、リアルタイムでコンソールと映像上に表示する。
    """
    print("プログラムを開始します。'q'キーを押すと終了します。")

    # --- GUI利用可否の判定 ---
    is_gui_available = True

    # --- カメラの設定 ---
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("エラー: カメラを開けませんでした。")
        return

    prev_time = time.time()
    fps = 0
    is_first_print = True

    while True:
        active_marker_id+=1
        if active_marker_id>=30:
            active_marker_id=0
        

        led_set(active_marker_id,(255,0,0))
        led_show()
       

        # === 1. カメラ映像の処理 ===
        ret, camera_frame = cap.read()
        if not ret:
            print("エラー: カメラフレームを読み込めませんでした。")
            break


        # === 色検出と情報保存 ===
        frame_int = camera_frame.astype(np.int16)
        target_colors = {"Blue": np.array([255, 0, 0]), "Green": np.array([0, 255, 0]), "Red": np.array([0, 0, 255])}
        color_data = {}
        for name, color_val in target_colors.items():
            distance_map = np.sum(np.abs(frame_int - color_val), axis=2)
            _min_dist, _max_dist, min_loc, _max_loc = cv2.minMaxLoc(distance_map)
            color_data[name] = {'loc': min_loc, 'dist': _min_dist}
            bgr_color = tuple(map(int, color_val))
            cv2.circle(camera_frame, min_loc, 10, bgr_color, 2)
            cv2.putText(camera_frame, name, (min_loc[0] + 15, min_loc[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, bgr_color, 2)

        # === FPS計算 ===
        current_time = time.time()
        elapsed_time = current_time - prev_time
        if elapsed_time > 0:
            fps = 1 / elapsed_time
        prev_time = current_time
        cv2.putText(camera_frame, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        # === コンソールへの整形出力 ===
        if not is_first_print:
            # 4行上にカーソルを移動 (FPS1 + 色情報3)
            print("\x1b[4A", end="")

        print(f"FPS: {fps:.2f}\x1b[K")
        for name in target_colors.keys():
            data = color_data[name]
            pos_str = f"({data['loc'][0]}, {data['loc'][1]})"
            dist_str = f"{data['dist']:.0f}"
            line = f"{name} closest at {pos_str} with distance {dist_str}"
            print(f"{line}\x1b[K")

        if is_first_print:
            is_first_print = False

        # === ウィンドウを表示 (GUIが利用可能な場合のみ) ===
        if is_gui_available:
            cv2.imshow('Camera Feed', camera_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # 後処理
    cap.release()
    if is_gui_available:
        cv2.destroyAllWindows()
    # 終了時に整形された表示をクリアするため、数行の改行を出力
    print("\n" * 4)
    print("プログラムを終了しました。")

if __name__ == '__main__':
    main()


