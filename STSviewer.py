#!/usr/bin/python

from PyQt4.QtGui import QMainWindow, QApplication, QFileDialog
from PyQt4 import QtGui, QtCore
from GUI_STSviewer import Ui_MainWindow
import sys
import pyOmicron as pyO
import re
import numpy as np
import sys,os
import matplotlib.gridspec as gridspec
from STS import STS

FontSize=8

class STSviewer(QMainWindow):
	def plot_err1(self, ax,X,Y,DY,col):
		"""
		Function to plot the mean and the statistical error (1*sigma and 2*sigma as a filled area)
		ax: The axis object
		X: the vector containing the X-data
		Y: the vector containing the mean data
		DY: the vector containing the standard-deviation data
		X,Y and DY should have the same length
		"""
		ax.plot(X,Y,color=col)
		ax.fill_between(X,Y-DY,Y+DY,facecolor=col,alpha=0.3)
		ax.fill_between(X,Y-2*DY,Y+2*DY,facecolor=col,alpha=0.2)

	def on_pick(self):
		pass

	def __init__(self):
		"""
		Initialize the graphical user interface
		"""
		QMainWindow.__init__(self)
		# Set up the user interface from Designer.
		self.ui = Ui_MainWindow()
		self.ui.setupUi(self)

		# Setup the ploting widgets
		self.canvas=self.ui.mpl.canvas
		self.fig = self.ui.mpl.canvas.fig
		self.canvas.mpl_connect('pick_event', self.on_pick)
		
		self.save=False 

		# Setup the plotting layout
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

		# Loocking for a Table of Content file (called toc.txt or ToX.txt)
		self.ToC=None
		f=False
		if os.path.exists(self.path+"/toc.txt"):
			f=open(self.path+"/toc.txt","r")
		elif os.path.exists(self.path+"/ToC.txt"):
			f=open(self.path+"/ToC.txt","r")
		if f:
			self.ToC={int(z[0]):z[1] for z in [x.split() for x in f.readlines()]}
			f.close()
		val=200 # value used for the colors
		# colors used for the plot lines
		self.colors=[(0,0,val),(0,val,0),(val,0,0),(val,val,0),(val,0,val),(0,val,val)]
		
		# Add the found data to the combo box
		self.populateUI()

		if len(sys.argv)>2:
			ID=sys.argv[2]
			self.ui.comboBox.setCurrentIndex(self.ui.comboBox.findText(ID))

		# QT: SIGNALS -> SLOTS
		# This set which function is called when buttons, checkboxes, etc. are clicked
		self.ui.comboBox.currentIndexChanged.connect(self.updateSTSid)
		self.ui.listWidget.itemChanged.connect(self.plotUpdate)
		self.ui.DV.valueChanged.connect(self.plotUpdate)
		self.ui.statCB.stateChanged.connect(self.plotUpdate)
		self.ui.normCB.stateChanged.connect(self.plotUpdate)
		self.ui.pushButton.clicked.connect(self.InfoShowHideToggle)
		self.ui.saveBT.clicked.connect(self.export)
		self.InfoShowHideToggle('Hide')
		
		self.updateSTSid()
		self.plotUpdate()

	def InfoShowHideToggle(self,action='Toggle'):
		"""
		Show a TreeWidget containing the details of a STS scan.
		"""
		if action=='Hide' or self.ui.treeWidget.isVisible():
			self.ui.treeWidget.hide()
			self.ui.pushButton.setText("<<")
		else:
			self.ui.treeWidget.show()
			self.ui.pushButton.setText(">>")

	def populateUI(self):
		"""
		Look for I(V) measurements and add them to the combobox list
		"""
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
			if self.ToC!=None and i in self.ToC:
				self.ui.comboBox.addItem(str(i)+" (%s)"%(self.ToC[i]))
			else:
				self.ui.comboBox.addItem(str(i))

	def updateSTSid(self):
		"""
		If and ID is chosen, the listWidget will be populated with the correct num and selected
		"""
		self.ui.listWidget.itemChanged.disconnect()
		self.ui.listWidget.clear()
		ID=int(self.ui.comboBox.currentText().split(' ')[0])
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
		"""
		Gather information about the STS measurement and populate the treeWidget (the one hidden on the right of the screen)
		"""
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
	def export(self):
		"""
		Toggle the flag to save the data
		"""
		self.save=True
		self.plotUpdate()
		self.save=False		
	
	def plotUpdate(self):
		"""
		Most important function which is retrieving and plotting the data
		"""
		# Clear the plot
		self.ax1.clear()
		self.ax1b.clear()
		self.ax2.clear()
		self.ax3.clear()
		self.ax3b.clear()

		# Setting labels and axis
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

		# plot the selected curves
		ID=int(self.ui.comboBox.currentText().split(' ')[0])
		paramsShowed=False
		stat=False
		norm=False
		if self.ui.statCB.isChecked(): stat=True
		if self.ui.normCB.isChecked(): norm=True
		counter=0
		for i in range(self.STS[ID]): # Scan over all STS having the same ID
			if self.ui.listWidget.item(i).checkState()==QtCore.Qt.Checked: # Is the curve selected by the user to be plotted?
				V,I,IM=self.M.getSTS(ID,i+1,params=True)
				NPTS=int(IM['Spectroscopy']['Device_1_Points']['value']) # Number of points in the V range
				DV=self.ui.DV.value()
				Vstep=(IM['Spectroscopy']['Device_1_End']['value']-IM['Spectroscopy']['Device_1_Start']['value'])/float(NPTS)
				skip=int(np.ceil(DV/Vstep))
				if not paramsShowed:
					paramsShowed=True
					p=self.M.getSTSparams(ID,i+1)
					self.updateModel(p)
					N=(0,NPTS)
					Im=[np.empty(N),np.empty(N)]
					dIm=[np.empty(N),np.empty(N)]
					IVm=[np.empty((0,NPTS+2*skip)),np.empty((0,NPTS+2*skip))]
					BIVm=[np.empty(N),np.empty(N)]
					dIdVIVm=[np.empty(N),np.empty(N)]
				sV=np.linspace(min(V),max(V),NPTS) # Voltage values in increading order
				if len(I)<NPTS: # Missing data
					I=np.pad(I,NPTS,'constant',constant_values=np.nan)
				elif len(I)>NPTS: # Forward & Backward scan
					if V[1]<V[0]: # Start with Downward scan
						IUp=I[NPTS:]
						IDown=I[NPTS-1::-1]
					else:
						IUp=I[:NPTS]
						IDown=I[-1:NPTS-1:-1]
					if len(IDown)<NPTS: # Missing data
						IDown=np.pad(IDown,NPTS,'constant',constant_values=np.nan)
					Im[0]=np.vstack((Im[0],IUp))
					Im[1]=np.vstack((Im[1],IDown))
					if not stat: self.ax1.plot(sV,IUp*1e-6,
						color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]),
						label="I%i (->)"%(i))
					if not stat: self.ax1.plot(sV,IDown*1e-6,'--',
						color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]),
						label="I%i (<-)"%(i))
				else:
					if V[0]==min(V):
						Im[0]=np.vstack((Im[0],I))
					else:
						Im[1]=np.vstack((Im[1],I))
					if not stat: self.ax1.plot(V,I*1e-6,
						color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]),
						label="I%i"%(i))
					
				if ID in self.hasDIDV:
					V2,dI=self.M.getDIDV(ID,i+1)
					if norm: dI-=dI.min()
					if len(I)>NPTS: # Forward & Backward scan
						if V[1]<V[0]: # Start with Downward scan
							dIUp=dI[NPTS:]
							dIDown=dI[NPTS-1::-1]
						else:
							dIUp=dI[:NPTS]
							dIDown=dI[-1:NPTS-1:-1]
						dIm[0]=np.vstack((dIm[0],dIUp))
						dIm[1]=np.vstack((dIm[1],dIDown))
						Is=[IUp,IDown]
						dIs=[dIUp,dIDown]
					else:
						Is=[I]
						dIs=[dI]
						if V[0]==min(V):
							dIm[0]=np.vstack((dIm[0],dI))
						else:
							dIm[1]=np.vstack((dIm[1],dI))

					for ud in range(len(Is)):
						if len(dIs[ud])<NPTS: dIs[ud]=np.pad(dIs[ud],NPTS,'constant',constant_values=np.nan)
						if not stat: self.ax1b.plot(sV,dIs[ud]*1e-6,[':','-.'][ud],
							color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]),
							label="dI%i (%s)"%(i,['->','<-'][ud]))
						delta=NPTS-len(Is[ud])
						if delta>0:
							if V[1]>V[0]: # problem on the downscan
								sV=sV[delta:]
							else:
								sV=sV[:-delta]
						S=STS(sV,Is[ud],DV)
						IV=S.getIV()
						BIV=S.getBIV()
						W=S.getW()
						nV=S.getnV()
						IVm[ud]=np.vstack((IVm[ud],IV))
						BIVm[ud]=np.vstack((BIVm[ud],BIV))
						dIdVIVm[ud]=np.vstack((dIdVIVm[ud],dIs[ud]/BIV))
						if not stat: self.ax3.plot(nV,1e-12*IV,['b','--b'][ud],
							label="I/V (%s)"%(["->","<-"][ud]))
						if not stat: self.ax3.plot(sV,1e-12*BIV,['r','--r'][ud],
							label="$\overline{I/V}$ (%s)"%(["->","<-"][ud]))
						if ud==0: self.ax3b.plot(nV,W,'g',label="conv. func.")
						if not stat: self.ax2.plot(sV,dIs[ud]/BIV,['-','--'][ud],
							color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]),
							label="(%s)"%(['->','<-'][ud]))
					# end for ud
				# end if STS is shown
			# end for i in IDs
