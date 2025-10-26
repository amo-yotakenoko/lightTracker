import cv2

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
square_length_mm = 83.0
# ArUcoマーカー自体の一辺の長さ (mm)
# square_length_mm より小さくする必要があります
marker_length_mm = square_length_mm*(2.0/3.0) 

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
