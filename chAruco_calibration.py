import cv2
from cv2 import aruco
import numpy as np
import chArUco_board
import time
# -----------------------------
# 1. CharucoBoard の作成
# -----------------------------

board = chArUco_board.board

# -----------------------------
# 2. カメラ準備
# -----------------------------




def load_camera_params(filename="camera_params.npz"):
    """
    camera_params.npz を読み込む関数。
    読み込みに失敗した場合は None を返す。

    Returns
    -------
    camera_matrix : np.array or None
    dist_coeffs : np.array or None
    """
    try:
        data = np.load(filename)
        camera_matrix = data.get("camera_matrix", None)
        dist_coeffs = data.get("dist_coeffs", None)
        print(f"{filename} を読み込みました。")
    except Exception:
        camera_matrix = None
        dist_coeffs = None
        print(f"{filename} の読み込みに失敗しました。None を返します。")
    
    return camera_matrix, dist_coeffs



def calc_camera_params(save_interval = 2.0):
    cap = None
    all_corners = []
    all_ids = []
    image_size = None
    last_save_time = 0   # 前回保存時間
    image_size= None

    cap=cv2.VideoCapture(0)
    print("カメラで CharucoBoard を写して 's' キーで画像を保存、'q' で終了")
    cap.set(cv2.CAP_PROP_BRIGHTNESS, 100)
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1)
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # ArUco マーカー検出
        corners, ids, rejected = aruco.detectMarkers(gray, chArUco_board.aruco_dict)
        if len(corners) > 0:
            aruco.drawDetectedMarkers(frame, corners, ids)

            # Charuco コーナー補間
            retval, charuco_corners, charuco_ids = aruco.interpolateCornersCharuco(
                corners, ids, gray, chArUco_board.board
            )

            if charuco_corners is not None and charuco_ids is not None:
                aruco.drawDetectedCornersCharuco(frame, charuco_corners, charuco_ids)

                # --- 自動保存 ---
                now = time.time()
                if len(charuco_corners) > 3 and (now - last_save_time) > save_interval:
                    all_corners.append(charuco_corners)
                    all_ids.append(charuco_ids)
                    last_save_time = now
                    if image_size is None:
                        image_size = gray.shape[::-1]
                    print(f"自動保存: {len(all_corners)} 枚目")

        cv2.imshow('Charuco Capture', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # -----------------------------
    # 3. キャリブレーション
    # -----------------------------
    if len(all_corners) > 0:
        ret, camera_matrix, dist_coeffs, rvecs, tvecs = aruco.calibrateCameraCharuco(
            charucoCorners=all_corners,
            charucoIds=all_ids,
            board=board,
            imageSize=image_size,
            cameraMatrix=None,
            distCoeffs=None
        )

        print("カメラ行列:\n", camera_matrix)
        print("歪み係数:\n", dist_coeffs)

        # -----------------------------
        # 4. 歪み補正確認
        # -----------------------------
        # cap = cv2.VideoCapture(0)
        # print("リアルタイムで歪み補正表示: 'q' で終了")
        # while True:
        #     ret, frame = cap.read()
        #     if not ret:
        #         break
        #     h, w = frame.shape[:2]
        #     new_camera_matrix, roi = cv2.getOptimalNewCameraMatrix(
        #         camera_matrix, dist_coeffs, (w, h), 1, (w, h)
        #     )
        #     undistorted = cv2.undistort(frame, camera_matrix, dist_coeffs, None, new_camera_matrix)
        #     cv2.imshow('Undistorted', undistorted)
        #     if cv2.waitKey(1) & 0xFF == ord('q'):
        #         break
        cap.release()
        cv2.destroyAllWindows()

        # -----------------------------
        # 5. パラメータ保存
        # -----------------------------
      
        return camera_matrix, dist_coeffs
    else:
        print("十分な Charuco コーナーが検出されませんでした。")



camera_matrix,dist_coeffs= load_camera_params("camera_params.npz")

if (camera_matrix is None) or (dist_coeffs is None):
    camera_matrix,dist_coeffs= calc_camera_params()
    np.savez("camera_params.npz", camera_matrix=camera_matrix, dist_coeffs=dist_coeffs)
    print("カメラパラメータを 'camera_params.npz' に保存しました。")

