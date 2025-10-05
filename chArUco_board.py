import cv2
import numpy as np
import sys
from PIL import Image
import matplotlib.pyplot as plt

# --- 設定パラメータ ---

# 1. ボードのレイアウト
# グリッドの交点の数 (X方向, Y方向)
squares_x = 42 // 8+1
squares_y = 30 // 8 +1
# 実際に描画される格子点の数は (squares_x-1, squares_y-1) になります

# 2. ArUco辞書の選択
# 例: DICT_5X5_1000 (5x5ビット, 1000個のマーカー)
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)

# 3. サイズ（世界座標系/ミリメートル）- A2用紙の制約内で調整
# ArUcoマーカーを配置する四角形（白い部分と黒い部分）の一辺の長さ (mm)
square_length_mm = 30.0 
# ArUcoマーカー自体の一辺の長さ (mm)
# square_length_mm より小さくする必要があります
marker_length_mm = 20.0 

# 4. 出力画像サイズ（ピクセル）
# A2サイズ（297*2 x 420 mm）を300 DPIで印刷する場合に必要なピクセル数に近い値

output_width_px = (297*2)*10
output_height_px = 420*10

# --- ChArUcoボードの生成 ---

# 1. ChArUcoBoardオブジェクトの作成
board = cv2.aruco.CharucoBoard(
    size=(squares_x, squares_y),
    squareLength=square_length_mm,
    markerLength=marker_length_mm,
    dictionary=aruco_dict
)


if __name__ == "__main__":

    # --- カメラパラメータ（例：仮の値、実際はキャリブレーションで得た値を使う）---
    # fx, fy, cx, cy はカメラ内部パラメータ



    cap = cv2.VideoCapture(0)


    cap.set(cv2.CAP_PROP_BRIGHTNESS, 128)
    cap.set(cv2.CAP_PROP_CONTRAST, 32)
    cap.set(cv2.CAP_PROP_SATURATION, 32)        # 色合い/鮮やかさに相当
    cap.set(cv2.CAP_PROP_HUE, 0)                # 色相（必要なら）
    cap.set(cv2.CAP_PROP_GAIN, 64)
    cap.set(cv2.CAP_PROP_WHITE_BALANCE_BLUE_U, 4300)  # ホワイトバランス（カメラによる）
    if not cap.isOpened():
        print("カメラが見つかりません。")
        exit()


    ret, frame = cap.read()
    height, width = frame.shape[:2]
    cx = width / 2
    cy = height / 2
    fx = fy = width  # 仮値でOK
    camera_matrix = np.array([[fx, 0, cx],
                            [0, fy, cy],
                            [0, 0, 1]], dtype=float)
    dist_coeffs = np.zeros((5, 1))  # 歪み補正なし

    # --- matplotlibで3D表示の準備 ---
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    plt.ion() # インタラクティブモードをオン
    cv2.namedWindow("Detected ChArUco")

    while True:

        ret, frame = cap.read()
        if not ret:
            print("フレーム取得失敗。")
            exit()

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # --- マーカー検出 ---
        corners, ids, _ = cv2.aruco.detectMarkers(gray, aruco_dict)

        if ids is not None and len(ids) > 0:
            # 検出結果を画像に描画
            frame = cv2.aruco.drawDetectedMarkers(frame.copy(), corners, ids)

            # --- ChArUcoコーナーを補間 ---
            ret, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(
                markerCorners=corners,
                markerIds=ids,
                image=gray,
                board=board
            )

            if ret > 4:
                # --- 姿勢推定 ---
                valid, rvec, tvec = cv2.aruco.estimatePoseCharucoBoard(
                    charuco_corners, charuco_ids, board, camera_matrix, dist_coeffs, None, None)

                if valid:
                    cv2.drawFrameAxes(frame, camera_matrix, dist_coeffs, rvec, tvec, 25)

                    # --- 個々のマーカーの姿勢を推定 ---
                    rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
                        corners, marker_length_mm, camera_matrix, dist_coeffs)



                    # --- matplotlibで3D表示 ---
                    # 回転ベクトルを回転行列に変換
                    R, _ = cv2.Rodrigues(rvec)

                    # カメラ座標系 → ボード座標系 変換
                    camera_position = -R.T @ tvec

                    # 3Dプロットをクリア
                    ax.cla()

                    # 原点（ボード中心）をプロット
                    ax.scatter(0, 0, 0, color='red', label='Board origin')

                    # カメラ位置をプロット
                    ax.scatter(camera_position[0], camera_position[1], camera_position[2],
                            color='blue', label='Camera position')

                    # --- 個々のマーカーの位置をプロット ---
                    if tvecs is not None:
                        for i, tvec_marker in enumerate(tvecs):
                            # マーカー位置をボード座標系に変換
                            marker_pos_board = R.T @ (tvec_marker.T - tvec)
                            if i == 0:
                                ax.scatter(marker_pos_board[0], marker_pos_board[1], marker_pos_board[2],
                                           color='orange', marker='x', label='Marker')
                            else:
                                ax.scatter(marker_pos_board[0], marker_pos_board[1], marker_pos_board[2],
                                           color='orange', marker='x')

                    # カメラの向きベクトル（3軸）を描画
                    axis_length = 50
                    # X軸 (赤)
                    x_axis_cam = np.array([[axis_length, 0, 0]]).T
                    x_axis_board = R.T @ x_axis_cam + camera_position
                    ax.plot([camera_position[0, 0], x_axis_board[0, 0]],
                            [camera_position[1, 0], x_axis_board[1, 0]],
                            [camera_position[2, 0], x_axis_board[2, 0]], color='red', label='Cam X')
                    # Y軸 (緑)
                    y_axis_cam = np.array([[0, axis_length, 0]]).T
                    y_axis_board = R.T @ y_axis_cam + camera_position
                    ax.plot([camera_position[0, 0], y_axis_board[0, 0]],
                            [camera_position[1, 0], y_axis_board[1, 0]],
                            [camera_position[2, 0], y_axis_board[2, 0]], color='green', label='Cam Y')
                    # Z軸 (青)
                    z_axis_cam = np.array([[0, 0, axis_length]]).T
                    z_axis_board = R.T @ z_axis_cam + camera_position
                    ax.plot([camera_position[0, 0], z_axis_board[0, 0]],
                            [camera_position[1, 0], z_axis_board[1, 0]],
                            [camera_position[2, 0], z_axis_board[2, 0]], color='blue', label='Cam Z')


                    # ax.view_init(elev=30, azim=60)

                    # 軸の範囲を固定
                    ax.set_xlim([-200, 200])
                    ax.set_ylim([-200, 200])
                    ax.set_zlim([0, -400])
                    
                    # 描画を更新
                    plt.draw()
                    plt.pause(0.01)

                  
           
                else:
                    print("姿勢推定に失敗しました。")
            else:
                print("ChArUcoコーナーの補間が不十分です。")
        else:
            print("マーカーが検出できませんでした。")
        cv2.imshow("Detected ChArUco", frame)
        cv2.moveWindow("Detected ChArUco", 0, 0)

        # waitKey(1) にすると 1ms ごとに次のフレームへ進む
        # 'q' キーで終了
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

