from itertools import chain
from compas_view2.app import App
from compas_view2.shapes import Text
from compas.geometry import Polyline, Sphere
from compas_view2.objects import Collection
from compas.datastructures import Mesh
from PIL import Image
import os


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
        if mesh.is_vertex_on_boundary(v) is True:
            break
        # check the singularites
        if mesh.vertex_degree(v) > 4:
            next = mesh.halfedge_after(u, v)
            # print(v, "v")
            if mesh.has_edge((next[1], u)) is True or mesh.has_edge((u, next[1])) is True: 
                if mesh.edge_attribute((u, v), 'course')[(u, v)] is False:
                    if mesh.vertex_attribute(v, "checked") is False:
                        mesh.vertex_attribute(v, "special", "t") # what does this mean???!!! please write comment
                        break
                else:
                    raise ValueError
            else:
                nextnext = mesh.halfedge_after(next[1], next[0])
                if mesh.has_edge((nextnext[1], next[1])) is True or mesh.has_edge((next[1], nextnext[1])) is True:
                    mesh.vertex_attribute(v, "special", "increase")
                    pass
                else:
                    nbrs = mesh.vertex_neighbors(v, ordered=True)
                    for nbr in nbrs:
                        if nbr == u: 
                            continue
                        a = mesh.edge_attribute((v, nbr), 'course')[(nbr, v)]
                        b = mesh.edge_attribute((v, nbr), 'course')[(v, nbr)]
                        if (a is True or b is True) and (not (a is True and b is True)):
                            i_u = nbrs.index(u)
                            i_nbr = nbrs.index(nbr)
                            count = (i_u-i_nbr)%len(nbrs)
                            # print(nbr, "nbr")

                    # count = 3
                    # print((nextnext[1], next[1]))
                    # print(next, u, v)

        nbrs = mesh.vertex_neighbors(v, ordered=True)
        i = nbrs.index(u)
        u = v
        v = nbrs[(i - count) % len(nbrs)]
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
        # fkey = mesh.halfedge_face(u, v)
        if mesh.is_vertex_on_boundary(v) is True:
            if mesh.is_edge_on_boundary(u, v) is False:
                break_v = v
                break
        if mesh.vertex_degree(v) > 4:
            break_v = v
            if mesh.edge_attribute((u, v), 'course')[(u, v)] is True:
                # if mesh.vertex_attribute(v, "checked") is True:
                break
            elif mesh.vertex_attribute(v, "checked") is True:
                break
        nbrs = mesh.vertex_neighbors(v, ordered=True)

        i = nbrs.index(u)
        u = v
        v = nbrs[(i + count) % len(nbrs)]
        edges.append((u, v))
        if v == edges[0][0]:
            break
    # print("break", break_v)
    if break_v is not None:
        sel_edges = []
        for e in edges:
            if e[0] == break_v:
                break
            sel_edges.append(e)
        # print("break v",break_v,  sel_edges)
        return sel_edges

    return edges


def course_r_l(mesh, start_edge):
    # parameters:
    #   mesh: input mesh
    #   start: the last edge in the edge loop
    #   course_nbr: nbr in the course direction
    # output:
    #   pts: list of point coordinates (x, y, z)
    edge = check_nbr_r(mesh, start_edge)

    loop = halfedge_loop_r_l(mesh, edge)
    for (u, v) in loop:
        mesh.edge_attribute((u, v), 'course')[(u, v)] = True

    loop_vkeys = chain.from_iterable(loop)  # flatten the nested loop
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
    # if mesh.vertex_attribute(vkeys[-1], "tri") == 0:
    #     mesh.vertex_attribute(vkey, "checked", False) # NEEDED?
    return vkeys, pts


def course_l_r(mesh, start_edge):
    # parameters:
    #   mesh: input mesh
    #   start: the last edge in the edge loop
    #   course_nbr: nbr in the course direction
    # output:
    #   pts: list of point coordinates (x, y, z)
    edge = check_nbr_l(mesh, start_edge)

    loop = halfedge_loop_l_r(mesh, edge)
    for (u, v) in loop:
        mesh.edge_attribute((u, v), 'course')[(u, v)] = True

    # for (u, v) in loop: # debug
    #     print(mesh.edge_attribute((u, v), 'checked')) # debug

    loop_set = set()
    loop_vkeys = chain.from_iterable(loop)  # flatten the nested loop
    vkeys = []
    pts = []
    for vkey in loop_vkeys:
        if vkey not in loop_set:
            loop_set.add(vkey)
            vkeys.append(vkey)

    if start_edge[1] != edge[0]:
        prev = mesh.halfedge_before(*loop[0])
        mid_pt = mesh.edge_midpoint(*prev)
        pts.append(mid_pt)

    if mesh.vertex_attribute(loop[-1][1], "tri") == 0 or mesh.vertex_attribute(loop[-1][1], "tri") == 1:
        if mesh.is_vertex_on_boundary(loop[-1][1]) is False:
            loop = loop[:-1]
        else:
            fkey = mesh.halfedge_face(*loop[-1])
            if len(mesh.face_vertices(fkey)) == 3:
                loop = loop[:-1]
            else:
                next = mesh.halfedge_after(*loop[-1])
                if mesh.is_edge_on_boundary(*next) is False:
                    loop = loop[:-1]
            # pass
        # else:
        #     if mesh.vertex_degree(loop[-1][1]) >= 4:
        #         loop = loop[:-1]

    for edge in loop:
        next = mesh.halfedge_after(*edge)
        mid_pt = mesh.edge_midpoint(*next)
        pts.append(mid_pt)

    return vkeys, pts


