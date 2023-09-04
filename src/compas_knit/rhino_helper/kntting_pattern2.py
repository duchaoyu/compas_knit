__author__ = "duch"

import os
import rhinoscriptsyntax as rs
import scriptcontext
import Rhino.Geometry as rg
from itertools import chain
import System.Drawing as sd
import time
start_time = time.time()

mesh = input_mesh.copy()
# mesh.flip_cycles()
temp_geo = []




mesh.update_default_vertex_attributes({"checked": False})

min_col = 0
max_col = 0
min_row = 0
max_row = 0
bitmap_dict = {}

# mesh.vertex_attribute(412, "tri", 0)
left = 1
right = 0

def halfedge_loop_r_l(mesh, edge):
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
        edges = [(u, v)]
        
        if mesh.is_edge_on_boundary(u, v):
            while True:
                nbrs = mesh.vertex_neighbors(v)
                fkey = mesh.halfedge_face(u, v)
                # if fkey is None:
                    # fkey = mesh.halfedge_face(v, u)
                if mesh.vertex_attribute(v, "tri") == right:
                    break
                if mesh.vertex_degree(v) == 2:
                    break
                nbrs = mesh.vertex_neighbors(v, ordered=True)
                i = nbrs.index(u)
                u = v
                v = nbrs[i-1]
                # v = nbrs[i - 2]
                edges.append((u, v))
                if v == edges[0][0]:
                    break
                
            return edges
            
        break_v = None
        
        while True:
            count = 2
            fkey = mesh.halfedge_face(u, v)
            if mesh.is_vertex_on_boundary(v) is True:
                break
            if mesh.vertex_attribute(v, "tri") == right:
                count = 3 
                if mesh.vertex_attribute(v, "checked") is False:
                    break
            nbrs = mesh.vertex_neighbors(v, ordered=True)
            i = nbrs.index(u)
            u = v
            v = nbrs[(i - count)%len(nbrs)]
            edges.append((u, v))
            if v == edges[0][0]:
                break
                
        if break_v is not None:
            sel_edges = []                  
            for e in edges:
                if e[0] == break_v:
                    break
                sel_edges.append(e)  
        
            return sel_edges
            
        return edges

def halfedge_loop_l_r(mesh, edge):
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
        edges = [(u, v)]
        
        break_v = None
        while True:
            count = 2
            fkey = mesh.halfedge_face(u, v)
            if mesh.is_vertex_on_boundary(v) is True:
                if mesh.is_edge_on_boundary(u, v) is False:
                    break_v = v
                    break
            if mesh.vertex_attribute(v, "tri") == left:
                break_v = v
                if mesh.vertex_attribute(v, "checked") is True:
                    break
            nbrs = mesh.vertex_neighbors(v, ordered=True)
            
            i = nbrs.index(u)
            u = v
            v = nbrs[(i + count)%len(nbrs)]
            edges.append((u, v))
            if v == edges[0][0]:
                break
                
        print("break", break_v)
        if break_v is not None:
            sel_edges = []                  
            for e in edges:
                if e[0] == break_v:
                    break
                sel_edges.append(e)  
        
            return sel_edges
            
        return edges


