from PyQt4 import QtGui
import sys
import pyOmicron as pyO
import re
import numpy as np

app=QtGui.QApplication(sys.argv)
path=QtGui.QFileDialog.getExistingDirectory()
#path=r"C:\Users\scholi\Desktop\15-Oct-2015"
del app
del QtGui
M=pyO.Matrix(path)

STS={}
for i in M.images:
  r=re.search(r"--([0-9]+)_([0-9]+).I\(V\)_mtrx",i)
  if r:
    ID=int(r.group(1))
    num=int(r.group(2))
    if ID in STS: STS[ID]+=1
    else: STS[ID]=1
for ID in STS:
    x,y=M.getSTS(ID)
    R=np.column_stack([x,y])
    for num in range(1,STS[ID]):
      x,y=M.getSTS(ID,num)
      R=np.column_stack((R,y))
    np.savetxt(str(path+"/STS-%i.dat"%(ID)),R,header="Bias[V] "+" ".join([str(i+1) for i in range(STS[ID])]))
    
