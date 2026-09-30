"""Knitting trajectories for the same mesh with the directional field rotated in steps.

Each vertex vector is rotated about the vertex normal. The field is a line field,
so the angles run from 0 up to 180 degrees. For every angle this writes the trajectories to
`<folder>/out/field_rotation/<angle>/`, and a summary, `summary.json`, and a contact sheet,
`field_rotation.png`, with a top view per angle and the spacing, singularities and trajectory
count against the angle.

    python scripts/tests/field_rotation.py
"""
import json
import os
import sys
import tempfile

import numpy as np
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from scipy.spatial import cKDTree

from compas.datastructures import Mesh
from compas_knit import DATA
from compas_knit.stripes import check_trajectories
from compas_knit.stripes import generate_stripes

# MODIFY -----------------------------------------------------------------
folder = os.path.join(DATA, "2part_remesh2")
name = "2part_remesh2"

stitch_height = 2.297
stitch_width = 3.54
step = 5  # degrees
# -------------------------------------------------------------------------

mesh_path = os.path.join(folder, name + ".obj")
field_path = os.path.join(folder, name + "_vertex_directional_field.txt")
out_dir = os.path.join(folder, "out", "field_rotation")
spacing = 2 * stitch_height

mesh = Mesh.from_obj(mesh_path)
xyz = np.array(mesh.vertices_attributes("xyz"))
normals = np.array([mesh.vertex_normal(vertex) for vertex in mesh.vertices()])
field = np.loadtxt(field_path)[:, :3]
tangent = field - (field * normals).sum(axis=1)[:, None] * normals


def rotated_field(angle):
    """The field turned by angle degrees about the vertex normals."""
    a = np.radians(angle)
    return tangent * np.cos(a) + np.cross(normals, tangent) * np.sin(a)


def resample(points, step):
    out = [points[0]]
    for a, b in zip(points[:-1], points[1:]):
        n = max(int(np.ceil(np.linalg.norm(b - a) / step)), 1)
        out += [a + (b - a) * t for t in np.arange(1, n + 1) / n]
    return np.array(out)


def gaps(trajectories):
    """Distance from points along each trajectory to the nearest other trajectory."""
    points = [resample(polyline, spacing / 5) for polyline in trajectories]
    labels = np.concatenate([np.full(len(p), i) for i, p in enumerate(points)])
    points = np.vstack(points)
    distances, indices = cKDTree(points).query(points, k=40)
    d = np.full(len(points), np.inf)
    for k in range(1, 40):
        other = (labels[indices[:, k]] != labels) & np.isinf(d)
        d[other] = distances[other, k]
    return d[np.isfinite(d)]


# the boundary, to tell the trajectories ending at a singularity from those ending at the boundary
boundary = []
for u, v in mesh.edges_on_boundary():
    boundary.append(resample(np.array([xyz[u], xyz[v]]), spacing / 10))
boundary_tree = cKDTree(np.vstack(boundary))

runs = []
for angle in range(0, 180, step):
    run_dir = os.path.join(out_dir, "{:03d}".format(angle))
    os.makedirs(run_dir, exist_ok=True)
    run_field = os.path.join(run_dir, name + "_vertex_directional_field.txt")
    np.savetxt(run_field, rotated_field(angle), fmt="%.9f")

    # the stripes executable prints to the process stdout, so capture that rather than sys.stdout
    with tempfile.TemporaryFile("w+") as log:
        sys.stdout.flush()
        saved = os.dup(1)
        os.dup2(log.fileno(), 1)
        try:
            trajectories = generate_stripes(mesh_path, run_field, stitch_height, stitch_width, out_dir=run_dir, check=False)
        finally:
            sys.stdout.flush()
            os.dup2(saved, 1)
            os.close(saved)
        log.seek(0)
        output = log.read()
    polylines = [np.array([list(point) for point in polyline.points]) for polyline in trajectories]
    ends = np.array([p[0] for p in polylines] + [p[-1] for p in polylines])
    inner = ends[boundary_tree.query(ends)[0] > spacing / 2]
    d = gaps(polylines)
    singularities = [line for line in output.splitlines() if "stripe singularities" in line]
    run = {
        "angle": angle,
        "trajectories": len(polylines),
        "singularities": int(singularities[0].split()[0]) if singularities else None,
        "inner_ends": len(inner),
        "suspect_segments": len(check_trajectories(trajectories, mesh, run_field)),
        "gap_median": float(np.median(d)),
        "gap_p10": float(np.percentile(d, 10)),
        "gap_p90": float(np.percentile(d, 90)),
    }
    runs.append(run)
    print("{angle:3d} deg  {trajectories:4d} trajectories  {singularities:4d} singularities  "
          "gap {gap_median:.3f} ({gap_p10:.2f}-{gap_p90:.2f})  {suspect_segments} suspect segments".format(**run))
    run["polylines"] = polylines
    run["inner"] = inner

