__author__ = "duch"

import os

# import System.Drawing as sd

from itertools import chain
from compas.datastructures import Mesh
from compas_view2.app import App
from compas.geometry import Polyline


folder = "/Users/duch/Desktop/prototype/shanghai/knitting_pattern"
filename = "mesh1.json"
file = os.path.join(folder, filename)
mesh = Mesh.from_json(file)

# mesh.flip_cycles()

temp_geo = []

mesh.update_default_vertex_attributes({"checked": False})

min_col = 0
max_col = 0
min_row = 0
max_row = 0
bitmap_dict = {}



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
        toggle = 0
        
        u, v = edge
        edges = [(u, v)]
        
        if mesh.is_edge_on_boundary(u, v):
            while True:
                nbrs = mesh.vertex_neighbors(v)
                fkey = mesh.halfedge_face(u, v)
                # if fkey is None:
                    # fkey = mesh.halfedge_face(v, u)
                if mesh.vertex_attribute(v, "tri") == toggle:
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
            if mesh.vertex_attribute(v, "tri") == toggle:
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
        toggle = 1
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
            if mesh.vertex_attribute(v, "tri") == toggle:
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
    
    if course_nbrs == []:
        vkey, course_nbr = check_nbr_dir(mesh, wale_nbrs[0], filter=True)
        return vkey, course_nbr
    
    
    course_nbr = course_nbrs[0]
    if len(course_nbrs) == 1:
        if mesh.vertex_attribute(course_nbr, "tri") == 1:
            vkey, course_nbr = check_nbr_dir(mesh, course_nbr, filter=True)
            return vkey, course_nbr
        
    if len(course_nbrs) > 1:    
        if mesh.vertex_attribute(vkey, "tri") == 0:
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
                        course_nbr

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
    print("debug", start_, nbr)
    
    loop = halfedge_loop_l_r(mesh, (start_, nbr))
    
    loop_set = set()
    loop_vkeys = chain.from_iterable(loop) # flatten the nested loop
    vkeys = []
    pts = []
    for vkey in loop_vkeys:
        if vkey not in loop_set:
            loop_set.add(vkey)
            vkeys.append(vkey)
            
    if start != start_:
        prev = mesh.halfedge_before(*loop[0])
        mid_pt = mesh.edge_midpoint(*prev)
        pts.append(mid_pt)
    
    if mesh.vertex_attribute(loop[-1][1], "tri") == 0:
        if mesh.is_vertex_on_boundary(loop[-1][1]) is False:   
            loop = loop[:-1]
        
    for edge in loop:
        next = mesh.halfedge_after(*edge)
        mid_pt = mesh.edge_midpoint(*next)
        pts.append(mid_pt)

    return vkeys, pts




mesh.delete_vertex(0)

location = [0, 0]


count = 0 
start =  1

try:
    while True and count < 90:
        count += 1

        # right to left
        # --------------
        # find the neighbour
        
        odd_vkeys, odd_pts = course_r_l(mesh, start, filter=True)
        temp_geo.extend(odd_pts) 
        print(count, odd_vkeys)


        # left to right
        # --------------
        # find the neighbour
        
        even_vkeys, even_pts = course_l_r(mesh, odd_vkeys[-1], filter=True)
        temp_geo.extend(even_pts) 
        print(count, even_vkeys)
        
        start = even_vkeys[-1]
except:
    print("end")

polyline = Polyline(temp_geo)


viewer = App()
# viewer.add(mesh)
viewer.add(polyline)
viewer.show()