def check_nbr_l(mesh, start_edge):
    fkey = mesh.halfedge_face(*start_edge)
    if len(mesh.face_vertices(fkey)) == 4:
        next = mesh.halfedge_after(*start_edge)
        nextnext = mesh.halfedge_after(*next)
        return nextnext
    elif mesh.vertex_attribute(start_edge[1], "special") == "t":
        next = mesh.halfedge_after(*start_edge)
        return next
    else:      
        raise ValueError


def check_nbr_r(mesh, start_edge):
    if mesh.edge_attribute(start_edge, 'course')[start_edge] is False:
        return start_edge
    else:
        return start_edge[::-1]


mesh = Mesh.from_json("/Users/duch/Documents/PhD/knit/benchmarks/simple_shell_tri.json")
mesh.flip_cycles()

# pre-process the mesh for unexpected occasions
mesh.delete_face(14036)
mesh.add_face([14277, 14436, 14300])
mesh.add_face([14300, 14436, 14459])

mesh.update_default_vertex_attributes({"checked": False})
mesh.update_default_vertex_attributes({"special": False})
mesh.update_default_edge_attributes({"course": {}})
for (u, v) in mesh.edges():
    mesh.edge_attribute((u, v), "course", {(u, v): False, (v, u): False})
    mesh.edge_attribute((u, v), "wale", False)





startedge = (17239, 17227)
polyline_points = []
polyline_vkeys = []


# for bitmap
min_col = 0
max_col = 0
min_row = 0
max_row = 0
bitmap_dict = {}
location = [0, 0]


count = 0
while True and count < 70:
    count += 1
    print("count", count)
    # R -> L 
    odd_vkeys, odd_pts = course_r_l(mesh, startedge)
    polyline_points.extend(odd_pts)
    polyline_vkeys.extend(odd_vkeys)

    for vkey in odd_vkeys:
        if mesh.vertex_attribute(vkey, "special") == "increase":
            print(vkey, "increase")

    # print(odd_vkeys)

    # bitmap
    for i, vkey in enumerate(odd_vkeys):
        if mesh.vertex_attribute(vkey, "special") == "increase":
            bitmap_dict[tuple(location)] = 2  # 2 mean incease
        else:
            bitmap_dict[tuple(location)] = 1  # 1 is default color, a simple stitch 
        location[0] -= 1
    
    # for _ in range(len(odd_pts)):
    #     bitmap_dict[tuple(location)] = 1
    #     location[0] -= 1
    if location[0] <= min_col:
        min_col = location[0]
    # go to the next row
    max_row += 1
    location[0] += 1
    location[1] += 1


    # L -> R 
    startedge = (odd_vkeys[-2], odd_vkeys[-1])
    even_vkeys, even_pts = course_l_r(mesh, startedge)
    polyline_points.extend(even_pts)
    polyline_vkeys.extend(even_vkeys)

    startedge = (even_vkeys[-2], even_vkeys[-1])

    # bitmap
    for _ in range(len(even_pts)):
        bitmap_dict[tuple(location)] = 1
        location[0] += 1
    if location[0] >= max_col:
        max_col = location[0]
    max_row += 1
    location[0] -= 1
    location[1] += 1





polyline = Polyline(polyline_points)
# print(polyline_vkeys)

polyline.to_json("/Users/duch/Documents/PhD/knit/benchmarks/polyline.json")


# bitmap
directory = "/Users/duch/Documents/PhD/knit/benchmarks"
output_path = os.path.join(directory, 'simple_shell.bmp')

# initiate the size of the bitmap
rows = max_row-min_row
columns = max_col-min_col

image = Image.new("RGB", (columns + 1, rows + 1), "white")

# black
pixels = image.load()
for (loc, val) in bitmap_dict.items():
    if val == 1:
        pixels[loc[0] - min_col, rows-loc[1]] = (0, 0, 0)
    elif val == 2:
        pixels[loc[0] - min_col, rows-loc[1]] = (255, 0, 0)
    # bm.SetPixel(loc[0] + columns, loc[1], sd.Color.Black)

image.save(output_path)


# show = True

# if show:
#     vkeys = mesh.vertices_where({"checked": True})
#     spheres = []
#     for vkey in vkeys:
#         xyz = mesh.vertex_coordinates(vkey)
#         # spheres.append(Sphere(xyz, 0.01))

#     viewer = App()
#     # viewer.add(mesh, show_faces=False, show_lines=True)
#     viewer.add(polyline, linecolor=(0.7, 0., 0.7))
#     viewer.add(Collection(spheres))
#     # text objects
#     maxkey = len(list(mesh.vertices()))
#     for vkey in mesh.vertices():
#         txt = Text(str(vkey), mesh.vertex_coordinates(vkey), height=50)
#         viewer.add(txt, color=(vkey/maxkey, vkey/maxkey, 0))

#     viewer.show()
