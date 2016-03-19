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
import sys
import matplotlib.gridspec as gridspec

FontSize=8

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
		self.canvas.mpl_connect('pick_event', self.on_pick)
		self.mpl_toolbar = NavigationToolbar(self.canvas, self.ui.widget)
		
		gs=gridspec.GridSpec(2, 2)
		sp1=gs.new_subplotspec((0,0))
		sp2=gs.new_subplotspec((1,0))
		sp3=gs.new_subplotspec((0,1),2)
		self.ax1 = self.fig.add_subplot(sp1)
		self.ax2  = self.fig.add_subplot(sp2)
		self.ax3  = self.fig.add_subplot(sp3)
		self.ax1b = self.ax1.twinx()
		self.ax3b = self.ax3.twinx()

		# Ask for the directory containing the matrix files
		if len(sys.argv)<2:
			self.path=QFileDialog.getExistingDirectory()
		else:
			self.path=sys.argv[1]
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
		self.ax1.clear()
		self.ax1b.clear()
		self.ax2.clear()
		self.ax3.clear()
		self.ax3b.clear()
		self.ax1.hold(True)
		self.ax1.set_xlabel("Bias [V]",fontsize=FontSize)
		self.ax2.set_xlabel("Bias [V]",fontsize=FontSize)
		self.ax1.set_ylabel("Current [pA]",fontsize=FontSize)
		self.ax1b.set_ylabel("dI/dV [pA/V]",fontsize=FontSize)
		self.ax2.set_ylabel(r'$\frac{dI/dV}{\overline{I/V}}$',fontsize=FontSize)
		self.ax3.set_xlabel("Bias [V]",fontsize=FontSize)
		self.ax3.set_ylabel("I/V [$\mu$A/V]",fontsize=FontSize)
		self.ax3b.yaxis.label.set_color("green")
		self.ax3b.tick_params(axis='y',colors="green")
		for i in range(self.STS[ID]):
			if self.ui.listWidget.isItemSelected(self.ui.listWidget.item(i)):
				V,I=self.M.getSTS(ID,i+1)
				Vstep=(max(V)-min(V))/len(V)
				Vhr=(max(V)-min(V))*0.5 # half-range
				self.ax1.plot(V,I*1e-6,color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]))
				if ID in self.hasDIDV:
					V,dI=self.M.getDIDV(ID,i+1)
					self.ax1b.plot(V,dI*1e-6,'--',color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]))
					DV=self.ui.DV.value()
					DVstep=Vstep*np.ceil(DV/Vstep) # Round DV to match a multiple of Vstep (round up)
					skip=DVstep/Vstep
					nVb=np.linspace(min(V)-DVstep,min(V),skip,endpoint=False)
					nVe=np.linspace(max(V)+Vstep,max(V)+DVstep,skip)
					nV=np.concatenate((nVb,V,nVe))
					W=np.exp(-np.abs(nV)/DV)/(2*DV)
					IV=I/V
					IV[V<1e-9]=0
					IV=np.concatenate(([IV[0]]*skip,IV,[IV[-1]]*skip))
					BIV=np.convolve(IV,W,mode='same')
					BIV=BIV[skip:-skip]
					self.ax3.plot(nV,1e-12*IV,'b',label="I/V")
					self.ax3.plot(V,1e-12*BIV,'r',label="$\overline{I/V}$")
					self.ax3b.plot(nV,W,'g',label="conv. func.")
					self.ax2.plot(V,dI/BIV,'r')
					self.ax3.legend(prop={'size':6})
		for x in [self.ax1,self.ax1b,self.ax2,self.ax3,self.ax3b]:
			x.tick_params(axis='both', labelsize=FontSize)
		self.canvas.draw()

app = QApplication(sys.argv)
S=STSviewer()
S.show()
sys.exit(app.exec_())
