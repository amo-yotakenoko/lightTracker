import numpy as np
import math

class TrackerObject:
    def __init__(self):
        self.markers={}
        self.position=np.array([0,0,0],dtype=np.float32).T
        self.rotation=np.eye(3)
        r=40
        h=50

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