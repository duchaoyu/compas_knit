__author__ = "duch"

import os
import rhinoscriptsyntax as rs
import Rhino.Geometry as rg
from itertools import chain
import System.Drawing as sd

mesh = input_mesh.copy()
temp_geo = []


mesh.update_default_vertex_attributes({"checked": False})

min_col = 0
max_col = 0
min_row = 0
max_row = 0
bitmap_dict = {}

def halfedge_loop(mesh, edge):
        """Find all edges on the same loop as the halfedge, in the direction of the halfedge.

        Parameters
        ----------
        edge : tuple[int, int]
            The identifier of the starting edge.

        Returns
        -------
        list[tuple[int, int]]
            The edges on the same loop as the given edge.

        """
        u, v = edge
        if mesh.is_edge_on_boundary(u, v):
            return mesh._halfedge_loop_on_boundary(edge)
        edges = [(u, v)]
        while True:
            
            fkey = mesh.halfedge_face(u, v)
            if mesh.is_vertex_on_boundary(v) is True:
                break
            if len(mesh.face_vertices(fkey)) == 3:
                break
            nbrs = mesh.vertex_neighbors(v, ordered=True)
            
            """
            nbrs = mesh.vertex_neighbors(v, ordered=True)
            if len(nbrs) != 4:
                # if mesh.vertex_attribute(v, "checked") is False:
                fkey = mesh.halfedge_face(u, v)
                print(fkey, mesh.face_vertices(fkey))
                # if len(mesh.face_vertices(fkey)) == 3:
                break
            """
            i = nbrs.index(u)
            u = v
            v = nbrs[(i + 2)%len(nbrs)]
            # v = nbrs[i - 2]
            edges.append((u, v))
            if v == edges[0][0]:
                break
        return edges
        
def check_nbr_dir(mesh, vkey, filter=True):
    # parameters:
    #   mesh: input mesh
    #   vkey: the vertex to check
    #   filter: optional, whether filter the checked points
    # output: 
    #   list: [weft_nbrs, course_nbrs]
    weft_nbrs = []
    course_nbrs = []
    nbrs = mesh.vertex_neighbors(vkey)
    for nbr in nbrs:
        if mesh.vertex_attribute(vkey, "row") == mesh.vertex_attribute(nbr, "row"):
            if filter:
                if mesh.vertex_attribute(nbr, "checked") is True:
                    continue
            weft_nbrs.append(nbr)

        else:
            # if filter:
            #     if mesh.vertex_attribute(nbr, "checked") is True:
            #         continue
            course_nbrs.append(nbr)
    return weft_nbrs, course_nbrs

def course_even(mesh, start, course_nbr):
    # parameters:
    #   mesh: input mesh
    #   start: the vertex to start
    #   course_nbr: nbr in the course direction
    # output: 
    #   pts: list of point coordinates (x, y, z)
    loop = halfedge_loop(mesh, (start, course_nbr))
    loop_set = set()
    loop_vkeys = chain.from_iterable(loop) # flatten the nested loop
    pts = []
    for vkey in loop_vkeys:
        if vkey not in loop_set:
            mesh.vertex_attribute(vkey, "checked", True)
            loop_set.add(vkey)
            xyz = mesh.vertex_coordinates(vkey)
            pts.append(xyz)
    return pts

def course_odd(mesh, start, weft_nbr):
    # create an odd line course
    # this line is always in the middle of the edge strip
    # parameters:
    #   mesh: input mesh
    #   start: the vertex to start
    #   weft_nbr: nbr in the weft direction
    # output: 
    #   pts: list of point coordinates (x, y, z)
    strips = mesh.edge_strip((start, weft_nbr))
    pts = []
    for (a,b) in strips:
        mid_pt = mesh.edge_midpoint(a, b)
        pts.append(mid_pt)
    return pts


location = [0, 0]
try: 
    while True:
        weft_nbrs, course_nbrs = check_nbr_dir(mesh, start, True)
            
        even_pts = course_even(mesh, start, course_nbrs[0])
        even_pts_r = [rg.Point3d(x=xyz[0], y=xyz[1], z=xyz[2]) for xyz in even_pts]
        temp_geo.extend(even_pts_r)
        # bitmap
        for _ in range(len(even_pts)):
            bitmap_dict[tuple(location)] = 1
            print(location)
            location[0] -= 1
        if location[0] <= min_col:
            min_col = location[0]
        # go to the next row
        max_row += 1
        location[0] += 1
        location[1] += 1

        
        odd_pts = course_odd(mesh, start, weft_nbrs[0])
        odd_pts_r = [rg.Point3d(x=xyz[0], y=xyz[1], z=xyz[2]) for xyz in odd_pts]
        temp_geo.extend(odd_pts_r)
        len_odd_pts = len(odd_pts)
        
        # bitmap
        for _ in range(len(odd_pts)):
            print(location)
            bitmap_dict[tuple(location)] = 1
            location[0] += 1
        if location[0] >= max_col:
            max_col = location[0]
        max_row += 1
        location[0] -= 1
        location[1] += 1
    
        start = weft_nbrs[0]
except:
    print("error")


"""
# for debugging
weft_nbrs, course_nbrs = check_nbr_dir(mesh, start, True)
print(weft_nbrs, course_nbrs)
even_pts = course_even(mesh, start, course_nbrs[0])
even_pts_r = [rg.Point3d(x=xyz[0], y=xyz[1], z=xyz[2]) for xyz in even_pts]
temp_geo.extend(even_pts_r)
        

odd_pts = course_odd(mesh, start, weft_nbrs[0])
odd_pts_r = [rg.Point3d(x=xyz[0], y=xyz[1], z=xyz[2]) for xyz in odd_pts]
temp_geo.extend(odd_pts_r)
"""
print(max_row, min_row, max_col, min_col)
# print(bitmap_dict)


directory = "/Users/duch/Desktop"
output_path = os.path.join(directory, 'knit.bmp')

# initiate the size of the bitmap
rows = max_row-min_row
columns = max_col-min_col
print(rows, columns)
bm = sd.Bitmap(columns + 1, rows + 1)

# color the bitmap to all White
for i in range(columns+1):
    for j in range(rows+1):
        bm.SetPixel(i,j,sd.Color.White)

# black
for (loc, val) in bitmap_dict.items():
    print(loc[0] + columns, loc[1])
    bm.SetPixel(loc[0] + columns, loc[1],sd.Color.Black)
    

bm.Save(output_path, sd.Imaging.ImageFormat.Bmp)   
  