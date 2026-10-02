"""A window for the simulation: change the stretch factors, the material and the loads, run it, export its settings.

Shows the mesh. *Run simulation* runs knit_sim with the parameters in the side panel, the boundary fixed, under the
concrete and the pressure, and shows the knit under them, shaded by the von Mises stress, light to dark, over the mesh as
it was; the status bar gives the displacements, the stresses, and how many faces are in compression. *Export settings*
writes the parameters of the last run, and what it gave, to `<folder>/<name>_settings.json`, from which
`scripts/fab/5_pattern_from_settings.py` makes the knitting pattern of that knit.

Edit the inputs below and run
    python scripts/sim/sim_window.py
"""
import os

from compas_knit import DATA
from compas_knit.app import sim_window

# MODIFY -----------------------------------------------------------------
folder = os.path.join(DATA, "pringle")  # the mesh <name>.obj and its field <name>_vertex_directional_field.txt
name = "pringle"
# -------------------------------------------------------------------------

sim_window(folder, name)
