from  chArUco_detect import *

import chArUco_board

# 5. 出力ファイル名を定義（PDF分割保存用）
output_basename = "A2_ChArUco_Board"

# 4. 画像をA3サイズ2枚に分割してPDFとして保存
try:

        # 2. ボードを描画
    # marginSize: ボードの外周の白い余白の幅 (ピクセル)
    # borderBits: マーカー自体の黒い枠線の幅 (通常 1 か 2)
    board_image = chArUco_board.board.generateImage(
        outSize=(chArUco_board.output_width_px, chArUco_board.output_height_px),
        marginSize=0, # 外側の白い余白を広く取る (A2に収めやすくするため)
        borderBits=1
    )

 
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