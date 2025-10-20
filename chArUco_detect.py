import cv2
import numpy as np
import sys
from PIL import Image
import matplotlib.pyplot as plt
from scipy.spatial.transform import Rotation
import matplotlib.patches as patches
import chArUco_board
# --- 設定パラメータ ---



def draw_uv_line(ax, camera_matrix, uv, camera_position,R):
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
    x_n = u  / fx
    y_n = v  / fy
    z_n = 1.0
    

    
    
    # print(f"{direction=}")
    # # print(camera_position,end_point)
    # # 3D線を描画
    # ray_end = R @ direction + camera_position
    # ax.plot([camera_position[0, 0], ray_end[0, 0]],
    #         [camera_position[1, 0], ray_end[1, 0]],
    #         [camera_position[2, 0], ray_end[2, 0]])
    
    ray_end = R @ np.array([[x_n*1000, y_n*1000, z_n*1000]]).T + camera_position
    ax.plot([camera_position[0, 0], ray_end[0, 0]],
                            [camera_position[1, 0], ray_end[1, 0]],
                            [camera_position[2, 0], ray_end[2, 0]])
    

def get_camera_pose(frame, camera, ax=None):




    if camera.ids is not None and len(camera.ids) > 0:
        # 検出結果を画像に描画
        frame = cv2.aruco.drawDetectedMarkers(frame, camera.corners, camera.ids)

        # --- ChArUcoコーナーを補間 ---
        ret, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(
            markerCorners=camera.corners,
            markerIds=camera.ids,
            image=frame,
            board=chArUco_board.board
        )

        if ret > 4:
            # --- 姿勢推定 ---
            valid, camera.rvec, camera.tvec = cv2.aruco.estimatePoseCharucoBoard(
                charuco_corners, charuco_ids, chArUco_board.board, camera.camera_matrix, camera.dist_coeffs, None, None)

            if valid:
                cv2.drawFrameAxes(frame, camera.camera_matrix, camera.dist_coeffs, camera.rvec, camera.tvec, 25)

                # --- 個々のマーカーの姿勢を推定 ---
                rvecs, tvecs, _ = cv2.aruco.estimatePoseSingleMarkers(
                    camera.corners, chArUco_board.marker_length_mm, camera.camera_matrix, camera.dist_coeffs)



                # --- matplotlibで3D表示 ---
                # ボードを「壁」に見せるための変換
                # ボード座標系(B)をワールド座標系(W)に変換するための回転
                # Scipyを使用して回転を定義: X軸90度 -> Y軸90度 (extrinsic)
                rot = Rotation.from_euler('XYZ', [90, 0,-90], degrees=True)
                #ボードからワールドに
                R_W_B = rot.as_matrix()

                # 1. カメラのポーズをワールド座標系に変換
                R_C_B, _ = cv2.Rodrigues(camera.rvec) # Board -> Camera の回転
                t_C_B = camera.tvec

                # カメラ位置 (World座標系)
                p_b_cam_origin = -R_C_B.T @ t_C_B
                p_w_cam_origin = R_W_B @ p_b_cam_origin
                camera_position = p_w_cam_origin

                # カメラ向き (World座標系)
                R_W_C = R_W_B @ R_C_B.T
                R = R_W_C # 描画で使う回転行列を更新






                
                


                    # --- 個々のマーカーの位置をプロット ---
                if ax is not None:
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
                



                


                return camera_position,R
        
            else:
                print("姿勢推定に失敗しました。")
        else:
            print("ChArUcoコーナーの補間が不十分です。")
            
    else:
        print("マーカーが検出できませんでした。")
    return None,None


def plot_camera_pose(camera_position,R,ax):
        
        if(R is None or camera_position is None):
            return 
        # カメラ位置をプロット
        ax.scatter(camera_position[0], camera_position[1], camera_position[2],
                color='blue', label='Camera position')

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
            (-cx, -cy),   # 左上
            (-cx, cy),    # 左下
            (cx, -cy),    # 右上
            (cx, cy)      # 右下
        ]
        for uv in uv_points:
            draw_uv_line(ax, camera_matrix, uv, camera_position,R)




if __name__ == "__main__":

    # --- カメラパラメータ（例：仮の値、実際はキャリブレーションで得た値を使う）---
    # fx, fy, cx, cy はカメラ内部パラメータ


 
    cap = cv2.VideoCapture(0)




    cap.set(cv2.CAP_PROP_BRIGHTNESS, 100)
    # cap.set(cv2.CAP_PROP_EXPOSURE, 0) 
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1) 

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

    camera_position,R=None,None
    while True:
        ax.cla()

        ret, frame = cap.read()
        if not ret:
            print("フレーム取得失敗。")
            exit()
                            

        new_camera_position, new_R = get_camera_pose(frame, camera_matrix, dist_coeffs, ax)

        # nullでなければ更新
        if new_camera_position is not None and new_R is not None:
            camera_position = new_camera_position
            R = new_R

        plot_camera_pose(camera_position,R,ax)



        x1, y1 = chArUco_board.squares_y * chArUco_board.square_length_mm, -chArUco_board.squares_x * chArUco_board.square_length_mm
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

        
        cv2.imshow("Detected ChArUco", frame)
        cv2.moveWindow("Detected ChArUco", 0, 0)

        # waitKey(1) にすると 1ms ごとに次のフレームへ進む
        # 'q' キーで終了
        key = cv2.waitKey(1)
        if key == ord('q'):
            break

