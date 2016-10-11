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

"""
	Developer: Olivier Scholder
	GIT repo: https://github.com/scholi/pyOmicron
	
	This App display a graphical window with various plot to analyse the I(V), dI/dI and (dI/dV)/(I/V) from Omicron STS files
"""

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

	def on_pick(self): # Do nothing important
		pass
	
	def initPlotLayout(self):
		"""
		Setup the plotting layout.
		"""
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

	def __init__(self,DIext='Aux2'):
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

		self.DIext=DIext

		# Setup the plotting layout
		self.initPlotLayout()

		# Ask for the directory containing the matrix files
		if len(sys.argv)<2:
			self.path=QFileDialog.getExistingDirectory()
		else:
			# If an argument is sent to the script, the first argument will be used as a Path. Very usefull for debugging the script without having to selectr the folder each time with window dialog
			self.path=sys.argv[1]
		
		# Read the Matrix file
		self.M=pyO.Matrix(self.path)

		# Looking for a Table of Content file (called toc.txt or ToC.txt)
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


		# QT: SIGNALS -> SLOTS
		# This set which function is called when buttons, checkboxes, etc. are clicked
		self.ui.comboBox.currentIndexChanged.connect(self.updateSTSid)
		self.ui.tableWidget.itemChanged.connect(self.plotUpdate)
		self.ui.DV.valueChanged.connect(self.plotUpdate)
		self.ui.statCB.stateChanged.connect(self.plotUpdate)
		self.ui.normCB.stateChanged.connect(self.plotUpdate)
		self.ui.pushButton.clicked.connect(self.InfoShowHideToggle)
		self.ui.saveBT.clicked.connect(self.export)
		self.InfoShowHideToggle('Hide')
		
		self.updateSTSid()
		
		if len(sys.argv)>2:
			ID=sys.argv[2]
			self.ui.comboBox.setCurrentIndex(self.ui.comboBox.findText(ID,QtCore.Qt.MatchStartsWith))

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
			if r and os.path.exists(self.path+"/"+i):
				j=int(r.group(1))
				if j in self.STS: self.STS[j]+=1
				else: self.STS[j]=1
				if i[:-9]+self.DIext+'(V)_mtrx' in self.M.images: self.hasDIDV.append(j)
		for i in self.STS:
			if self.ToC!=None and i in self.ToC:
				self.ui.comboBox.addItem(str(i)+" (%s)"%(self.ToC[i]))
			else:
				self.ui.comboBox.addItem(str(i))

	def updateSTSid(self):
		"""
		If and ID is chosen, the tableWidget will be populated with the correct num and selected
		"""
		if self.ui.comboBox.currentIndex()==-1: raise ValueError("No Data found!")
		self.ui.tableWidget.itemChanged.disconnect()
		self.ui.tableWidget.clear()
		ID=int(self.ui.comboBox.currentText().split(' ')[0])
		self.ui.tableWidget.setRowCount(self.STS[ID])
		self.ui.tableWidget.setColumnCount(3)
		for i in range(self.STS[ID]):
			item = QtGui.QTableWidgetItem()
			item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
			item.setCheckState(QtCore.Qt.Checked)
			self.ui.tableWidget.setItem(i,0,item)

			item = QtGui.QTableWidgetItem()
			item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
			item.setCheckState(QtCore.Qt.Checked)
			self.ui.tableWidget.setItem(i,1,item)

			item = QtGui.QTableWidgetItem()
			item.setText(str(i+1)+" -----")
			item.setTextColor(QtGui.QColor(*self.colors[i%len(self.colors)]))
			self.ui.tableWidget.setItem(i,2,item)
		self.ui.tableWidget.itemChanged.connect(self.plotUpdate)
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
					child.setText(0,str(value['value']))
				else:
					child.setText(0,str(value['value'])+" "+str(value['unit']))
				item.addChild(child)
			else:
				for key, val in sorted(value.items()):
					child=QtGui.QTreeWidgetItem()
					child.setText(0,key)
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
					child.setText(0, str(val))
				child.setExpanded(True)
		else:
			child=QtGui.QTreeWidgetItem()
			child.setText(0,str(value))
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
		
		# If checkbox "statistics" is checked, then variable stat=True
		if self.ui.statCB.isChecked(): stat=True 
		if self.ui.normCB.isChecked(): norm=True
		counter=0
		NumShown=[]

		for i in range(self.STS[ID]): # Scan over all STS having the same ID
			ShowUp=self.ui.tableWidget.item(i,0).checkState()==QtCore.Qt.Checked
			ShowDown=self.ui.tableWidget.item(i,1).checkState()==QtCore.Qt.Checked
			print(ID,i,ShowUp,ShowDown)
			if ShowUp or ShowDown: # Is the curve selected by the user to be plotted?
				if not i+1 in NumShown:	NumShown.append(i+1) # Store in a list which num will be displayed

				# Retrieve the STS data for the ID and num=i+1
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

					# The follwing variables store matrices of the various signals as a list. The first element of the list is for the Up scans and the second for Down scans
					Im=[np.empty(N),np.empty(N)] # Current: I
					dIm=[np.empty(N),np.empty(N)] # dI/dV
					IVm=[np.empty((0,NPTS+2*skip)),np.empty((0,NPTS+2*skip))] # I/V
					BIVm=[np.empty(N),np.empty(N)] # Broadened I/V (BIV)
					dIdVIVm=[np.empty(N),np.empty(N)] # (dI/dV)/BIV

				# reconstruct the voltage array
				sV=np.linspace(min(V),max(V),NPTS) # Voltage values in increading order

				if len(I)<NPTS: # Missing data
					I=np.pad(I,NPTS,'constant',constant_values=np.nan)
				elif len(I)>NPTS: # Forward & Backward scan
					if V[1]<V[0]: # Start with Downward scan
						IUp=I[NPTS:]
						IDown=I[NPTS-1::-1] # flip first part of the data
					else:
						IUp=I[:NPTS]
						IDown=I[-1:NPTS-1:-1] # Flip second part of the data
					if len(IDown)<NPTS: # Missing data
						IDown=np.pad(IDown,NPTS,'constant',constant_values=np.nan)
					if ShowUp: Im[0]=np.vstack((Im[0],IUp))   # Im[0] contains the Up scans
					if ShowDown: Im[1]=np.vstack((Im[1],IDown)) # Im[1] contains the Down scans
					if not stat and ShowUp:
						self.ax1.plot(sV,IUp*1e-6,
							color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]),
							label="I%i (->)"%(i))
					if not stat and ShowDown:
						self.ax1.plot(sV,IDown*1e-6,'--',
							color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]),
							label="I%i (<-)"%(i))
				else: # Start with upward scan without backward info
					if V[0]==min(V):
						if ShowUp: Im[0]=np.vstack((Im[0],I))
					else:
						if ShowDown: Im[1]=np.vstack((Im[1],I))
					if not stat: self.ax1.plot(V,I*1e-6,
						color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]),
						label="I%i"%(i))
					
				if ID in self.hasDIDV:
					V2,dI=self.M.getSTS(ID,i+1,self.DIext)
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
					# end for ud (up/down)
				# end if STS is shown
			# end for i in IDs