def check_nbr_dir(mesh, vkey, filter=True):
    # parameters:
    #   mesh: input mesh
    #   vkey: the vertex to check
    #   dir: "l_r or r_l"
    #   filter: optional, whether filter the checked points
    # output: 
    #   list: [weft_nbrs, course_nbrs]
    nbrs = mesh.vertex_neighbors(vkey)
    course_nbrs = []
    wale_nbrs = []

    for nbr in nbrs:    
        if mesh.vertex_attribute(vkey, "row") != mesh.vertex_attribute(nbr, "row"):
            if filter:
                if mesh.vertex_attribute(nbr, "checked") is True:
                    continue
            course_nbrs.append(nbr)
        else:
            if filter:
                if mesh.vertex_attribute(nbr, "checked") is True:
                    continue
            wale_nbrs.append(nbr)
    
    print(vkey, wale_nbrs, course_nbrs)
    
    if course_nbrs == []:
        vkey, course_nbr = check_nbr_dir(mesh, wale_nbrs[0], filter=True)
        return vkey, course_nbr
    
    
    course_nbr = course_nbrs[0]
    if len(course_nbrs) == 1:
        if mesh.vertex_attribute(course_nbr, "tri") == right:
            vkey, course_nbr = check_nbr_dir(mesh, course_nbr, filter=True)
            # print(course_nbr, "TRIDEBUG", mesh.vertex_attribute(course_nbr, "tri"))
            return vkey, course_nbr
            
            
        
    if len(course_nbrs) > 1:    
        if mesh.vertex_attribute(vkey, "tri") == left:
            for can in course_nbrs:
                if mesh.vertex_attribute(can, "row") > mesh.vertex_attribute(course_nbr, "row"):
                    course_nbr = can
                elif mesh.vertex_attribute(can, "row") == mesh.vertex_attribute(course_nbr, "row"):
                    if mesh.vertex_attribute(can, "column") < mesh.vertex_attribute(course_nbr, "column"):
                        course_nbr = can
        else:
            for can in course_nbrs:
                if mesh.vertex_attribute(can, "row") < mesh.vertex_attribute(course_nbr, "row"):
                    course_nbr = can
                elif mesh.vertex_attribute(can, "row") == mesh.vertex_attribute(course_nbr, "row"):
                    if mesh.vertex_attribute(can, "column") < mesh.vertex_attribute(course_nbr, "column"):
                        course_nbr = can

    return vkey, course_nbr


def course_r_l(mesh, start, filter=True):
    # parameters:
    #   mesh: input mesh
    #   start: the vertex to start
    #   course_nbr: nbr in the course direction
    # output: 
    #   pts: list of point coordinates (x, y, z)
    start_, nbr = check_nbr_dir(mesh, start, filter=True)

    loop = halfedge_loop_r_l(mesh, (start_, nbr))
    
    if start == 105:
        loop2 = halfedge_loop_r_l(mesh, (1162, 1233))
        loop += loop2
    if start == 2168:
        loop2 = halfedge_loop_r_l(mesh, (2238, 2259))
        loop += loop2
    if start == 2193:
        loop2 = halfedge_loop_r_l(mesh, (2292, 2304))
        loop += loop2
    
    loop_vkeys = chain.from_iterable(loop) # flatten the nested loop
        
    loop_set = set()
    vkeys = []
    pts = []
    for vkey in loop_vkeys:
        if vkey not in loop_set:
            mesh.vertex_attribute(vkey, "checked", True)
            loop_set.add(vkey)
            vkeys.append(vkey)
            xyz = mesh.vertex_coordinates(vkey)
            pts.append(xyz)
    return vkeys, pts



def course_l_r(mesh, start, filter=True):
    # parameters:
    #   mesh: input mesh
    #   start: the vertex to start
    #   course_nbr: nbr in the course direction
    # output: 
    #   pts: list of point coordinates (x, y, z)
    start_, nbr = check_nbr_dir(mesh, start, filter=True)
    print("debug", start, start_, nbr, mesh.vertex_attribute(start, "tri"))
    
    loop = halfedge_loop_l_r(mesh, (start_, nbr))
    
    loop_set = set()
    loop_vkeys = chain.from_iterable(loop) # flatten the nested loop
    vkeys = []
    pts = []
    for vkey in loop_vkeys:
        if vkey not in loop_set:
            loop_set.add(vkey)
            vkeys.append(vkey)
    """
    if mesh.vertex_attribute(start, "tri") == right:
        if mesh.is_vertex_on_boundary(start) is True:
            mid_pt = mesh.edge_midpoint(start, vkeys[1])
            pts.append(mid_pt)
    """
    
    if start != start_:
        prev = mesh.halfedge_before(*loop[0])
        mid_pt = mesh.edge_midpoint(*prev)
        pts.append(mid_pt)
    
    if mesh.vertex_attribute(loop[-1][1], "tri") == left:
        if mesh.is_vertex_on_boundary(loop[-1][1]) is False:
            loop = loop[:-1]
        else:
            fkey = mesh.halfedge_face(*loop[-1])
            if len(mesh.face_vertices(fkey)) == 3:
                loop = loop[:-1]
        
    for edge in loop:
        next = mesh.halfedge_after(*edge)
        mid_pt = mesh.edge_midpoint(*next)
        pts.append(mid_pt)

    return vkeys, pts

