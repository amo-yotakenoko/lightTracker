import time
import chArUco_detect
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import chArUco_board
import tracker_object
from scipy.spatial.transform import Rotation as R

def uv_to_ray(cam, uv, scale=1000.0):
    """
    画像上のピクセル uv からワールド座標系でのレイ終端点を計算して返す。
    """
    u, v = uv
    fx = cam.camera_matrix[0, 0]
    fy = cam.camera_matrix[1, 1]
    cx = cam.camera_matrix[0, 2]
    cy = cam.camera_matrix[1, 2]

    # 正規化カメラ座標系
    x_n = (u - cx) / fx
    y_n = (v - cy) / fy
    z_n = 1.0

    ray_cam = np.array([[x_n * scale, y_n * scale, z_n * scale]]).T
    return cam.camera_rotation @ ray_cam + cam.camera_position


def draw_uv_line(cam,uv,ax,text=None):
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

    ray_end = uv_to_ray(cam, uv, scale=1000.0)

    ax.plot([cam.camera_position[0, 0], ray_end[0, 0]],
                            [cam.camera_position[1, 0], ray_end[1, 0]],
                            [cam.camera_position[2, 0], ray_end[2, 0]])
    if text is not None:
        ax.text(ray_end[0, 0], ray_end[1, 0], ray_end[2, 0], text, color='black')




def plot_camera_pose(cam,ax):
        
        if(cam.camera_rotation is None or cam.camera_position is None):
            return 
        # カメラ位置をプロット
        ax.scatter(cam.camera_position[0], cam.camera_position[1], cam.camera_position[2],
                color='blue', label='Camera position')

        # カメラの向きベクトル（3軸）を描画 (World座標系基準)
        axis_length = 50
        # R は R_W_C (Camera -> World の回転)
        # X軸 (赤)
        x_axis_world = cam.camera_rotation @ np.array([[axis_length, 0, 0]]).T + cam.camera_position
        ax.plot([cam.camera_position[0, 0], x_axis_world[0, 0]],
                [cam.camera_position[1, 0], x_axis_world[1, 0]],
                [cam.camera_position[2, 0], x_axis_world[2, 0]], color='red', label='Cam X')
        # Y軸 (緑)
        y_axis_world = cam.camera_rotation @ np.array([[0, axis_length, 0]]).T + cam.camera_position
        ax.plot([cam.camera_position[0, 0], y_axis_world[0, 0]],
                [cam.camera_position[1, 0], y_axis_world[1, 0]],
                [cam.camera_position[2, 0], y_axis_world[2, 0]], color='green', label='Cam Y')
        # Z軸 (青)
        z_axis_world = cam.camera_rotation @ np.array([[0, 0, axis_length]]).T + cam.camera_position
        ax.plot([cam.camera_position[0, 0], z_axis_world[0, 0]],
                [cam.camera_position[1, 0], z_axis_world[1, 0]],
                [cam.camera_position[2, 0], z_axis_world[2, 0]], color='blue', label='Cam Z')
        

        # 各角を中心からの座標に変更
        uv_points = [
           np.array([0, 0]),   # 左上
           np.array([0, cam.cy*2]),    # 左下
           np.array([cam.cx*2, 0]),    # 右上
           np.array([cam.cx*2, cam.cy*2])      # 右下
        ]
        for uv in uv_points:
            draw_uv_line( cam, uv,ax)





def plot_board(ax):
        x1, y1 = chArUco_board.squares_y * chArUco_board.square_length_mm, -chArUco_board.squares_x * chArUco_board.square_length_mm
        print(f"board:{x1=},{y1=}")
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



def compute_position_gradient( object, cameras, eps=0.1):
    """
    object.position に対する勾配を有限差分で計算
    """
    grad = np.zeros(3, dtype=np.float32)
    shifts = [np.array([-eps,0,0],dtype=np.float32),
              np.array([ eps,0,0],dtype=np.float32),
              np.array([0,-eps,0],dtype=np.float32),
              np.array([0, eps,0],dtype=np.float32),
              np.array([0,0,-eps],dtype=np.float32),
              np.array([0,0, eps],dtype=np.float32)]
    
    # x
    grad[0] = tracker_object.error_distance(object.transformed_markers(add_position=shifts[0]), cameras) - \
              tracker_object.error_distance(object.transformed_markers(add_position=shifts[1]), cameras)
    # y
    grad[1] = tracker_object.error_distance(object.transformed_markers(add_position=shifts[2]), cameras) - \
              tracker_object.error_distance(object.transformed_markers(add_position=shifts[3]), cameras)
    # z
    grad[2] = tracker_object.error_distance(object.transformed_markers(add_position=shifts[4]), cameras) - \
              tracker_object.error_distance(object.transformed_markers(add_position=shifts[5]), cameras)
    
    grad *= 0.1  # 元のコードに合わせる
    return grad


def compute_rotation_gradient( object, cameras, eps=0.1):
    # 現在の回転
    rot = R.identity()

    grad_rotvec = np.zeros(3)  # X, Y, Z軸の回転ベクトル勾配

    for i, axis in enumerate(['x', 'y', 'z']):
        # 微小回転
        delta = np.zeros(3)
        delta[i] = eps  # 軸方向だけ回転
        rot_plus = R.from_rotvec(delta) * rot
        rot_minus = R.from_rotvec(-delta) * rot

        # 誤差計算
        err_plus = tracker_object.error_distance(object.transformed_markers(add_rotation=rot_plus.as_matrix()), cameras)
        err_minus = tracker_object.error_distance(object.transformed_markers(add_rotation=rot_minus.as_matrix()), cameras)

        # 中心差分
        grad_rotvec[i] = (err_plus - err_minus) / (2*eps)

        # 回転更新
        delta_rot = R.from_rotvec(-grad_rotvec * 0.0001)  # 学習率的に調整
        rot = delta_rot * rot
    return rot




def estimation(cameras):
    fig = plt.figure()
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax = fig.add_subplot(111, projection='3d')
    plt.ion() # インタラクティブモードをオン
    while True:
        ax.cla()
        plot_board(ax)
        for cam in cameras:
            if cam.camera_position is None or cam.camera_rotation is None:
                continue
            plot_camera_pose(cam,ax)


            for marker in cam.markers:
                if(len(marker.estimate_id())!=1):
                    continue

                # print(f"{marker.position=},{marker.estimate_id()=}" )
                draw_uv_line( cam, marker.position,ax,text=f"{marker.estimate_id()}")



        for object in tracker_object.objects:
            print("----")
            object.plot(ax)
            tracker_object.error_distance(object.transformed_markers(), cameras,ax=ax)
            grad_pos = compute_position_gradient( object, cameras)
            object.position += grad_pos


            grad_rot = compute_rotation_gradient( object, cameras)
            object.rotation = object.rotation @  grad_rot.as_matrix()


            # u, _, v = np.linalg.svd(object.rotation)
            # object.rotation = u @ v






        ax.set_xlim([200, -200])
        ax.set_ylim([000, 400])
        ax.set_zlim([0, -400])
        # ax.set_box_aspect([1,1,1]) 

        plt.draw()
        plt.pause(0.01)



#         marker.position=array([356., 238.], dtype=float32),marker.estimate_id()=[0]
# marker.position=array([371., 260.], dtype=float32),marker.estimate_id()=[1]
# marker.position=array([391., 243.], dtype=float32),marker.estimate_id()=[2]