import cv2
import numpy as np
import cv2.aruco as aruco
import time

# --- Charuco Board 作成 ---
squares_x = 5
squares_y = 7
square_length_mm = 30
marker_length_mm = 20
aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)

board = aruco.CharucoBoard_create(
    squaresX=squares_x,
    squaresY=squares_y,
    squareLength=square_length_mm,
    markerLength=marker_length_mm,
    dictionary=aruco_dict
)

# --- カメラ0番を開く ---
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("カメラを開けませんでした")

all_corners = []
all_ids = []
img_size = None

# 撮影制御
captured_frames = 0
target_frames = 30
last_capture_time = 0
capture_interval = 0.5  # 秒単位でフレーム間隔を空ける

print("Charuco コーナーのキャリブレーション用画像を撮影します。")
print(f"{target_frames} 枚撮影したら自動で処理が始まります。")

while captured_frames < target_frames:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    if img_size is None:
        img_size = gray.shape[::-1]

    # ArUco マーカー検出
    corners, ids, rejected = aruco.detectMarkers(gray, aruco_dict)

    if ids is not None and len(ids) > 0:
        retval, charuco_corners, charuco_ids = aruco.interpolateCornersCharuco(
            corners, ids, gray, board
        )
        if charuco_corners is not None and charuco_ids is not None:
            # 連続フレームで同じものをカウントしないために時間間隔をチェック
            if time.time() - last_capture_time > capture_interval:
                all_corners.append(charuco_corners)
                all_ids.append(charuco_ids)
                captured_frames += 1
                last_capture_time = time.time()
                print(f"{captured_frames}/{target_frames} 枚撮影しました")

            # 検出したコーナーを描画
            aruco.drawDetectedCornersCharuco(frame, charuco_corners, charuco_ids)

    cv2.imshow("Charuco Calibration", frame)
    if cv2.waitKey(1) & 0xFF == 27:  # ESCキーで途中終了
        break

cap.release()
cv2.destroyAllWindows()

# --- キャリブレーション ---
if len(all_corners) > 0:
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = aruco.calibrateCameraCharuco(
        all_corners,
        all_ids,
        board,
        img_size,
        None,
        None
    )

    print("Camera matrix:\n", camera_matrix)
    print("Distortion coefficients:\n", dist_coeffs)

    # --- 保存 ---
    np.savez("camera_parameters.npz", camera_matrix=camera_matrix, dist_coeffs=dist_coeffs)
    print("カメラパラメータを 'camera_parameters.npz' に保存しました。")
else:
    print("Charuco コーナーが検出されませんでした。")
