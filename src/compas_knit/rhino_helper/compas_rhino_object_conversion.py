__author__ = "duchaoyu"

import rhinoscriptsyntax as rs
import scriptcontext as sc
import Rhino.Geometry as rg
from compas.datastructures import Mesh
from compas.geometry import centroid_points
from compas.utilities import pairwise

def point_to_R(point):
    x= point[0]
    y = point[1]
    z = point[2]
    return rg.Point3d(x, y, z)

def vector_to_R(vector):
    x = vector[0]
    y = vector[1]
    z = vector[2]
    return rg.Vector3d(x, y, z)

def line_to_R(line):
    st = line[0]
    ed = line[1]
    st_pt = rg.Point3d(st[0], st[1], st[2])
    ed_pt = rg.Point3d(ed[0], ed[1], ed[2])
    return rg.Line(st_pt, ed_pt)

def polygon_to_R(polygon):
    if isinstance(polygon, list):
        points = polygon
    else:
        points = polygon.points
    R_points = []
    for pt in points:
        R_pt = rg.Point3d(pt[0], pt[1], pt[2])
        R_points.append(R_pt)
    R_points.append(R_points[0])
    return rg.Polyline(R_points)

def polyline_to_R(polyline):
    if isinstance(polyline, list):
        points = polyline
    else:
        points = polyline.points
    R_points = []
    for pt in points:
        R_pt = rg.Point3d(pt[0], pt[1], pt[2])
        R_points.append(R_pt)
    R_points.append(R_points[0])
    return rg.Polyline(R_points)

def circle_to_R(circle):
    p = circle.plane
    r = circle.radius
    origin = rg.Point3d(p.point[0], p.point[1], p.point[2])
    normal = rg.Vector3d(p.normal[0], p.normal[1], p.normal[2])
    return rg.Circle(rg.Plane(origin, normal), r)

def plane_to_R(plane):
    pt = plane[0]
    normal = plane[1]
    return rg.Plane(rg.Point3d(*pt), rg.Vector3d(*normal))

def mesh_to_R(mesh):
    R_mesh = rg.Mesh()
    key_count_dict = {}

    count = 0
    for vkey in mesh.vertices():
        x, y, z = mesh.vertex_coordinates(vkey)
        R_mesh.Vertices.Add(rg.Point3d(x, y, z))
        key_count_dict[vkey] = count
        count += 1
       
    count_key_dict = {v: k for k, v in key_count_dict.items()}
    for fkey in mesh.faces():
        f_vkeys = mesh.face_vertices(fkey)
        f_vkeys = [key_count_dict[key] for key in f_vkeys]
        if len(f_vkeys) <= 4:
            R_mesh.Faces.AddFace(*f_vkeys)
        else:
            centroid = centroid_points([mesh.vertex_coordinates(count_key_dict[vkey]) for vkey in f_vkeys])
            c = R_mesh.Vertices.Add(rg.Point3d(*centroid))
            facets = []
            for i, j in pairwise(f_vkeys + f_vkeys[:1]):
                facets.append(R_mesh.Faces.AddFace(i, j, c))
            ngon = rg.MeshNgon.Create(f_vkeys, facets)
            R_mesh.Ngons.AddNgon(ngon)
    R_mesh.Normals.ComputeNormals()
    R_mesh.Compact()
    return R_mesh

from compas.utilities import geometric_key
from compas.datastructures import Mesh

def R_mesh_to_C(R_mesh):

    gkey_dict = {}
    R_vkey_C_vkey_dict = {}
    gkey_index_dict = {}
    vertices = []
    count = 0

    for i, vertex in enumerate(R_mesh.Vertices):
        gkey = geometric_key([float(vertex.X), float(vertex.Y), float(vertex.Z)])
        if gkey not in gkey_dict.keys():
            gkey_dict[gkey] = count
            R_vkey_C_vkey_dict[i] = count
            count += 1
            
        else:
            index = gkey_dict[gkey]
            R_vkey_C_vkey_dict[i] = index

    vertices = []
    
    index_gkey_dict = dict((v,k) for k,v in gkey_dict.iteritems())
    
    for i, key in enumerate(index_gkey_dict.keys()):
        str_list = index_gkey_dict[i]
        split = str_list.split(",")
        vertices.append([round(float(x),2) for x in split])
        
    faces = []
    
    for ngon in R_mesh.GetNgonAndFacesEnumerable():
        face = list(ngon.BoundaryVertexIndexList())
        c_face = []
        for v_index in face:
            c_face.append(R_vkey_C_vkey_dict[v_index])
        faces.append(c_face)

    C_mesh = Mesh.from_vertices_and_faces(vertices, faces)
    return C_mesh
        
        

sc.sticky['polygon_to_R'] = polygon_to_R
sc.sticky['polyline_to_R'] = polyline_to_R
sc.sticky['circle_to_R'] = circle_to_R
sc.sticky['point_to_R'] = point_to_R
sc.sticky['vector_to_R'] = vector_to_R
sc.sticky['line_to_R'] = line_to_R
sc.sticky['plane_to_R'] = plane_to_R
sc.sticky['mesh_to_R'] = mesh_to_R
sc.sticky['R_mesh_to_C'] = R_mesh_to_C
