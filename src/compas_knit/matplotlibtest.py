import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
    
path = "/Users/duch/Downloads/Tensile_Test_10kN8.txt"

data = pd.read_csv(path, sep=";", skipinitialspace=True)
print(data.head())
print(data.tail())
print(data.keys())

# make data
strength =  data.iloc[:,1]
strain =  data.iloc[:,3]

# print(data['Time'] ==  data.iloc[:,0])

# plot
fig, ax = plt.subplots()
ax.plot(strain, strength)
ax.set_xlabel("strain")
ax.set_ylabel("strength")
plt.show()