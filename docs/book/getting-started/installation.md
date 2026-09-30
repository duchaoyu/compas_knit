# Installation

## Python package

```bash
git clone git@github.com:duchaoyu/compas_knit.git
cd compas_knit
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

`requirements.txt` installs COMPAS 2, numpy, scipy, pillow and compas\_viewer.

## The `stripes` executable

The trajectories are computed by a small C++ program, built once with CMake.
CMake downloads libigl, polyscope and geometry-central.

```bash
cmake -S src/cpp_stripes -B src/cpp_stripes/build
cmake --build src/cpp_stripes/build -j 8
```

Python looks for it at `src/cpp_stripes/build/stripes`.
To use a build elsewhere, set `COMPAS_KNIT_STRIPES` to its path.

## Rhino / Grasshopper

<!-- TODO: installing in Rhino, cpptoknitting.gh -->

## Check the installation

```bash
python -c "import compas_knit.stripes, compas_knit.viewer; print('ok')"
src/cpp_stripes/build/stripes --help
```