#			self.ax3.legend(prop={'size':6}) quite slow. comment it for now
#			self.ax1.legend(loc=2,prop={'size':6})
#			self.ax1b.legend(loc=1,prop={'size':6})
		if stat: # If statistic checkbox is enabled
			for ud in range(2):
				if Im[ud].shape[0]==0: continue
				fmt=['-','--'][ud]
				col1=['blue','purple'][ud]
				col2=['red','orange'][ud]
				col3=['green','green'][ud]
				Imm=Im[ud].mean(axis=0)
				Ims=Im[ud].std(axis=0)
				
				dImm=dIm[ud].mean(axis=0)
				dIms=dIm[ud].std(axis=0)

				dIVm=dIdVIVm[ud].mean(axis=0)
				dIVs=dIdVIVm[ud].std(axis=0)
				IVmm=IVm[ud].mean(axis=0)
				IVms=IVm[ud].std(axis=0)
				BIVmm=BIVm[ud].mean(axis=0)
				BIVms=BIVm[ud].std(axis=0)
				self.plot_err1(self.ax1,sV,Imm,Ims,col1)
				self.plot_err1(self.ax1b,sV,dImm,dIms,col2)
				self.plot_err1(self.ax2,sV,dIVm,dIVs,col1)
				self.plot_err1(self.ax3,nV,IVmm,IVms,col1)
				self.ax3.plot(sV,BIVmm,color=col2)
				self.ax3.fill_between(sV,BIVmm-BIVms,BIVmm+BIVms,facecolor=col2,alpha=0.3)
				self.ax3.fill_between(sV,BIVmm-2*BIVms,BIVmm+2*BIVms,facecolor=col2,alpha=0.2)
		for x in [self.ax1,self.ax1b,self.ax2,self.ax3,self.ax3b]:
			x.tick_params(axis='both', labelsize=FontSize)
		self.canvas.draw()
		# end plotUpdate

app = QApplication(sys.argv)
S=STSviewer()
S.show()
sys.exit(app.exec_())
