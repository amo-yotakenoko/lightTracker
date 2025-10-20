"""
hex_and_concentric_circles.py

正方形の画像に正六角形を描き、中心から各頂点方向へ画像外まで伸びる直線（無限に伸びる代わりに画像外まで延長）と
中心を共有する同心円を30個描画するサンプルスクリプト。
Pillow（PIL）とnumpyを使います。

使い方:
    pip install pillow numpy
    python hex_and_concentric_circles.py

生成されるファイル: hex_circles.png
"""

from PIL import Image, ImageDraw
import numpy as np
import math

# ====== 設定 ======
IMAGE_SIZE = 800           # 正方形の1辺ピクセル数
BG_COLOR = (255, 255, 255) # 背景色（白）
HEX_FILL = (230, 240, 255) # 六角形内部の塗り色
HEX_OUTLINE = (20, 60, 160) # 六角形の輪郭色
HEX_OUTLINE_WIDTH = 6

CIRCLE_COUNT = 30          # 同心円の数（要求: 30）
CIRCLE_MAX_RATIO = 0.48    # 画像サイズに対する最大半径（比率）
CIRCLE_WIDTH = 2           # 同心円の線の太さ
CIRCLE_COLOR = (200, 40, 40) # 同心円の色

RAY_COLOR = (30, 30, 30)   # 中心から頂点方向へ伸ばす直線の色
RAY_WIDTH = 2              # 直線の太さ

SAVE_PATH = 'hex_circles.png'

# ====== ヘルパー ======

def regular_polygon_vertices(center, radius, sides, rotation_deg=0):
    """中心 center=(x,y)、半径 radius、辺の数 sides の正多角形頂点リストを返す。
    rotation_deg は度単位で回転量（0で右方向に最初の頂点）。
    """
    cx, cy = center
    verts = []
    for i in range(sides):
        angle_deg = rotation_deg + 360.0 * i / sides
        angle = math.radians(angle_deg)
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        verts.append((x, y))
    return verts

# ====== 画像作成 ======

img = Image.new('RGB', (IMAGE_SIZE, IMAGE_SIZE), BG_COLOR)
draw = ImageDraw.Draw(img)

center = (IMAGE_SIZE / 2.0, IMAGE_SIZE / 2.0)

# 六角形の半径（頂点までの距離）を画像サイズの比で決める
hex_radius = IMAGE_SIZE * 0.35
# 上が尖る六角形にするために回転を-90度に設定
hex_vertices = regular_polygon_vertices(center, hex_radius, sides=6, rotation_deg=-90)

# 六角形を塗りつぶす
draw.polygon(hex_vertices, fill=HEX_FILL)
# 太い輪郭を描く
for i in range(len(hex_vertices)):
    a = hex_vertices[i]
    b = hex_vertices[(i + 1) % len(hex_vertices)]
    draw.line([a, b], fill=HEX_OUTLINE, width=HEX_OUTLINE_WIDTH)

# ====== 中心から頂点方向に無限に伸びる（画像外まで延長する）直線を描く ======
# 中心から各頂点に向かうベクトルを正規化して、画像の外まで伸ばす長さを計算する
# 画像の角（コーナー）までの最大距離を取り、それより少し大きめに伸ばす
corners = [(0,0), (0, IMAGE_SIZE), (IMAGE_SIZE, 0), (IMAGE_SIZE, IMAGE_SIZE)]
max_corner_dist = max(math.hypot(cx - x, cy - y) for (x, y) in corners for cx, cy in [center])
extend_length = max_corner_dist * 1.1  # 余裕をもって画像外まで伸ばす

for vx, vy in hex_vertices:
    dx = vx - center[0]
    dy = vy - center[1]
    norm = math.hypot(dx, dy)
    if norm == 0:
        continue
    ux = dx / norm
    uy = dy / norm
    end_x = center[0] + ux * extend_length
    end_y = center[1] + uy * extend_length
    # 中心 -> end を描く
    draw.line([center, (end_x, end_y)], fill=RAY_COLOR, width=RAY_WIDTH)

# ====== 同心円を描く（30個） ======
max_circle_radius = IMAGE_SIZE * CIRCLE_MAX_RATIO
# 小さい方の最小半径は max の 1/30 程度にする（丸が全部見えるように）
min_circle_radius = max_circle_radius * 0.02
radii = np.linspace(min_circle_radius, max_circle_radius, CIRCLE_COUNT)

for r in radii:
    left_up = (center[0] - r, center[1] - r)
    right_down = (center[0] + r, center[1] + r)
    draw.ellipse([left_up, right_down], outline=CIRCLE_COLOR, width=CIRCLE_WIDTH)

# ====== 保存＆表示 ======
img.save(SAVE_PATH)
print(f"Saved: {SAVE_PATH}")
try:
    img.show()
except Exception:
    pass

# ====== カスタマイズのヒント ======
# - 直線の色/太さは RAY_COLOR / RAY_WIDTH を変更してください。
# - 同心円の数を変えるには CIRCLE_COUNT を変更してください。
# - 六角形の向きや大きさは hex_radius と rotation_deg を調整してください。
