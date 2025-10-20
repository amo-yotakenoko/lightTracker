import numpy as np
import math
import estimation
class TrackerObject:
    def __init__(self):
        self.markers={}
        self.position=np.array([0,0,0],dtype=np.float32).T
        self.rotation=np.eye(3)
        r=40/2
        h=50/2

        for i in range(6):
            x=math.cos(math.radians(60*i))*r
            y=math.sin(math.radians(60*i))*r
            z=(0 if i%2==0 else h)
            self.markers[i]=np.array([x,y,z]).T


    def transformed_markers(self,add_rotation=None,add_position=None):
        rotation=self.rotation
        position=self.position
        if add_rotation is not None:
            rotation=self.rotation @add_rotation
        if add_position is not None:
            position=self.position+add_position
        for i,pos in self.markers.items():

            transformed_pos = rotation @ pos + position
            yield i, transformed_pos



    def plot(self,ax):
        xs=[]
        ys=[]
        zs=[]
        for i,pos in self.transformed_markers():
            xs.append(pos[0])
            ys.append(pos[1])
            zs.append(pos[2])
        ax.plot(xs,ys,zs,color='red' ,   marker='*',    markersize=10, )
            



objects=[TrackerObject()]



def error_distance(transformed_markers,cameras,ax=None):
    transformed_markers=list(transformed_markers)

    total_error=0
    for cam in cameras:
        if cam.camera_position is None or cam.camera_rotation is None:
            continue
        for marker in cam.markers:
            print(f"{marker.estimate_id()=}{len(marker.estimate_id())=}{len(marker.estimate_id())!=1=}")
            if(len(marker.estimate_id())!=1):
                continue
            marker_id=marker.estimate_id()[0]
            ray_origin=cam.camera_position
            print(f"{marker.position=}")
            ray_emit=  estimation.uv_to_ray(cam, marker.position, scale=1000.0)
            # estimation.draw_uv_line(cam,marker.position,ax)
            # ax.plot([cam.camera_position[0, 0], ray_emit[0, 0]],
            #                 [cam.camera_position[1, 0],ray_emit[1, 0]],
            #                 [cam.camera_position[2, 0], ray_emit[2, 0]],color='blue',
            #             linestyle='--')
            

            for obj_id, obj_pos in transformed_markers:
                print(f"Marker ID: {marker_id}, Object ID: {obj_id}")

                if obj_id != marker_id:
                    continue
                # 点と直線の距離計算
                p0 = ray_origin.ravel() 
                p1 =  ray_emit.ravel() 
                p2 = obj_pos.ravel() 

                

                line_vec = p1 - p0
                point_vec = p2 - p0
                line_len = np.dot(line_vec, line_vec)
                t = np.dot(point_vec, line_vec) / line_len
                # t = max(0, min(1, t))  # tを0から1の範囲に制限
                projection = p0 + t * line_vec
                distance = np.linalg.norm(p2 - projection)
                total_error += distance
                print(f"Marker ID: {marker_id}, Object ID: {obj_id}, Distance: {distance}")

                # if ax is not None:
                #     # 元の直線を描画（任意の長さ）
                #     ax.plot(
                #         [p0[0], p1[0]],
                #         [p0[1], p1[1]],
                #         [p0[2], p1[2]],
                #         color='blue',
                #         linestyle='--',
                #         label='Ray'
                    # )

                #     # 点を描画
                #     ax.scatter(
                #         p2[0], p2[1], p2[2],
                #         color='green',
                #         marker='o',
                #         s=50,
                #         label=f'Object Marker {marker_id}'
                #     )

                    # 点と線の最短線（垂線）を描画
                if ax is not None:
                    ax.plot(
                        [p2[0], projection[0]],
                        [p2[1], projection[1]],
                        [p2[2], projection[2]],
                        color='red',
                        linestyle='-',
                        linewidth=0.5,
                    )

    return total_error 