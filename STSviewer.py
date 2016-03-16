#!/usr/bin/python

from PyQt4.QtGui import QMainWindow, QApplication, QFileDialog
from PyQt4 import QtGui, QtCore
from GUI_STSviewer import Ui_MainWindow
import sys
import pyOmicron as pyO
import re
import matplotlib as mpl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.mlab as mlab
import numpy as np

class STSviewer(QMainWindow):
	def on_pick(self):
		pass
	def __init__(self):
		QMainWindow.__init__(self)
		# Set up the user interface from Designer.
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)

		self.dpi = 100
				
		self.fig = Figure((9.0,6.0), dpi=self.dpi)
		self.canvas = FigureCanvas(self.fig)
		self.canvas.setParent(self.ui.widget)
		self.axes = self.fig.add_subplot(211)
		self.twin = self.axes.twinx()
		self.ax2  = self.fig.add_subplot(212)
		self.canvas.mpl_connect('pick_event', self.on_pick)
		self.mpl_toolbar = NavigationToolbar(self.canvas, self.ui.widget)

		# Ask for the directory containing the matrix files
		self.path=QFileDialog.getExistingDirectory()
		self.M=pyO.Matrix(self.path)
		val=200 # value used for the colors
		# colors used for the plot lines
		self.colors=[(0,0,val),(0,val,0),(val,0,0),(val,val,0),(val,0,val),(0,val,val)]
		
		# SIGNALS -> SLOTS
		self.ui.comboBox.currentIndexChanged.connect(self.updateSTSid)
		self.ui.listWidget.itemSelectionChanged.connect(self.plotUpdate)
		self.ui.DV.valueChanged.connect(self.plotUpdate)
		self.populateUI()
		
	def populateUI(self):
		self.ui.listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
		self.STS={}
		self.hasDIDV=[]
		for i in self.M.images:
			r=re.search(r"--([0-9]+)_([0-9]+).I\(V\)_mtrx",i)
			if r:
				j=int(r.group(1))
				if j in self.STS: self.STS[j]+=1
				else: self.STS[j]=1
				if i[:-9]+'Aux2(V)_mtrx' in self.M.images: self.hasDIDV.append(j)
		for i in self.STS:
			self.ui.comboBox.addItem(str(i))

	def updateSTSid(self): # If and ID is chosen, the listWidget will be populated with the correct num and selected
		self.ui.listWidget.clear()
		ID=int(self.ui.comboBox.currentText())
		for i in range(self.STS[ID]):
			item = QtGui.QListWidgetItem()
			item.setText(str(i+1)+" -----")
			item.setTextColor(QtGui.QColor(*self.colors[i%len(self.colors)]))
			self.ui.listWidget.addItem( item )
			item.setSelected(True)
			
		self.plotUpdate()
	def plotUpdate(self):
		# plot the selected curves
		ID=int(self.ui.comboBox.currentText())
		self.axes.clear()
		self.twin.clear()
		self.ax2.clear()
		self.axes.hold(True)
		self.axes.set_xlabel("Bias [V]")
		self.ax2.set_xlabel("Bias [V]")
		self.axes.set_ylabel("Current [pA]")
		self.twin.set_ylabel("dI/dV [pA/V]")
		self.ax2.set_ylabel(r'$\frac{dI/dV}{\overline{I/V}}$')
		for i in range(self.STS[ID]):
			if self.ui.listWidget.isItemSelected(self.ui.listWidget.item(i)):
				V,I=self.M.getSTS(ID,i+1)
				self.axes.plot(V,I*1e-6,color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]))
				if ID in self.hasDIDV:
					V,dI=self.M.getDIDV(ID,i+1)
					self.twin.plot(V,dI*1e-6,'--',color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]))
					DV=self.ui.DV.value()
					BIV=np.convolve(I/V,np.exp(-np.abs(V)/DV)/(2*DV),mode='same')
					self.ax2.plot(V,dI/BIV,'r')
			
		self.canvas.draw()

app = QApplication(sys.argv)
S=STSviewer()
S.show()
sys.exit(app.exec_())