location = [0, 0]

count = 0 
while True and count < 111:
    count += 1

    # right to left
    # --------------
    # find the neighbour
    
    odd_vkeys, odd_pts = course_r_l(mesh, start, filter=True)
    
    start = odd_vkeys[-1]
    
    
    if mesh.vertex_attribute(odd_vkeys[0], "tri") == left and mesh.is_vertex_on_boundary(odd_vkeys[0]) is False:
        odd_vkeys = odd_vkeys[1:]
        odd_pts = odd_pts[1:]    
    
    if mesh.vertex_attribute(odd_vkeys[-1], "tri") == right and mesh.is_vertex_on_boundary(odd_vkeys[-1]) is False:
        odd_vkeys = odd_vkeys[:-1]
        odd_pts = odd_pts[:-1]    
    
    
    odd_pts_r = [rg.Point3d(x=xyz[0], y=xyz[1], z=xyz[2]) for xyz in odd_pts]
    temp_geo.extend(odd_pts_r) 
    print("r-l", odd_vkeys)

    # bitmap
    for _ in range(len(odd_pts)):
        bitmap_dict[tuple(location)] = 1
        location[0] -= 1
    if location[0] <= min_col:
        min_col = location[0]
    # go to the next row
    max_row += 1
    location[0] += 1
    location[1] += 1


    # left to right
    # --------------
    # find the neighbour
    
    even_vkeys, even_pts = course_l_r(mesh, start, filter=True)
    start = even_vkeys[-1]
        
    
    
    even_pts_r = [rg.Point3d(x=xyz[0], y=xyz[1], z=xyz[2]) for xyz in even_pts]
    temp_geo.extend(even_pts_r) 
    print("l-r", even_vkeys)
    
    # bitmap
    for _ in range(len(even_pts)):
        bitmap_dict[tuple(location)] = 1
        location[0] += 1
    if location[0] >= max_col:
        max_col = location[0]
    max_row += 1
    location[0] -= 1
    location[1] += 1


    

    if time.time() - start_time > 10: # 1 minute limit
        raise Exception("time's up!")


# add last few lines.... ===================================
loop = mesh.edge_loop((144,145))
loop_vkeys = chain.from_iterable(loop) # flatten the nested loop
loop_set = set()
vkeys = []
pts = []
for vkey in loop_vkeys:
    if vkey not in loop_set:
        mesh.vertex_attribute(vkey, "checked", True)
        loop_set.add(vkey)
        vkeys.append(vkey)
        xyz = mesh.vertex_coordinates(vkey)
        pts.append(xyz)
even_pts_r = [rg.Point3d(x=xyz[0], y=xyz[1], z=xyz[2]) for xyz in pts]
temp_geo.extend(even_pts_r) 

# bitmap
for _ in range(len(pts)):
    bitmap_dict[tuple(location)] = 1
    location[0] -= 1
if location[0] <= min_col:
    min_col = location[0]
# go to the next row
max_row += 1
# location[0] += 1
location[1] += 1

loop = mesh.edge_loop((2341,2336))
pts = []

for edge in loop:
    next = mesh.halfedge_after(*edge)
    mid_pt = mesh.edge_midpoint(*next)
    pts.append(mid_pt)
    
odd_pts_r = [rg.Point3d(x=xyz[0], y=xyz[1], z=xyz[2]) for xyz in pts]
temp_geo.extend(odd_pts_r) 

# bitmap
for _ in range(len(pts)):
    bitmap_dict[tuple(location)] = 1
    location[0] += 1
if location[0] >= max_col:
    max_col = location[0]
max_row += 1
# location[0] -= 1
location[1] += 1

# end of add last few lines.... ===================================

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
