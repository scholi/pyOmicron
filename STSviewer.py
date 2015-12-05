from PyQt4.QtGui import QMainWindow, QApplication, QFileDialog
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
        self.populateUI()
    def populateUI(self):
        self.fig = self.ui.mplwidget.figure
        self.ax = self.fig.add_subplot(1,1,1)
        self.ui.comboBox.currentIndexChanged.connect(self.plotUpdate)
        self.STS={}
        for i in self.M.images:
            r=re.search(r"--([0-9]+)_([0-9]+).I\(V\)_mtrx",i)
            if r:
                j=int(r.group(1))
                if j in self.STS: self.STS[j]+=1
                else: self.STS[j]=1
        for i in self.STS:
            self.ui.comboBox.addItem(str(i))
    def plotUpdate(self):
        ID=int(self.ui.comboBox.currentText())
        self.ax.clear()
        self.ax.hold(True)
        for i in range(self.STS[ID]):
            x,y=self.M.getSTS(ID,i+1)
            self.ax.plot(x,y)
        self.ui.mplwidget.draw()

app = QApplication(sys.argv)
S=STSviewer()
S.show()
sys.exit(app.exec_())
