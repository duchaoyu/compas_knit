__author__ = "duch"

import System.Drawing as sd
import os

x_set = set()
y_set = set()

for pt in pts: # all points in the bitmap
    x = round(pt.X*100, 0)
    y = round(pt.Y*100, 0)
    
    x_set.add(x)
    y_set.add(y)

x_list = list(x_set)
x_list.sort()
y_list = list(y_set)
y_list.sort()

rows = len(x_list)
columns = len(y_list)

dict_x = {}
dict_y = {}

for i, x in enumerate(x_list):
    dict_x[int(x)] = i

for i, y in enumerate(y_list):
    dict_y[int(y)] = i


# # convert the dictory to nested loop 
# # if the code is split in two python components
# dict_x = list(dict_x.items())
# dict_y = list(dict_y.items())

# # turn the nested list back to dictionary
# # helper function for grasshopper 
# dict_x = {key:item for (key, item) in dict_x}
# dict_y = {key:item for (key, item) in dict_y}

directory = "/Users/duch/Desktop"
output_path = os.path.join(directory, 'knit.bmp')

# initiate the size of the bitmap
bm = sd.Bitmap(rows, columns)

# color the bitmap to all White
for i in range(columns):
    for j in range(rows):
        bm.SetPixel(j,i,sd.Color.White)

# black
for pt in c1:
    x = round(pt.X*100, 0)
    y = round(pt.Y*100, 0)
    index_i = dict_x[int(x)]
    index_j = dict_y[int(y)]
    
    bm.SetPixel(index_i,index_j,sd.Color.Black)
    
# blue
for pt in c2:
    x = round(pt.X*100, 0)
    y = round(pt.Y*100, 0)
    index_i = dict_x[int(x)]
    index_j = dict_y[int(y)]
    
    bm.SetPixel(index_i,index_j,sd.Color.Blue)

# green
for pt in c3:
    x = round(pt.X*100, 0)
    y = round(pt.Y*100, 0)
    index_i = dict_x[int(x)]
    index_j = dict_y[int(y)]
    
    bm.SetPixel(index_i,index_j,sd.Color.Green)


# red
for pt in c4:
    x = round(pt.X*100, 0)
    y = round(pt.Y*100, 0)
    index_i = dict_x[int(x)]
    index_j = dict_y[int(y)]
    
    bm.SetPixel(index_i,index_j,sd.Color.Red)


# yellow
for pt in c5:
    x = round(pt.X*100, 0)
    y = round(pt.Y*100, 0)
    index_i = dict_x[int(x)]
    index_j = dict_y[int(y)]
    
    bm.SetPixel(index_i,index_j,sd.Color.Yellow)

bm.Save(output_path, sd.Imaging.ImageFormat.Bmp)   
  