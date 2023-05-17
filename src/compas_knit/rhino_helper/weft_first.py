__author__ = "duch"

import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
import ghpythonlib.components as gh
from compas.datastructures import Mesh


tempgeo = [] # DEBUG
text_cur = [] # DEBUG

mesh = Mesh()
mesh.update_default_vertex_attributes({"row": None, "column": None})

for i, crv in enumerate(contour_curves):
    # divide the curve by length, get the points on the curve
    length = crv.GetLength()
    seg_count = int(length / course_dis)
    ts = crv.DivideByCount(seg_count, True)
    pts = [crv.PointAt(t) for t in ts] 
    vkeys = []
    
    # add pts on the curve to mesh
    if i == 0:
        for j, pt in enumerate(pts):
            
            vkey = mesh.add_vertex(x=float(pt.X), y=float(pt.Y), z=float(pt.Z))
            vkeys.append(vkey)
            mesh.vertex_attributes(vkey, ["row", "column"], [i, j])
            
            tempgeo.append(pt)
            text_cur.append(str(j))
    
    else:
        for j, pt in enumerate(pts):
            vkey = mesh.add_vertex(x=float(pt.X), y=float(pt.Y), z=float(pt.Z))
            vkeys.append(vkey)

            # compare the first point in the current row with the previous row
            # to defind the start of the column index
            if j == 0:
                adjust = 0
                closest_ancestor = gh.ClosestPoint(pt, ancestor_pts)[1]
                
                if closest_ancestor == 0:
                    closest_current = gh.ClosestPoint(ancestor_pts[0], pts)[1]
                    if closest_current == 0:
                        # situation I
                        # + | + | + | +  current row
                        # + | + | + | +  ancestor row
                        pass
                    else:
                        # situation II
                        # + | + | + | +  current row
                        #         + | +  ancestor row
                        ancestor_column = mesh.vertex_attributea(ancestor_vkeys[0], "column")
                        adjust -= ancestor_column + closest_current

                else: # closest_ancestor > 0
                    # situation III
                        #         + | +  current row
                        # + | + | + | +  ancestor row
                        ancestor_column = mesh.vertex_attributea(ancestor_vkeys[closest_ancestor], "column")
                        adjust += ancestor_column


            mesh.vertex_attributes(vkey, ["row", "column"], [i, j+adjust])
            tempgeo.append(pt)
            text_cur.append(str(j+adjust))

    
    # save the information of the last row 
    ancestor_seg_count = seg_count
    ancestor_pts = pts
    ancestor_vkeys = vkeys
    
    
# check the weft (column)
column_min = min(mesh.vertices_attribute("column"))
column_max = max(mesh.vertices_attribute("column"))

for j in range(column_min, column_max + 1):
    vkeys = mesh.vertices_where({"column": j})
    pts = [mesh.vertex_coordinates(vkey) for vkey in vkeys]
    count = len(vkeys)
    if j > 1:
        ancestor_indices = []
        current_indices = []
        # for pt in the current row, find the closest point in the ancestor row 
        # CAN BE OPTIMISED
        for i, pt in enumerate(pts):
            ancestor_index = gh.ClosestPoint(pt, ancestor_pts)[1]
            ancestor_indices.append(ancestor_index)
        
        # for pt in the ancestor row, find the closest point in the current row
        # CAN BE OPTIMISED
        for i, pt in enumerate(ancestor_pts):
            current_index = gh.ClosestPoint(pt, pts)[1]
            current_indices.append(current_index)
            text_cur.append(str(current_index)) # DEBUG
        
        k = 0
        h = 0
        count = 0
        # create faces
        while k < ancestor_count-1 and h < count-1 and count < 50:
            count += 1
            anc_ind = ancestor_indices[h]
            cur_ind = current_indices[k]
            anc_ind_next = ancestor_indices[h+1]
            cur_ind_next = current_indices[k+1]

            if anc_ind <= cur_ind and anc_ind_next <= cur_ind_next and anc_ind_next > anc_ind:
                mesh.add_face([ancestor_vkeys[k], ancestor_vkeys[k+1], vkeys[h+1], vkeys[h]])
                k += 1 
                h += 1 
                
            elif anc_ind_next == anc_ind:
                mesh.add_face([ancestor_vkeys[k], vkeys[h+1], vkeys[h]])
                h += 1 
        
    ancestor_vkeys = vkeys
    ancestor_pts = pts
    ancestor_count = count
    
    print(mesh.vertices_attribute("row", keys=vkeys))
    
        



