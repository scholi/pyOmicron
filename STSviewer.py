from PyQt4.QtGui import QMainWindow, QApplication, QFileDialog
from PyQt4 import QtGui, QtCore
from GUI_STSviewer import Ui_MainWindow
import sys
import pyOmicron as pyO
import re

class STSviewer(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        # Set up the user interface from Designer.
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.path=QFileDialog.getExistingDirectory()
        self.M=pyO.Matrix(self.path)
        val=200
        self.colors=[(0,0,val),(0,val,0),(val,0,0),(val,val,0),(val,0,val),(0,val,val)]
        
        # SIGNALS -> SLOTS
        self.ui.comboBox.currentIndexChanged.connect(self.updateSTSid)
        self.ui.listWidget.itemSelectionChanged.connect(self.plotUpdate)
        self.populateUI()
        
    def populateUI(self):
        self.ui.listWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.fig = self.ui.mplwidget.figure
        self.ax = self.fig.add_subplot(1,1,1)    
        self.STS={}
        for i in self.M.images:
            r=re.search(r"--([0-9]+)_([0-9]+).I\(V\)_mtrx",i)
            if r:
                j=int(r.group(1))
                if j in self.STS: self.STS[j]+=1
                else: self.STS[j]=1
        for i in self.STS:
            self.ui.comboBox.addItem(str(i))

    def updateSTSid(self):
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
        ID=int(self.ui.comboBox.currentText())
        self.ax.clear()
        self.ax.hold(True)
        for i in range(self.STS[ID]):
            if self.ui.listWidget.isItemSelected(self.ui.listWidget.item(i)):
                x,y=self.M.getSTS(ID,i+1)
                self.ax.plot(x,y,color="#{0:02x}{1:02x}{2:02x}".format(*self.colors[i%len(self.colors)]))
        self.ui.mplwidget.draw()

app = QApplication(sys.argv)
S=STSviewer()
S.show()
sys.exit(app.exec_())
