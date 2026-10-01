"""View the simulated geometry over the original one, shaded by the stress.

Reads the results `scripts/simulate.py` wrote to `<folder>/out/`.

Edit the inputs below and run
    python scripts/view_simulation.py
"""
import os

from compas_knit import DATA
from compas_knit.viewer import view_simulation

# MODIFY -----------------------------------------------------------------
folder = os.path.join(DATA, "circular_flat")  # the same as in scripts/simulate.py
name = "circular_flat"

quantity = "von_mises"  # or principal_1, principal_2, T_wale_Nm, T_course_Nm, S11, S22, S12; None: no shading
view = "perspective"  # or top, front, right
show_field = False  # start with the directional field shown, or switch it on with the checkbox
# -------------------------------------------------------------------------

out = os.path.join(folder, "out", name)
stress = out + "_stress.csv" if quantity else None
field = os.path.join(folder, name + "_vertex_directional_field.txt")
view_simulation(os.path.join(folder, name + ".obj"), out + "_deformed.obj", stress, quantity=quantity or "von_mises",
                field=field, show_field=show_field, view=view)
