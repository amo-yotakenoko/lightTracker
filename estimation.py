import time
import chArUco_detect
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import chArUco_board
import tracker_object
from scipy.spatial.transform import Rotation as R
import define_sign
import cv2

import settings 

marker_3d_points=[None]*30

def uv_to_ray(cam, uv, scale=10000.0):
    """
    画像上のピクセル uv からワールド座標系でのレイ終端点を計算して返す。
    cam.dist_coeffs を使ってレンズ歪みを補正する。
    """
    u, v = uv
    # 歪み補正
    uv_undistorted = cv2.undistortPoints(
        np.array([[u, v]], dtype=np.float32).reshape(1,1,2),  # 1x1x2 に変形
        cam.camera_matrix,
        cam.dist_coeffs
    )

    # 正規化カメラ座標系
    x_n = uv_undistorted[0,0,0]
    y_n = uv_undistorted[0,0,1]
    z_n = 1.0

    ray_cam = np.array([[x_n * scale, y_n * scale, z_n * scale]]).T
    # カメラ座標 → ワールド座標
    ray_world = cam.camera_rotation @ ray_cam + cam.camera_position
    return ray_world


def draw_uv_line(cam,uv,ax,color=None,text=None):
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

    ray_end = uv_to_ray(cam, uv)

    ax.plot([cam.camera_position[0, 0], ray_end[0, 0]],
                            [cam.camera_position[1, 0], ray_end[1, 0]],
                            [cam.camera_position[2, 0], ray_end[2, 0]],color=color,lw=0.5)
    
    # if text is not None:
    #     color = color if color is not None else 'black'
    #     ax.text(ray_end[0, 0], ray_end[1, 0], ray_end[2, 0], text, color=color )




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
            draw_uv_line( cam, uv,ax,color='gray')





def plot_board(ax):
    x1 = chArUco_board.squares_y * chArUco_board.square_length_mm
    y1 = chArUco_board.squares_x * chArUco_board.square_length_mm

    # 頂点を順に並べる（時計回り）
    rect_path = np.array([
        [0, 0, 0],       # 左下
        [y1, 0, 0],     # 右下
        [y1, x1, 0],    # 右上
        [0, x1, 0],      # 左上
        [0, 0, 0],       # 左下に戻る
    ]).T  # 3xN に転置して掛け算しやすくする

    # # rotation 行列を作る（X,Y,Z軸での回転）
    # R_total = R.from_euler('XYZ', settings.board_rotation, degrees=True).as_matrix()

    # # 全座標に適用
    # rotated_path = R_total @ rect_path

    # 3xN → Nx3 に戻す
    rotated_path = rect_path.T

    # 描画
    ax.plot(rotated_path[:, 0], rotated_path[:, 1], rotated_path[:, 2], color='r', linewidth=2)


def estimate_marker_position(ray_list):
    """複数の (origin, direction) から最小二乗交点を求める"""
    if len(ray_list) < 2:
        return None  # データ不足

    A = np.zeros((3, 3))
    b = np.zeros(3)

    for origin, direction in ray_list:
        p = origin.flatten()
        d = direction.flatten()
        I = np.eye(3)
        A_i = I - np.outer(d, d)
        A += A_i
        b += A_i @ p

    # 最小二乗解
    x, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    return x




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
    

    # grad = np.clip(grad, -100z, 100)
    return grad


def compute_rotation_gradient( object, cameras, eps=1e-3):
    # 現在の回転
    rot = R.identity()

    grad_rotvec = np.zeros(3)  # X, Y, Z軸の回転ベクトル勾配

    for i in [0,1,2]:
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
  
    if np.linalg.norm(grad_rotvec) > 0:
        max_grad = 1e3  # 適当な上限
        grad_rotvec = np.clip(grad_rotvec, -max_grad, max_grad)

        # 回転更新
        delta_rot = R.from_rotvec(-grad_rotvec * 0.01)  # 学習率的に調整

        rot = delta_rot * rot
    return rot

def estimate_pose_from_markers(origin_points, target_points):
    """
    origin_points : list or ndarray (N,3)  # モデル上のマーカー座標（物体座標系）
    target_points : list or ndarray (N,3)  # 観測されたマーカーの3D位置（ワールド座標系）
    
    return:
        R_opt (3x3) 回転行列
        t_opt (3,)   並進ベクトル
    """
    origin_points = np.array(origin_points)
    target_points = np.array(target_points)

    if len(origin_points) < 3:
        raise ValueError("At least 3 points are required for pose estimation")

    # 1. 重心を求めて中心化
    centroid_origin = np.mean(origin_points, axis=0)
    centroid_target = np.mean(target_points, axis=0)
    origin_centered = origin_points - centroid_origin
    target_centered = target_points - centroid_target

    # 2. Kabsch法で回転行列を求める
    H = origin_centered.T @ target_centered
    U, S, Vt = np.linalg.svd(H)
    R_opt = Vt.T @ U.T

    # 右手系を維持（det(R) < 0 の場合は反転補正）
    if np.linalg.det(R_opt) < 0:
        Vt[2, :] *= -1
        R_opt = Vt.T @ U.T

    # 3. 平行移動ベクトルを計算
    t_opt = centroid_target - R_opt @ centroid_origin

    return t_opt,R_opt