##			self.ax3.legend(prop={'size':6}) quite slow. comment it for now
##			self.ax1.legend(loc=2,prop={'size':6})
##		 	self.ax1b.legend(loc=1,prop={'size':6})

		if self.save:
			# Saving the data
			X=np.vstack((sV,Im[0],dIm[0],Im[1],dIm[1],dIdVIVm[0],dIdVIVm[1]))
			header="DV=%.3fV\nV\t"%(DV)
			header+="\t".join(["I{}_Up(V)".format(i) for i in NumShown])
			header+="\t"+"\t".join(["dI{}/dV_Up".format(i) for i in NumShown])
			header+="\t"+"\t".join(["I{}_Down(V)".format(i) for i in NumShown])
			header+="\t"+"\t".join(["dI{}/dV_Down".format(i) for i in NumShown])
			header+="\t"+"\t".join(["(dI{}_Up/dV)/(I/V)".format(i) for i in NumShown])
			header+="\t"+"\t".join(["(dI{}_Down/dV)/(I/V)".format(i) for i in NumShown])
			np.savetxt("STS_%i.dat"%(ID),X.transpose(),header=header)
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
				try:
					self.plot_err1(self.ax1b,sV,dImm,dIms,col2)
					self.plot_err1(self.ax2,sV,dIVm,dIVs,col1)
					self.plot_err1(self.ax3,nV,IVmm,IVms,col1)
				except:
					pass # No DI signal
				self.ax3.plot(sV,BIVmm,color=col2)
				self.ax3.fill_between(sV,BIVmm-BIVms,BIVmm+BIVms,facecolor=col2,alpha=0.3)
				self.ax3.fill_between(sV,BIVmm-2*BIVms,BIVmm+2*BIVms,facecolor=col2,alpha=0.2)
		for x in [self.ax1,self.ax1b,self.ax2,self.ax3,self.ax3b]:
			x.tick_params(axis='both', labelsize=FontSize)
		self.canvas.draw()
		# end plotUpdate

app = QApplication(sys.argv)
S=STSviewer(DIext='Aux1')
S.show()
sys.exit(app.exec_())
