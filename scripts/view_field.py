"""View the input mesh and its directional field, from the top.

Edit the inputs below and run
    python scripts/view_field.py
"""
import os

from compas_knit.viewer import view_field

# MODIFY -----------------------------------------------------------------
folder = "/Users/duch/Documents/PhD/knit/2024_prototypes/2part/anisotropic"
name = "2part_remesh2"
# -------------------------------------------------------------------------

mesh_path = os.path.join(folder, name + ".obj")
field_path = os.path.join(folder, name + "_vertex_directional_field.txt")

view_field(mesh_path, field_path)
