# Validating the simulation: the flat dome

A flat circular membrane, anchored on its boundary and inflated, is the simplest check of the simulation. Its crown
height is compared with Hencky's analytical solution, for an isotropic membrane, and with an independent finite
element program, CalculiX, for the knit.

![The flat dome inflated, scripts/simulate.py, shaded by the von Mises stress](../.gitbook/assets/flat-dome.png)

## The sample

`data/circular_flat/circular_flat.obj`, the circular flat mesh of the fabsim examples: 399 vertices, 735 triangles,
radius a = 0.5985 m, flat in the xy plane with its normals along +z. The 61 boundary vertices are anchored and the
pressure is p = 1000 Pa. The knitting direction, the wale, is read per vertex from
`circular_flat_vertex_directional_field.txt`. `scripts/simulate.py` runs it and shows the result.

## Hencky's solution

For an isotropic membrane of modulus E (N/m, Young's modulus times thickness) clamped on a circle of radius a, Hencky's
solution of the Föppl–von Kármán membrane equations gives the crown height

```
w0 = C(nu) · a · (p a / E)^(1/3),    C(0.3) = 0.662
```

There is no such closed form for the orthotropic knit, so it is checked against CalculiX.

## CalculiX

[CalculiX](http://www.calculix.de) 2.23, with the same mesh as M3D3 membrane elements, geometric nonlinearity (`NLGEOM`,
which with a linear elastic material is St. Venant–Kirchhoff, the material of `knit_sim`) and a follower pressure. The
knit's stiffness matrix

```
C = 1/(1 - nu²) · [[E_w,             nu √(E_w E_c),  0                    ],
                   [nu √(E_w E_c),   E_c,            0                    ],
                   [0,               0,              ½ √(E_w E_c)(1 - nu) ]]
```

is given as orthotropic engineering constants, E1 = E_w, E2 = E_c, nu12 = nu √(E_w / E_c),
G12 = √(E_w E_c) / (2 (1 + nu)), oriented along the wale. A flat membrane has no stiffness against pressure at the
start, so both programs get the same small pre-tension, a stretch of 1.001, in CalculiX as a thermal contraction.

## Results

Crown height in metres, p = 1000 Pa.

| Material (N/m) | Wale | Hencky | CalculiX | knit_sim | knit_sim before the fix |
|---|---|---|---|---|---|
| isotropic, E 10000, nu 0.3 | — | 0.1550 | 0.1538 | 0.1538 | 0.2263 |
| E_w 10300, E_c 13400, nu 0.58 | x | — | 0.1245 | 0.1245 | 0.1823 |
| E_w 5000, E_c 2500, nu 0.198 | x | — | 0.2268 | 0.2268 | 0.3397 |
| E_w 12500, E_c 5000, nu 0.198 | y | — | 0.1684 | 0.1684 | 0.2489 |

The same 10300 / 13400 material at 1100 and 1200 Pa: 0.1287 and 0.1327 m, in both programs.

`knit_sim` and CalculiX agree to four digits. Hencky's solution is for a perfectly flexible membrane with small slopes,
and is 0.8 % above both; on a finer disc, `scripts/tests/simulate_disc.py`, `knit_sim` is within 0.1 % of it:

| Disc, radius 0.5 m, E 10000 N/m, nu 0.3 | Triangles | Hencky | knit_sim |
|---|---|---|---|
| edge 0.04 m | 1015 | 0.1219 | 0.1220 (+0.06 %) |
| edge 0.02 m | 3929 | 0.1219 | 0.1219 (+0.00 %) |

## The pressure fix

The orthotropic and isotropic StVK elements of fabsim took the work of the pressure on a triangle as
(x0 + x1 + x2) · n / 6, with n = (x0 − x2) × (x1 − x2). That is three times the volume of the tetrahedron the triangle
makes with the origin, x0 · (x1 × x2) / 6, so the pressure acted three times over, and the crown height came out
3^(1/3) ≈ 1.44 times too high, the last column above. The stresses, the reactions and the cable tensions were three
times too high too. `src/cpp_sim/patches/fabsim_pressure_volume.patch` divides by 18 in the energy and the gradient,
and the Hessian likewise, and is applied to fabsim when `knit_sim` is built.

## The current example

`scripts/simulate.py` with E_w 12500, E_c 5000, nu 0.198, the wale along y and the stretch factors 1.1 and 1.1, the
image above: crown height 0.0728 m, von Mises stress 1344 to 1493 N/m. The pre-strain is a rest shape smaller than the
mesh, which a thermal contraction in CalculiX only approximates at large strains, so it is not in the comparison.

## Run it

```
python scripts/simulate.py               # the example, and the viewer
python scripts/tests/simulate_disc.py    # the discs against Hencky, fails if more than 2 % off
```
