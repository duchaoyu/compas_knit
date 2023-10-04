
from itertools import chain


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
            # fkey = mesh.halfedge_face(u, v)
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
        # fkey = mesh.halfedge_face(u, v)
        if mesh.is_vertex_on_boundary(v) is True:
            break
        if mesh.vertex_attribute(v, "tri") == toggle:
            # if mesh.vertex_attribute(v, "checked") is True:
            #     print(v, "continue")
            #     pass
            if mesh.edge_attribute((u, v), 'checked')[(u, v)] is False:
                if mesh.vertex_attribute(v, "checked") is False:
                # count = 3
                    break
                else:
                    count = 3 
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
        if mesh.vertex_attribute(v, "tri") == toggle:
            break_v = v
            if mesh.edge_attribute((u, v), 'checked')[(u, v)] is True:
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


def check_nbr_dir(mesh, vkey, filter=True):
    # parameters:
    #   mesh: input mesh
    #   vkey: the vertex to check
    #   filter: optional, whether filter the checked points
    # output:
    #   (vkey, looping_nbr)
    nbrs = mesh.vertex_neighbors(vkey)
    print("nbrs", nbrs)
    looping_nbrs = []
    same_row_nbrs = []

    # iterate through all the nbrs of the start vkey
    for nbr in nbrs:
        # use attribute "row" to check which direction this neighbour is
        if mesh.vertex_attribute(vkey, "row") != mesh.vertex_attribute(nbr, "row"):
            if filter:
                if mesh.vertex_attribute(vkey, "checked") is True: # the end of an odd row
                    if mesh.vertex_attribute(vkey, "tri") == 0:

                        if mesh.edge_attribute((vkey, nbr), 'checked')[(nbr, vkey)] is True:
                            # if mesh.vertex_attribute(nbr, "checked") is True:
                            continue
                    elif mesh.vertex_attribute(vkey, "tri") == 1:
                        if mesh.edge_attribute((vkey, nbr), 'checked')[(vkey, nbr)] is True:
                            # if mesh.vertex_attribute(nbr, "checked") is True:
                            continue
                    else:
                        if mesh.edge_attribute((vkey, nbr), 'checked')[(nbr, vkey)] is True:
                            # if mesh.vertex_attribute(nbr, "checked") is True:
                            continue
                else:               
                    if mesh.edge_attribute((vkey, nbr), 'checked')[(vkey, nbr)] is True:
                        continue

            looping_nbrs.append(nbr)
        else:
            if filter:
                # if mesh.edge_attribute((vkey, nbr), 'checked')[(nbr, vkey)] is True:
                if mesh.vertex_attribute(nbr, "checked") is True:
                    continue
            same_row_nbrs.append(nbr)
    print(looping_nbrs, same_row_nbrs)


    if looping_nbrs == []:
        if same_row_nbrs == []:
            raise ValueError("this is a dead end")
        vkey, looping_nbr = check_nbr_dir(mesh, same_row_nbrs[0], filter=True)
        return vkey, looping_nbr

    looping_nbr = looping_nbrs[0]

    # HERE CAN BE POTENTIALLY WRONG>>>>>>>>>>>>>
    if len(looping_nbrs) == 1:
        if mesh.vertex_attribute(looping_nbr, "tri") == 1:
            if mesh.is_vertex_on_boundary(looping_nbr) is True:
                return vkey, looping_nbr
            vkey, looping_nbr = check_nbr_dir(mesh, looping_nbr, filter=True)
            return vkey, looping_nbr
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    if len(looping_nbrs) > 1:
        if mesh.vertex_attribute(vkey, "tri") == 0:
            for can in looping_nbrs:
                if mesh.vertex_attribute(can, "row") > mesh.vertex_attribute(looping_nbr, "row"):
                    looping_nbr = can
                elif mesh.vertex_attribute(can, "row") == mesh.vertex_attribute(looping_nbr, "row"):
                    if mesh.vertex_attribute(can, "column") < mesh.vertex_attribute(looping_nbr, "column"):
                        looping_nbr = can

        elif mesh.vertex_attribute(vkey, "tri") == 1:
            for can in looping_nbrs:
                if mesh.vertex_attribute(can, "row") < mesh.vertex_attribute(looping_nbr, "row"):
                    looping_nbr = can
                elif mesh.vertex_attribute(can, "row") == mesh.vertex_attribute(looping_nbr, "row"):
                    if mesh.is_vertex_on_boundary(looping_nbr) is True:
                        looping_nbr = can
                    elif mesh.is_vertex_on_boundary(can) is True:
                        pass
                    else:
                        if mesh.vertex_attribute(can, "column") < mesh.vertex_attribute(looping_nbr, "column"):
                            looping_nbr = can
        else:
            for can in looping_nbrs:
                if mesh.vertex_attribute(can, "row") < mesh.vertex_attribute(looping_nbr, "row"):
                    looping_nbr = can
                elif mesh.vertex_attribute(can, "row") == mesh.vertex_attribute(looping_nbr, "row"):
                    if mesh.vertex_attribute(can, "column") < mesh.vertex_attribute(looping_nbr, "column"):
                        looping_nbr = can

    return vkey, looping_nbr


def course_r_l(mesh, start, filter=True):
    # parameters:
    #   mesh: input mesh
    #   start: the vertex to start
    #   course_nbr: nbr in the course direction
    # output:
    #   pts: list of point coordinates (x, y, z)
    start_, nbr = check_nbr_dir(mesh, start, filter=True)
    print(start_, nbr)

    loop = halfedge_loop_r_l(mesh, (start_, nbr))
    for (u, v) in loop: 
        mesh.edge_attribute((u, v), 'checked')[(u, v)] = True

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
    for (u, v) in loop: 
        mesh.edge_attribute((u, v), 'checked')[(u, v)] = True
    
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

    if start != start_:
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
