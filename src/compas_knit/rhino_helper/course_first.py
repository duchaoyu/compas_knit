__author__ = "duch"

import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import ghpythonlib.components as gh
from compas.datastructures import Mesh


tempgeo = [] # DEBUG
text_cur = [] # DEBUG

mesh = Mesh()
mesh.update_default_vertex_attributes({"row": None, "column": None, "tri": None})


for i, crv in enumerate(contour_curves):
    
    # divide the curve by length, get the points on the curve
    length = crv.GetLength()
    seg_count = int(length / course_dis)
    ts = crv.DivideByCount(seg_count, True)
    pts = [crv.PointAt(t) for t in ts] 
    vkeys = []
    
    # add pts on the curve to mesh
    for j, pt in enumerate(pts):
        tempgeo.append(pt)
        vkey = mesh.add_vertex(x=float(pt.X), y=float(pt.Y), z=float(pt.Z))
        mesh.vertex_attributes(vkey, ["row", "column"], [i, j])
        vkeys.append(vkey)
    
    
    # add faces to the mesh
    # this process starting from the second row
    if i > 0:
        ancestor_indices = []
        current_indices = []
        # for pt in the current row, find the closest point in the ancestor row 
        # CAN BE OPTIMISED
        for j, pt in enumerate(pts):
            ancestor_index = gh.ClosestPoint(pt, ancestor_pts)[1]
            ancestor_indices.append(ancestor_index)
        
        # for pt in the ancestor row, find the closest point in the current row
        # CAN BE OPTIMISED
        for j, pt in enumerate(ancestor_pts):
            current_index = gh.ClosestPoint(pt, pts)[1]
            current_indices.append(current_index)
            text_cur.append(str(current_index)) # DEBUG
        
        
        print(ancestor_indices, current_indices)
        
        k = 0
        h = 0
        
        # create faces
        count = 0
        while k < ancestor_seg_count and h < seg_count and count < 150:
            count += 1
            anc_ind = ancestor_indices[h]
            cur_ind = current_indices[k]
            anc_ind_next = ancestor_indices[h+1]
            cur_ind_next = current_indices[k+1]

            if anc_ind <= cur_ind and anc_ind_next <= cur_ind_next and anc_ind_next > anc_ind:
                mesh.add_face([ancestor_vkeys[k], ancestor_vkeys[k+1], vkeys[h+1], vkeys[h]])
                print("1", [ancestor_vkeys[k], ancestor_vkeys[k+1], vkeys[h+1], vkeys[h]])
                
                k += 1 
                h += 1 
                
            elif anc_ind_next == anc_ind:
                # if mesh.edge_length(ancestor_vkeys[k], vkeys[h]) <= course_dis * 2:
                mesh.add_face([ancestor_vkeys[k], vkeys[h+1], vkeys[h]])
                print("2", [ancestor_vkeys[k], vkeys[h+1], vkeys[h]])
                mesh.vertex_attribute(ancestor_vkeys[k], "tri", 0)
                h += 1 
            
            elif anc_ind >= cur_ind and anc_ind_next >= cur_ind_next and cur_ind_next > cur_ind:
                mesh.add_face([ancestor_vkeys[k], ancestor_vkeys[k+1], vkeys[h+1], vkeys[h]])
                print("11", [ancestor_vkeys[k], ancestor_vkeys[k+1], vkeys[h+1], vkeys[h]])
                k += 1 
                h += 1 
            
            elif cur_ind_next == cur_ind:
                # if mesh.edge_length(ancestor_vkeys[k], vkeys[h]) <= course_dis * 2:
                mesh.add_face([ancestor_vkeys[k], ancestor_vkeys[k+1], vkeys[h]])
                print("22", [ancestor_vkeys[k], ancestor_vkeys[h+1], vkeys[h]])
                mesh.vertex_attribute(vkeys[h], "tri", 1)
                k += 1 
            
            '''
            elif cur_ind <= anc_ind and cur_ind <= anc_ind_next and cur_ind_next > anc_ind_next:
            
                # ancestor     k    | k+1
                # current   h | h+1 | h+2
                mesh.add_face([ancestor_vkeys[k], vkeys[h+1], vkeys[h]])
                print("3", [k, h+1, h], [cur_ind, anc_ind_next, anc_ind])
                h += 1 
                
            elif anc_ind <= cur_ind and anc_ind <= cur_ind_next and anc_ind_next > cur_ind_next:
                # ancestor  k | k+1 | k+2
                # current       h   | h+1 
                mesh.add_face([ancestor_vkeys[k], ancestor_vkeys[k+1], vkeys[h]])
                print("4", [k, h+1, h], [cur_ind, cur_ind_next, anc_ind])
                k += 1

            elif cur_ind <= anc_ind and cur_ind <= anc_ind_next:
                # ancestor  k      |   k+1
                # current   h | h+1 | h+2
                mesh.add_face([ancestor_vkeys[k], vkeys[h+1], vkeys[h]])
                print("5", [ancestor_vkeys[k], vkeys[h+1], vkeys[h]])
                k += 1 
            else:
                print("smething")
            '''
        if k < ancestor_seg_count and h == seg_count:
            mesh.add_face([ancestor_vkeys[k], ancestor_vkeys[k+1], vkeys[h]])
            mesh.vertex_attribute(vkeys[h], "tri", 1)
            
        elif k == ancestor_seg_count and h < seg_count:
            mesh.add_face([ancestor_vkeys[k], vkeys[h+1], vkeys[h]])
            mesh.vertex_attribute(ancestor_vkeys[k], "tri", 0)
        
        '''
        # find the start vertex's cloest point in the ancestor row
        start_index_ancestor = gh.ClosestPoint(pts[0], ancestor_pts)[1]
        start_index_current =  gh.ClosestPoint(ancestor_pts[0], pts)[1]
        end_index_ancestor = gh.ClosestPoint(pts[-1], ancestor_pts)[1]
        end_index_current = gh.ClosestPoint(ancestor_pts[-1], pts)[1]

        if start_index_ancestor > start_index_current:
        # situation I: 
        # 0`| 1`| 2`| 3`| 4`|  ancestor row, start_index_ancestor=2
        #         0 | 1 | 2 |  current row, start_index_current=0
            # for k in range(closest_index_ancestor):
            #     mesh.add_face([ancestor_vkeys[k+1], ancestor_vkeys[k], vkeys[0]])
            # for j in range(len(vkeys) - 1):
            #     mesh.add_face([vkeys[j], vkeys[j+1], ancestor_vkeys[j+1+closest_index_ancestor], ancestor_vkeys[j+closest_index_ancestor]])
            raise NotImplementedError("not implemented")
        elif start_index_ancestor < start_index_current:
        # situation II:
        #         0`| 1`| 2`|  ancestor row, start_index_ancestor=0
        # 0 | 1 | 2 | 3 | 4 |  current row, start_index_current=2
            # closest_index = gh.ClosestPoint(ancestor_pts[0], 
            # mesh.vertex_attribute(vkey, "ancestor", ancestor_vkeys[closest_index]+j)
            raise NotImplementedError("not implemented")
        # situation III:
        # 0`| 1`| 2`| 3`| 4`|  ancestor row, start_index_ancestor=0
        # 0 | 1 | 2 | 3 | 4 |  current row, start_index_current=0
        else:
            if ancestor_seg_count < seg_count:
                for k in range(seg_count-1):
                    if k < ancestor_seg_count-1: 
                        mesh.vertex_attribute(vkey, "ancestor", ancestor_vkeys[k])
                        mesh.add_face([vkeys[k], vkeys[k+1], ancestor_vkeys[k+1], ancestor_vkeys[k]])
                    else:
                        mesh.vertex_attribute(vkey, "ancestor", ancestor_vkeys[-1])
                        mesh.add_face([vkeys[k], vkeys[k+1], ancestor_vkeys[-1]])
        '''
                
    
    # save the information of the last row 
    ancestor_seg_count = seg_count
    ancestor_pts = pts
    ancestor_vkeys = vkeys
        

print(mesh)
