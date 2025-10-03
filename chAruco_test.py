import cv2
import numpy as np

# --- chArUco_board.py から流用した設定 ---
squares_x = 42 // 8+1
squares_y = 30 // 8 +1
square_length_mm = 30.0
marker_length_mm = 20.0
aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
detector_params = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(aruco_dict, detector_params)

# ChArUcoBoardオブジェクトの作成
board = cv2.aruco.CharucoBoard(
    size=(squares_x, squares_y),
    squareLength=square_length_mm,
    markerLength=marker_length_mm,
    dictionary=aruco_dict
)

# --- カメラの準備 ---
cap = cv2.VideoCapture(0) # 0はデフォルトのカメラ
cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1) # 自動露出を有効にする


if not cap.isOpened():
    print("エラー: カメラを開けません。")
    exit()

# --- 検出と表示のループ ---
while True:

    ret, frame = cap.read()
    if not ret:
        print("エラー: フレームを読み取れません。")
        break

    # グレースケールに変換
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # ArUcoマーカーの検出
    corners, ids, rejectedImgPoints = detector.detectMarkers(gray)

    # マーカーが検出された場合
    if ids is not None:
        # ChArUcoボードのコーナーを補間
        ret, charuco_corners, charuco_ids = cv2.aruco.interpolateCornersCharuco(
            markerCorners=corners,
            markerIds=ids,
            image=gray,
            board=board
        )

        # 検出されたマーカーを描画
        frame = cv2.aruco.drawDetectedMarkers(frame, corners, ids)

        # ChArUcoコーナーが十分に検出された場合
        if ret > 0:
            # 検出されたChArUcoコーナーを描画
            frame = cv2.aruco.drawDetectedCornersCharuco(frame, charuco_corners, charuco_ids, (0, 255, 0))

    # 結果を表示
    cv2.imshow('ChArUco Board Detection', frame)

    # 'q'キーが押されたらループを抜ける
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- 後処理 ---
cap.release()
cv2.destroyAllWindows()