def estimation(cameras):
    fig = plt.figure()
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)
    ax = fig.add_subplot(121, projection='3d')
    ax_zoom = fig.add_subplot(122, projection='3d')
    plt.ion() # インタラクティブモードをオン
    while True:
        ax.cla()
        ax_zoom.cla()
        plot_board(ax)
        plot_board(ax_zoom)

        rays = {i: [] for i in range(30)}

        for cam in cameras:
            for marker in cam.markers:
                marker_ids = marker.estimate_id()
                # IDが有効か確認
                if marker_ids is None or len(marker_ids) != 1:
                    continue

                marker_id = marker_ids[0]

                # カメラ位置とレイ方向の算出
                ray_end = uv_to_ray(cam, marker.position)
                origin = np.array(cam.camera_position, dtype=float).reshape(3, 1)
                direction = np.array(ray_end, dtype=float).reshape(3, 1) - origin

                # 正規化（ゼロ除算防止）
                norm = np.linalg.norm(direction)
                if norm < 1e-6:
                    continue
                direction /= norm

                # 形式統一：3x1 numpy配列ペア
                rays[marker_id].append((origin, direction))


                for marker_id, ray_list in rays.items():            
                    if len(ray_list)<2:
                        continue
                    # print(f"marker_id={marker_id} ray_count={len(ray_list)}")
                    # print(f"{ray_list=}")


        
        for marker_id, ray_list in rays.items():
            if len(ray_list) < 2:
                continue
            pos = estimate_marker_position(ray_list)
            marker_3d_points[marker_id]=pos
            ax_zoom.scatter(*pos, s=60, color=define_sign.marker_display_colors[marker_id])
            ax_zoom.text(pos[0], pos[1], pos[2], f"{marker_id}")


        for object in tracker_object.objects:
            # print("----")
            # print(f"{marker_3d_points=}")
            # print(f"{list(object.transformed_markers())=}")
            # print(f"{object.position=}")
            # print(f"{object.rotation=}")
            target_points=[]
            origin_points=[]

            for marker_id, object_marker_3d_point in object.markers.items():
                if marker_3d_points[marker_id] is None:
                    continue
                detect_marker_3d_point = marker_3d_points[marker_id]
                target_points.append(detect_marker_3d_point)
                origin_points.append(object_marker_3d_point)
                

            # print(f"{(origin_points)=}\n{(target_points)=}")
            if(len(origin_points)>=3):
                object.position,object.rotation=  estimate_pose_from_markers(origin_points, target_points)
                # estimate_pose_from_markers(origin_points, target_points)
                # print(f"object position updated:{object.position=}")
                # print(f"object rotation updated:\n{object.rotation=}")

            

        for cam in cameras:
            if cam.camera_position is None or cam.camera_rotation is None:
                continue
            plot_camera_pose(cam,ax)


            for marker in cam.markers:
                if(len(marker.estimate_id())!=1):
                    continue

                # print(f"{marker.position=},{marker.estimate_id()=}" )
                # print(f"{define_sign.marker_display_colors[marker.estimate_id()[0]]=}")


                draw_uv_line( cam, marker.position,ax,text=f"{marker.estimate_id()}",color=define_sign.marker_display_colors[marker.estimate_id()[0]])
                draw_uv_line( cam, marker.position,ax_zoom,color=define_sign.marker_display_colors[marker.estimate_id()[0]])

            


            # tracker_object.error_distance(object.transformed_markers(), cameras,ax=ax)
            # tracker_object.error_distance(object.transformed_markers(), cameras,ax=ax_zoom)



            # for i in range(1):
            #     grad_pos = compute_position_gradient( object, cameras)
            #     object.position += grad_pos*10


            #     grad_rot = compute_rotation_gradient( object, cameras)
            #     object.rotation = object.rotation @  grad_rot.as_matrix()


            # u, _, v = np.linalg.svd(object.rotation)
            # object.rotation = u @ v

        for object in tracker_object.objects:
            # print("----")
            
            object.plot(ax)
            object.plot(ax_zoom)
       
        size=chArUco_board.squares_y * chArUco_board.square_length_mm*3
        offset = np.array([
            size/2*0.5,size/2,-size/2
        ], dtype=np.float32)


        ax.set_xlim([offset[0]-size/2, offset[0]+size/2])
        ax.set_ylim([offset[1]+size/2, offset[1]-size/2])
        ax.set_zlim([ offset[2]+size/2, offset[2]-size/2])
        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')


        size=200
        offset=object.position
        ax_zoom.set_xlim([offset[0]-size/2, offset[0]+size/2])
        ax_zoom.set_ylim([offset[1]+size/2, offset[1]-size/2])
        ax_zoom.set_zlim([ offset[2]+size/2, offset[2]-size/2])
  
        ax.view_init(elev=30, azim=time.time()*10) 
        ax_zoom.view_init(elev=30, azim=time.time()*10) 

        # print(f"{object.position=}")


        # ax.set_box_aspect([1,1,1]) 

        plt.draw()
        plt.pause(0.01)



#         marker.position=array([356., 238.], dtype=float32),marker.estimate_id()=[0]
# marker.position=array([371., 260.], dtype=float32),marker.estimate_id()=[1]
# marker.position=array([391., 243.], dtype=float32),marker.estimate_id()=[2]