import cv2
import numpy as np
import sys
from PIL import Image
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation
import matplotlib.patches as patches

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


def draw_uv_line(ax, camera_matrix, uv, camera_position=np.zeros(3)):
    """
    カメラから画像上のピクセル uv への線を描画する（3D座標系）
    
    Parameters
    ----------
    ax : matplotlib 3D axis
    camera_matrix : np.array shape(3,3) カメラ内部行列
    uv : tuple (u,v) 画像座標
    camera_position : np.array shape(3,) カメラ位置（デフォルト原点）
    length : float 線の長さ（任意スケール）
    color : str 線の色
    """
    u, v = uv
    fx = camera_matrix[0,0]
    fy = camera_matrix[1,1]
    cx = camera_matrix[0,2]
    cy = camera_matrix[1,2]
    
    # 正規化カメラ座標系
    x_n = (u - cx) / fx
    y_n = (v - cy) / fy
    z_n = 1.0
    
    # 単位ベクトル
    direction = np.array([x_n, y_n, z_n])
    direction /= np.linalg.norm(direction)
    
    # 線の終点
    end_point = camera_position + direction * 100
    print(camera_position,end_point)
    # 3D線を描画
    ax.plot([camera_position[0,0], end_point[0,0]],
            [camera_position[1,0], end_point[1,0]],
            [camera_position[2,0], end_point[2,0]])


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
                    # ボードを「壁」に見せるための変換
                    # ボード座標系(B)をワールド座標系(W)に変換するための回転
                    # Scipyを使用して回転を定義: X軸90度 -> Y軸90度 (extrinsic)
                    rot = Rotation.from_euler('XYZ', [90, 0,-90], degrees=True)
                    #ボードからワールドに
                    R_W_B = rot.as_matrix()

                    # 1. カメラのポーズをワールド座標系に変換
                    R_C_B, _ = cv2.Rodrigues(rvec) # Board -> Camera の回転
                    t_C_B = tvec

                    # カメラ位置 (World座標系)
                    p_b_cam_origin = -R_C_B.T @ t_C_B
                    p_w_cam_origin = R_W_B @ p_b_cam_origin
                    camera_position = p_w_cam_origin

                    # カメラ向き (World座標系)
                    R_W_C = R_W_B @ R_C_B.T
                    R = R_W_C # 描画で使う回転行列を更新

                    # 3Dプロットをクリア
                    ax.cla()

                    # ワールド座標系の原点（＝ボードの原点）をプロット
                    ax.scatter(0, 0, 0, color='black', label='World Origin')

                    # カメラ位置をプロット
                    ax.scatter(camera_position[0], camera_position[1], camera_position[2],
                            color='blue', label='Camera position')
                    
                    
                    x1, y1 = squares_y * square_length_mm, -squares_x * square_length_mm
                    # 頂点を順に並べる（時計回り）
                    rect_path = np.array([
                        [0,0, 0],  # 左下
                        [x1,0, 0],  # 右下
                        [x1,0, y1],  # 右上
                        [0,0, y1],  # 左上
                        [0,0, 0],  # 左下に戻る（閉じる）
                    ])
                    # 線で描画
                    ax.plot(rect_path[:,0], rect_path[:,1], rect_path[:,2], color='r', linewidth=2)


                    # --- 個々のマーカーの位置をプロット ---
                    if tvecs is not None:
                        for i, tvec_marker in enumerate(tvecs):
                            # マーカー位置をボード座標系に変換
                            p_b_marker = R_C_B.T @ (tvec_marker.T - t_C_B)
                            # マーカー位置をワールド座標系に変換
                            p_w_marker = R_W_B @ p_b_marker
                            
                            if i == 0:
                                ax.scatter(p_w_marker[0], p_w_marker[1], p_w_marker[2],
                                           color='orange', marker='x', label='Marker')
                            else:
                                ax.scatter(p_w_marker[0], p_w_marker[1], p_w_marker[2],
                                           color='orange', marker='x')
                    

                    # カメラの向きベクトル（3軸）を描画 (World座標系基準)
                    axis_length = 50
                    # R は R_W_C (Camera -> World の回転)
                    # X軸 (赤)
                    x_axis_world = R @ np.array([[axis_length, 0, 0]]).T + camera_position
                    ax.plot([camera_position[0, 0], x_axis_world[0, 0]],
                            [camera_position[1, 0], x_axis_world[1, 0]],
                            [camera_position[2, 0], x_axis_world[2, 0]], color='red', label='Cam X')
                    # Y軸 (緑)
                    y_axis_world = R @ np.array([[0, axis_length, 0]]).T + camera_position
                    ax.plot([camera_position[0, 0], y_axis_world[0, 0]],
                            [camera_position[1, 0], y_axis_world[1, 0]],
                            [camera_position[2, 0], y_axis_world[2, 0]], color='green', label='Cam Y')
                    # Z軸 (青)
                    z_axis_world = R @ np.array([[0, 0, axis_length]]).T + camera_position
                    ax.plot([camera_position[0, 0], z_axis_world[0, 0]],
                            [camera_position[1, 0], z_axis_world[1, 0]],
                            [camera_position[2, 0], z_axis_world[2, 0]], color='blue', label='Cam Z')
                    

                    # 各角を中心からの座標に変更
                    uv_points = [
                        (0 , 0 ),
                        # (0 - cx, 0 - cy),       # 左上
                        # (0 - cx, height - cy),  # 左下
                        # (width - cx, 0 - cy),   # 右上
                        # (width - cx, height - cy) # 右下
                    ]
                    for uv in uv_points:
                        draw_uv_line(ax, camera_matrix, uv, camera_position)

                    ax.set_xlabel("World X (mm)")
                    ax.set_ylabel("World Y (mm)")
                    ax.set_zlabel("World Z (mm)")
                    # ax.legend()
                    # ax.view_init(elev=30, azim=60)

                    # 軸の範囲を固定
                    ax.set_xlim([200, -200])
                    ax.set_ylim([000, 400])
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

