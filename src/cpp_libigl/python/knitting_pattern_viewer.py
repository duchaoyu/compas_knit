from compas.datastructures import Mesh
from compas_view2.app import App
from compas_view2.shapes import Text
from compas.geometry import Polyline, Sphere
from compas_view2.objects import Collection
import os
from PIL import Image
from pattern_functions_edge import course_r_l, course_l_r

# import
path = os.path.abspath("/Users/duch/Documents/Github/compas_knit/src/cpp_libigl/build/temp/mesh.json")
mesh = Mesh.from_json(path)
# EXPLANATION
# the mesh has the following vertex attributes:
# the row tells which which isoline the vertex belongs to
# the column tells the location of the vertex in the isolien
# the tri tells it's the start or end of the triangle and its relative location to the isoline

# this part is for better visualisation of the viewer... ----------
scale = 2
for vkey in mesh.vertices():
    xyz = mesh.vertex_coordinates(vkey)
    mesh.vertex_attribute(vkey, "x", xyz[0]*scale)
    mesh.vertex_attribute(vkey, "y", xyz[1]*scale)
    mesh.vertex_attribute(vkey, "z", xyz[2]*scale)
# -----------------------------------------------------------------

mesh.update_default_vertex_attributes({"checked": False})
mesh.update_default_edge_attributes({"checked": {}})
for (u, v) in mesh.edges():
    mesh.edge_attribute((u, v), "checked", {(u, v): False, (v, u): False})

# # eliminate the edges on the boundary
# for bdr in mesh.edges_on_boundaries():
#     for (u, v) in bdr:
#         if mesh.halfedge_face(u, v) is None:
#             mesh.edge_attribute((u, v), 'checked')[(u, v)] = True
#         elif mesh.halfedge_face(v, u) is None:
#             mesh.edge_attribute((u, v), 'checked')[(v, u)] = True


# for bitmap
min_col = 0
max_col = 0
min_row = 0
max_row = 0
bitmap_dict = {}
location = [0, 0]

# starting vertex
start = 844
end = 1016
count = 0  # DEBUGGING
polyline_points = []  # visualise the knitting sequence

show = True
# show = False
while True and count < 98:
    # try:
    count += 1
    print("count", count)
    # right to left
    # ---------------
    odd_vkeys, odd_pts = course_r_l(mesh, start, filter=True)
    polyline_points.extend(odd_pts)
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

    even_vkeys, even_pts = course_l_r(mesh, odd_vkeys[-1], filter=True)

    # check ending 
    if end in even_vkeys:
        index = even_vkeys.index(end)
        even_vkeys = even_vkeys[:index+1]
        even_pts = even_pts[:index+1]
        polyline_points.extend(even_pts)
        # bitmap
        for _ in range(len(even_pts)):
            bitmap_dict[tuple(location)] = 1
            location[0] += 1
        if location[0] >= max_col:
            max_col = location[0]
        max_row += 1
        location[0] -= 1
        location[1] += 1
        break

    polyline_points.extend(even_pts)
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

    start = even_vkeys[-1]

    # print("start", start)
    # except:
    #     pass

polyline = Polyline(polyline_points)


# bitmap
directory = "/Users/duch/Documents/Github/compas_knit/src/cpp_libigl/build/temp/"
output_path = os.path.join(directory, 'knit.bmp')

# initiate the size of the bitmap
rows = max_row-min_row
columns = max_col-min_col
print(rows, columns)

image = Image.new("RGB", (columns + 1, rows + 1), "white")
# bm = sd.Bitmap(columns + 1, rows + 1)
# # color the bitmap to all White
# for i in range(columns+1):
#     for j in range(rows+1):
#         bm.SetPixel(i, j, sd.Color.White)

# black
pixels = image.load()
for (loc, val) in bitmap_dict.items():
    pixels[loc[0] + columns, loc[1]] = (0, 0, 0)
    # bm.SetPixel(loc[0] + columns, loc[1], sd.Color.Black)

image.save(output_path)

# bm.Save(output_path, sd.Imaging.ImageFormat.Bmp)

if show:
    vkeys = mesh.vertices_where({"checked": True})
    spheres = []
    for vkey in vkeys:
        xyz = mesh.vertex_coordinates(vkey)
        spheres.append(Sphere(xyz, 0.01))

    viewer = App()
    viewer.add(mesh, show_faces=False, show_lines=True)
    # viewer.add(polyline, linecolor=(0.7, 0., 0.7))
    # viewer.add(Collection(spheres))
    # # text objects
    # maxkey = len(list(mesh.vertices()))
    # for vkey in mesh.vertices():
    #     txt = Text(str(vkey), mesh.vertex_coordinates(vkey), height=50)
    #     viewer.add(txt, color=(vkey/maxkey, vkey/maxkey, 0))

    viewer.show()
