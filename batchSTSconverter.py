from PyQt4 import QtGui
import sys
import pyOmicron as pyO
import re
import numpy as np

# Ask for a directory
app=QtGui.QApplication(sys.argv)
path=QtGui.QFileDialog.getExistingDirectory()
# Read the matric file
M=pyO.Matrix(path)

STS={}
for i in M.images: # Scan through all files
  r=re.search(r"--([0-9]+)_([0-9]+).I\(V\)_mtrx",i)
  if r: # if file is a I(V)_mtrx one
    ID=int(r.group(1))
    num=int(r.group(2))
    if ID in STS: STS[ID]+=1 # Store the number of measurements performed for ID
    else: STS[ID]=1
for ID in STS:
    x,y=M.getSTS(ID) # Get the first num curve of the ID
    R=np.column_stack([x,y]) # Result matrix. Is an array where the columns are on the form [x,y1,y2,y3,...] 
    for num in range(1,STS[ID]):
      x,y=M.getSTS(ID,num)
      R=np.column_stack((R,y))
    # Save the data as ascii. Can be easily parsed by gnuplot, R and Matlab
    np.savetxt(str(path+"/STS-%i.dat"%(ID)),R,header="Bias[V] "+" ".join([str(i+1) for i in range(STS[ID])]))
    
