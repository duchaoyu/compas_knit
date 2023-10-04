import os

# this is the file from cpp
# it contains xyz, edge pairs, and which isoline it belongs to 
# file = os.path.abspath("/Users/duch/Documents/Github/compas_knit/src/cpp_libigl/build/temp/output.txt")
file = os.path.abspath("/Users/duch/Documents/PhD/knit/benchmarks/output.txt")


with open(file, "r") as i_file:
    # read xyzs 
    line = i_file.readline().strip()
    pts = []

    while line:
        if not line:
            break
        xyz = line.split()
        pts.append(xyz)
        line = i_file.readline().strip()
        

    # read edges
    line = i_file.readline().strip()
    edges = []
    while line:
        if not line:
            break
        uv = line.split()
        edges.append(uv)

        line = i_file.readline().strip()
        
    # read distances
    line = i_file.readline().strip()
    dis = []
    while line:
        if not line:
            break
        dis.append(line)
        
        line = i_file.readline().strip()
