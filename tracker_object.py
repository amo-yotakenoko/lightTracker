import numpy as np
import math
import estimation
import define_sign
class TrackerObject:
    def __init__(self):
        self.markers={}
        self.position=np.array([0,0,0],dtype=np.float32).T
        self.rotation=np.eye(3)
        self.r=40
        self.h=50

        for i in range(6):
            x=math.cos(math.radians(60*i))*self.r
            y=math.sin(math.radians(60*i))*self.r
            z=(0 if i%2==0 else self.h)
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
        colors=[]
        for i,pos in self.transformed_markers():
            xs.append(pos[0])
            ys.append(pos[1])
            zs.append(pos[2])
            colors.append(define_sign.marker_display_colors[i])
        ax.scatter(xs, ys, zs, color=colors, marker='*', s=100)
        ax.plot(xs,ys,zs,color='k' ,linewidth=0.5, )
        

        # ax.scatter(xs, ys, zs, color=colors, marker='*', s=100) 



        for h in [0,self.h]:
            # x, y 座標を計算
            theta = np.linspace(0, 2*np.pi, 200)
            x = self.r * np.cos(theta)
            y = self.r * np.sin(theta)
            z = np.zeros_like(theta) +h
            pos = np.vstack((x, y, z))  # shape (3, 200)

            # 3. 回転と平行移動
            transformed_pos = self.rotation @ pos + self.position.reshape(3,1)

            ax.plot(
                transformed_pos[0, :], 
                transformed_pos[1, :], 
                transformed_pos[2, :], 
                color='k',linewidth=0.5,
                )


        # # X軸 (赤)
        # x_axis_world = self.rotation @ np.array([[50, 0, 0]]).T + self.position
        # ax.plot([self.position[0], x_axis_world[0, 0]],
        #         [self.position[1], x_axis_world[1, 0]],
        #         [self.position[2], x_axis_world[2, 0]], color='red', label='Cam X')
        # # Y軸 (緑)
        # y_axis_world = self.rotation @ np.array([[0, 50, 0]]).T + self.position
        # ax.plot([self.position[0], y_axis_world[0, 0]],
        #         [self.position[1], y_axis_world[1, 0]],
        #         [self.position[2], y_axis_world[2, 0]], color='green', label='Cam Y')
        # # Z軸 (青)
        # z_axis_world = self.rotation @ np.array([[0, 0, 10]]).T + self.position
        # ax.plot([self.position[0], z_axis_world[0, 0]],
        #         [self.position[1], z_axis_world[1, 0]],
        #         [self.position[2], z_axis_world[2, 0]], color='blue', label='Cam Z')
        
                # X軸 (赤)
        x_axis_world = self.rotation @ np.array([50, 0, 0]).T+self.position
        # print(f"{self.position=},{x_axis_world=}")
        ax.plot([self.position[0], x_axis_world[0]],
                [self.position[1], x_axis_world[1]],
                [self.position[2], x_axis_world[2]], color='red')
        # Y軸 (緑)
        y_axis_world = self.rotation @ np.array([0, 50, 0]).T +self.position
        ax.plot([self.position[0], y_axis_world[0]],
                [self.position[1], y_axis_world[1]],
                [self.position[2], y_axis_world[2]], color='green')
        # Z軸 (青)
        z_axis_world = self.rotation @ np.array([0, 0, 50]).T +self.position
        ax.plot([self.position[0], z_axis_world[0]],
                [self.position[1], z_axis_world[1]],
                [self.position[2], z_axis_world[2]], color='blue')
            

            



objects=[TrackerObject()]



def error_distance(transformed_markers,cameras,ax=None):
    transformed_markers=list(transformed_markers)

    total_error=0
    for cam in cameras:
        if cam.camera_position is None or cam.camera_rotation is None:
            continue
        for marker in cam.markers:
            # print(f"{marker.estimate_id()=}{len(marker.estimate_id())=}{len(marker.estimate_id())!=1=}")
            if(len(marker.estimate_id())!=1):
                continue
            marker_id=marker.estimate_id()[0]
            ray_origin=cam.camera_position
            # print(f"{marker.position=}")
            ray_emit=  estimation.uv_to_ray(cam, marker.position)
            # estimation.draw_uv_line(cam,marker.position,ax)
            # ax.plot([cam.camera_position[0, 0], ray_emit[0, 0]],
            #                 [cam.camera_position[1, 0],ray_emit[1, 0]],
            #                 [cam.camera_position[2, 0], ray_emit[2, 0]],color='blue',
            #             linestyle='--')
            

            for obj_id, obj_pos in transformed_markers:
                # print(f"Marker ID: {marker_id}, Object ID: {obj_id}")

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
                total_error += distance**2
                               
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