with open(os.path.join(out_dir, "summary.json"), "w") as f:
    json.dump([{k: v for k, v in run.items() if k not in ("polylines", "inner")} for run in runs], f, indent=1)

# contact sheet --------------------------------------------------------------

INK = (38, 38, 38)
MUTED = (115, 115, 115)
GRID = (225, 225, 225)
LINE = (31, 78, 121)  # one hue for the trajectories and the chart lines
END = (200, 40, 40)
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
except OSError:
    font = small = ImageFont.load_default()

lo = xyz.min(axis=0)
hi = xyz.max(axis=0)
tile, pad, head = 600, 20, 60
columns = 6
scale = (tile - 2 * pad) / max(hi[0] - lo[0], hi[1] - lo[1])


def to_tile(points, ox, oy):
    x = (points[:, 0] - (lo[0] + hi[0]) / 2) * scale + tile / 2 + ox
    y = -(points[:, 1] - (lo[1] + hi[1]) / 2) * scale + tile / 2 + oy + head
    return list(zip(x, y))


rows = -(-len(runs) // columns)
chart_h = 420
sheet = Image.new("RGB", (columns * tile, rows * (tile + head) + chart_h + 80), "white")
draw = ImageDraw.Draw(sheet)

for n, run in enumerate(runs):
    ox, oy = (n % columns) * tile, (n // columns) * (tile + head)
    for segment in boundary:
        draw.line(to_tile(segment, ox, oy), fill=(170, 170, 170), width=2)
    for polyline in run["polylines"]:
        draw.line(to_tile(polyline, ox, oy), fill=LINE, width=1)
    for x, y in to_tile(run["inner"], ox, oy) if len(run["inner"]) else []:
        draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=END)
    draw.text((ox + pad, oy + 8), "{} deg".format(run["angle"]), fill=INK, font=font)
    draw.text((ox + pad + 110, oy + 12), "{} traj  {} sing  gap {:.2f}".format(
        run["trajectories"], run["singularities"], run["gap_median"]), fill=MUTED, font=small)


def chart(x0, width, title, values, target=None):
    """A small line chart of values against the angle, one measure, one axis."""
    y0, h = rows * (tile + head) + 60, chart_h - 60
    left, right, top, bottom = x0 + 70, x0 + width - 30, y0 + 40, y0 + h
    vmin, vmax = min(values + ([target] if target else [])), max(values + ([target] if target else []))
    margin = (vmax - vmin) * 0.15 or 1
    vmin, vmax = vmin - margin, vmax + margin
    X = lambda a: left + (right - left) * a / 180
    Y = lambda v: bottom - (bottom - top) * (v - vmin) / (vmax - vmin)
    draw.text((x0 + 20, y0), title, fill=INK, font=font)
    for v in np.linspace(vmin, vmax, 5):
        draw.line([(left, Y(v)), (right, Y(v))], fill=GRID, width=1)
        draw.text((x0 + 10, Y(v) - 10), "{:.2f}".format(v) if vmax - vmin < 10 else "{:.0f}".format(v), fill=MUTED, font=small)
    for a in range(0, 181, 45):
        draw.text((X(a) - 12, bottom + 8), str(a), fill=MUTED, font=small)
    if target:
        draw.line([(left, Y(target)), (right, Y(target))], fill=MUTED, width=2)
        draw.text((right - 170, Y(target) - 26), "2 x stitch height", fill=MUTED, font=small)
    angles = [run["angle"] for run in runs]
    draw.line([(X(a), Y(v)) for a, v in zip(angles, values)], fill=LINE, width=2)
    for a, v in zip(angles, values):
        draw.ellipse([X(a) - 4, Y(v) - 4, X(a) + 4, Y(v) + 4], fill=LINE)


third = sheet.width // 3
chart(0, third, "median gap between trajectories", [run["gap_median"] for run in runs], target=spacing)
chart(third, third, "stripe singularities", [run["singularities"] for run in runs])
chart(2 * third, third, "trajectories", [run["trajectories"] for run in runs])
draw.text((20, sheet.height - 36), "field rotation (deg) on the x axis.  red dots: trajectories ending at a singularity",
          fill=MUTED, font=small)

sheet_path = os.path.join(out_dir, "field_rotation.png")
sheet.save(sheet_path)
print("Wrote", sheet_path)
