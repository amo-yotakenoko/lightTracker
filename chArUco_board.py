import cv2
import numpy as np
import sys
from PIL import Image

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

# 5. 出力ファイル名を定義（PDF分割保存用）
output_basename = "A2_ChArUco_Board"

# --- ChArUcoボードの生成 ---

# 1. ChArUcoBoardオブジェクトの作成
board = cv2.aruco.CharucoBoard(
    size=(squares_x, squares_y),
    squareLength=square_length_mm,
    markerLength=marker_length_mm,
    dictionary=aruco_dict
)

# 2. ボードを描画
# marginSize: ボードの外周の白い余白の幅 (ピクセル)
# borderBits: マーカー自体の黒い枠線の幅 (通常 1 か 2)
board_image = board.generateImage(
    outSize=(output_width_px, output_height_px),
    marginSize=0, # 外側の白い余白を広く取る (A2に収めやすくするため)
    borderBits=1
)

# 4. 画像をA3サイズ2枚に分割してPDFとして保存
try:
    print("A2ボード画像を生成しました。A3サイズのPDF2枚に分割して保存します...")

    # 画像の幅を取得し、分割点を計算
    # CharucoBoard.generateImageはグレースケール画像を返すため、チャンネル数はない
    height, width = board_image.shape
    split_point = width // 2

    # 画像を左右に分割
    left_image_gray = board_image[:, :split_point]
    right_image_gray = board_image[:, split_point:]

    # グレースケール画像をPillowで扱えるRGB形式に変換
    left_image_rgb = cv2.cvtColor(left_image_gray, cv2.COLOR_GRAY2RGB)
    right_image_rgb = cv2.cvtColor(right_image_gray, cv2.COLOR_GRAY2RGB)

    # PillowのImageオブジェクトに変換
    pil_left = Image.fromarray(left_image_rgb)
    pil_right = Image.fromarray(right_image_rgb)

    # PDFとして保存
    left_pdf_path = f"{output_basename}_Left.pdf"
    right_pdf_path = f"{output_basename}_Right.pdf"

    # A3用紙のDPIを考慮して保存（約3508x2480ピクセル @ 300DPI）
    # PillowはDPIを直接PDFに設定するのが複雑なため、解像度を指定して保存
    pil_left.save(left_pdf_path, "PDF", resolution=300.0, save_all=True)
    pil_right.save(right_pdf_path, "PDF", resolution=300.0, save_all=True)

    print(f"ボードを2つのPDFファイルに保存しました:")
    print(f"- {left_pdf_path}")
    print(f"- {right_pdf_path}")

except Exception as e:
    print(f"Error: 画像の処理またはPDFの保存中にエラーが発生しました: {e}")
    sys.exit(1)