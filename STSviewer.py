#!/usr/bin/python

from PyQt4.QtGui import QMainWindow, QApplication, QFileDialog
from PyQt4 import QtGui, QtCore
from GUI_STSviewer import Ui_MainWindow
import sys
import pyOmicron as pyO
import re
import numpy as np
import sys
import matplotlib.gridspec as gridspec
from STS import STS
import time

FontSize=8

class STSviewer(QMainWindow):
	def on_pick(self):
		pass
	def __init__(self):
		QMainWindow.__init__(self)
		# Set up the user interface from Designer.
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)

		self.canvas=self.ui.mpl.canvas
		self.fig = self.ui.mpl.canvas.fig
		self.canvas.mpl_connect('pick_event', self.on_pick)
		
		gs=gridspec.GridSpec(2, 2)
		sp1=gs.new_subplotspec((0,0))
		sp2=gs.new_subplotspec((1,0))
		sp3=gs.new_subplotspec((0,1),2)
		self.ax1 = self.fig.add_subplot(sp1)
		self.ax2  = self.fig.add_subplot(sp2)
		self.ax3  = self.fig.add_subplot(sp3)
		self.ax1b = self.ax1.twinx()
		self.ax3b = self.ax3.twinx()
		self.fig.tight_layout()

		# Ask for the directory containing the matrix files
		if len(sys.argv)<2:
			self.path=QFileDialog.getExistingDirectory()
		else:
			self.path=sys.argv[1]
		self.M=pyO.Matrix(self.path)
		val=200 # value used for the colors
		# colors used for the plot lines
		self.colors=[(0,0,val),(0,val,0),(val,0,0),(val,val,0),(val,0,val),(0,val,val)]
		
	
		self.populateUI()

		if len(sys.argv)>2:
			ID=sys.argv[2]
			self.ui.comboBox.setCurrentIndex(self.ui.comboBox.findText(ID))

		# SIGNALS -> SLOTS
		self.ui.comboBox.currentIndexChanged.connect(self.updateSTSid)
		self.ui.listWidget.itemChanged.connect(self.plotUpdate)
		self.ui.DV.valueChanged.connect(self.plotUpdate)
		self.ui.pushButton.clicked.connect(self.InfoShowHideToggle)
		self.InfoShowHideToggle('Hide')
		
		self.updateSTSid()
		self.plotUpdate()

	def InfoShowHideToggle(self,action='Toggle'):
		if action=='Hide' or self.ui.treeWidget.isVisible():
			self.ui.treeWidget.hide()
			self.ui.pushButton.setText("<<")
		else:
			self.ui.treeWidget.show()
			self.ui.pushButton.setText(">>")

	def populateUI(self):
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
		self.ui.listWidget.itemChanged.disconnect()
		self.ui.listWidget.clear()
		ID=int(self.ui.comboBox.currentText())
		for i in range(self.STS[ID]):
			item = QtGui.QListWidgetItem()
			item.setText(str(i+1)+" -----")
			item.setTextColor(QtGui.QColor(*self.colors[i%len(self.colors)]))
			item.setFlags(item.flags()|QtCore.Qt.ItemIsUserCheckable)
			self.ui.listWidget.addItem( item )
			item.setCheckState(QtCore.Qt.Checked)
		self.ui.listWidget.itemChanged.connect(self.plotUpdate)
		self.plotUpdate()

	def updateModel(self, value, item=None):
		if item==None:
			self.ui.treeWidget.clear()
			item=self.ui.treeWidget.invisibleRootItem()
		if type(value) is dict:
			if 'value' in value and 'unit' in value:
				child=QtGui.QTreeWidgetItem()	
				if value['unit']=='--':
					child.setText(0,unicode(value['value']))
				else:
					child.setText(0,unicode(value['value'])+" "+unicode(value['unit']))
				item.addChild(child)
			else:
				for key, val in sorted(value.iteritems()):
					child=QtGui.QTreeWidgetItem()
					child.setText(0,unicode(key))
					item.addChild(child)
					self.updateModel(val, child)
		elif type(value) is list:
			for val in value:
				child=QtGui.QTreeWidgetItem()
				item.addChild(child)
				if type(val) is dict:
					child.setText(0, '[dict]')
					self.updateModel(val,child)
				elif type(val) is list:
					child.setText(0, '[list]')
					self.updateModel(val,child)
				else:
					child.setText(0, unicode(val))
				child.setExpanded(True)
		else:
			child=QtGui.QTreeWidgetItem()
			child.setText(0,unicode(value))
			item.addChild(child)

	def plotUpdate(self):
		start=time.clock()
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
		paramsShowed=False
		for i in range(self.STS[ID]):
			if self.ui.listWidget.item(i).checkState()==QtCore.Qt.Checked:
				if not paramsShowed:
					paramsShowed=True
					temp,p=self.M.getSTSparams(ID,i+1)
					self.updateModel(p)
				V,I,IM=self.M.getSTS(ID,i+1,params=True)
				NPTS=int(IM['Spectroscopy']['Device_1_Points']['value']) # Number of points in the V range
				Vstep=(max(V)-min(V))/float(NPTS)
				sV=np.linspace(min(V),max(V),NPTS) # Voltage values in increading order
				if len(I)>NPTS: # Forward & Backward scan
					if V[1]<V[0]: # Start with Downward scan
						IUp=I[NPTS:]
						IDown=I[NPTS-1::-1]
					else:
						IUp=I[:NPTS]
						IDown=I[-1:NPTS-1:-1]
					self.ax1.plot(sV,IUp*1e-6,
						color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]),
						label="I%i (->)"%(i))
					self.ax1.plot(sV,IDown*1e-6,'--',
						color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]),
						label="I%i (<-)"%(i))
				else:
					self.ax1.plot(V,I*1e-6,
						color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]),
						label="I%i"%(i))
					
				DV=self.ui.DV.value()
				if ID in self.hasDIDV:
					V2,dI=self.M.getDIDV(ID,i+1)
					if len(I)>NPTS: # Forward & Backward scan
						if V[1]<V[0]: # Start with Downward scan
							dIUp=dI[NPTS:]
							dIDown=dI[NPTS-1::-1]
						else:
							dIUp=dI[:NPTS]
							dIDown=dI[-1:NPTS-1:-1]
						Is=[IUp,IDown]
						dIs=[dIUp,dIDown]
					else:
						Is=[I]
						dIs=[dI]

					for ud in range(len(Is)):
						self.ax1b.plot(sV,dIs[ud]*1e-6,[':','-.'][ud],
							color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]),
							label="dI%i (%s)"%(i,['->','<-'][ud]))
						delta=NPTS-len(Is[ud])
						if delta>0:
							if V[1]>V[0]: # problem on the downscan
								sV=sV[delta:]
							else:
								sV=sV[:-delta]
						S=STS(sV,Is[ud],dIs[ud],DV)
						IV=S.getIV()
						BIV=S.getBIV()
						W=S.getW()
						nV=S.getnV()
						self.ax3.plot(nV,1e-12*IV,['b','--b'][ud],
							label="I/V (%s)"%(["->","<-"][ud]))
						self.ax3.plot(sV,1e-12*BIV,['r','--r'][ud],
							label="$\overline{I/V}$ (%s)"%(["->","<-"][ud]))
						if ud==0: self.ax3b.plot(nV,W,'g',label="conv. func.")
						self.ax2.plot(sV,dIs[ud]/BIV,['-','--'][ud],
							color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]),
							label="(%s)"%(['->','<-'][ud]))
					# end for ud
				# end if STS is shown
			# end for i in IDs
#			self.ax3.legend(prop={'size':6}) quite slow. comment it for now
#			self.ax1.legend(loc=2,prop={'size':6})
#			self.ax1b.legend(loc=1,prop={'size':6})
			for x in [self.ax1,self.ax1b,self.ax2,self.ax3,self.ax3b]:
				x.tick_params(axis='both', labelsize=FontSize)
		self.canvas.draw()
		DT=time.clock()-start
		msg="Running time: %f"%(DT)
		item=self.ui.treeWidget.invisibleRootItem()
		child=QtGui.QTreeWidgetItem()	
		child.setText(0,unicode(msg))
		item.addChild(child)
		# end plotUpdate

app = QApplication(sys.argv)
S=STSviewer()
S.show()
sys.exit(app.exec_())
