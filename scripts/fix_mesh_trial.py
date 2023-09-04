"""Provides a scripting component.
    Inputs:
        x: The x script variable
        y: The y script variable
    Output:
        a: The a output variable"""

__author__ = "duch"

from compas_view2.app import App
from compas.datastructures import Mesh
import os 
from scipy.spatial import distance

folder = "/Users/duch/Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat/2.0b4.0.9/c32ba60b0e0c097af1f49a1fd3ffcc42/Message/MessageTemp/0a4dca4fe97d182b230a6dfbca2d3f7c/File"

filename_in = "mesh1_fix.json"
file_in = os.path.join(folder, filename_in)
mesh = Mesh.from_json(file_in)

new_mesh = Mesh()
new_mesh.update_default_vertex_attributes({"row": None, "column": None, "tri": None})

def closest(new_point, points):
    closest_index = None
    closest_dis = None
    for i, point in enumerate(points):
        # distance = ((point[0] - new_point[0])**2 + (point[1] - new_point[1])**2 + (point[2] - new_point[2])**2)**0.5
        dis = distance.euclidean(point, new_point)
        if closest_dis is None or dis < closest_dis:
            closest_index = i
            closest_dis = dis
    return closest_index


row = -1
while True and row <= 100:
    col = 1
    vkeys = []
    pts = []
    
    
    while True and col <= 100:
        vertices = list(mesh.vertices_where({"row":row, "column": col}))
        if vertices == []:
            break
        if len(vertices) != 1:
            raise ValueError("wrong")
        
        vertex = vertices[0]
        xyz = mesh.vertex_coordinates(vertex)
        vkey = new_mesh.add_vertex(x=xyz[0], y=xyz[1], z=xyz[2])
        new_mesh.vertex_attributes(vkey, ["row", "column"], [row, col])
        
        vkeys.append(vkey)
        pts.append(xyz)
        
        col += 1
        
        
    seg_count = len(vkeys)
    
    if row > 0 :
        
        ancestor_indices = []
        current_indices = []
        # for pt in the current row, find the closest point in the ancestor row 
        # CAN BE OPTIMISED, QUADTREE
        for j, pt in enumerate(pts):
            ancestor_index = closest(pt, ancestor_pts)
            ancestor_indices.append(ancestor_index)
        
        # for pt in the ancestor row, find the closest point in the current row
        # CAN BE OPTIMISED
        for j, pt in enumerate(ancestor_pts):
            current_index = closest(pt, ancestor_pts)
            current_indices.append(current_index)
        
        
        print(ancestor_indices, current_indices)
        
        k = 0
        h = 0
        
        # create faces
        count = 0
        
        while k < ancestor_seg_count and h < seg_count and count < 50:
            count += 1
            anc_ind = ancestor_indices[h]
            cur_ind = current_indices[k]
            anc_ind_next = ancestor_indices[h+1]
            cur_ind_next = current_indices[k+1]

            if anc_ind <= cur_ind and anc_ind_next <= cur_ind_next and anc_ind_next > anc_ind:
                new_mesh.add_face([ancestor_vkeys[k], ancestor_vkeys[k+1], vkeys[h+1], vkeys[h]])
                print("1", [ancestor_vkeys[k], ancestor_vkeys[k+1], vkeys[h+1], vkeys[h]])
                
                k += 1 
                h += 1 
                
            elif anc_ind_next == anc_ind:
                new_mesh.add_face([ancestor_vkeys[k], vkeys[h+1], vkeys[h]])
                print("2", [ancestor_vkeys[k], vkeys[h+1], vkeys[h]])
                new_mesh.vertex_attribute(ancestor_vkeys[k], "tri", 0)
                h += 1 
            
            elif anc_ind >= cur_ind and anc_ind_next >= cur_ind_next and cur_ind_next > cur_ind:
                new_mesh.add_face([ancestor_vkeys[k], ancestor_vkeys[k+1], vkeys[h+1], vkeys[h]])
                print("11", [ancestor_vkeys[k], ancestor_vkeys[k+1], vkeys[h+1], vkeys[h]])
                k += 1 
                h += 1 
            
            elif cur_ind_next == cur_ind:
                new_mesh.add_face([ancestor_vkeys[k], ancestor_vkeys[k+1], vkeys[h]])
                print("22", [ancestor_vkeys[k], ancestor_vkeys[h+1], vkeys[h]])
                new_mesh.vertex_attribute(vkeys[h], "tri", 1)
                k += 1 
            
           
        if k < ancestor_seg_count and h == seg_count:
            new_mesh.add_face([ancestor_vkeys[k], ancestor_vkeys[k+1], vkeys[h]])
        elif k == ancestor_seg_count and h < seg_count:
            new_mesh.add_face([ancestor_vkeys[k], vkeys[h+1], vkeys[h]])
        
        
    row += 1
    
    # save the information of the last row 
    ancestor_seg_count = seg_count
    ancestor_pts = pts
    ancestor_vkeys = vkeys

viewer = App()
viewer.add(mesh)
viewer.show()