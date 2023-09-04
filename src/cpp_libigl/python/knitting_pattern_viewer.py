from compas.datastructures import Mesh

from compas_view2.app import App
from compas_view2.shapes import Text
import os

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

min_col = 0
max_col = 0
min_row = 0
max_row = 0
bitmap_dict = {}



viewer = App()
viewer.add(mesh, show_faces=False)

# text objects 
maxkey = len(list(mesh.vertices()))

for vkey in mesh.vertices():
    txt = Text(str(vkey), mesh.vertex_coordinates(vkey), height=50)
    viewer.add(txt, color=(vkey/maxkey, vkey/maxkey, 0))

viewer.show()