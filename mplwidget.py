from PyQt4 import QtGui
import matplotlib as mpl
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.mlab as mlab
import matplotlib.gridspec as gridspec

class MplCanvas(FigureCanvas):
	def __init__(self):
		self.fig = Figure()
		FigureCanvas.__init__(self, self.fig)
		FigureCanvas.setSizePolicy(self,
			QtGui.QSizePolicy.Expanding,
			QtGui.QSizePolicy.Expanding)
		FigureCanvas.updateGeometry(self)

class MplWidget(QtGui.QWidget):
		def __init__(self, parent = None):
			QtGui.QWidget.__init__(self, parent)
			self.canvas = MplCanvas()
			self.canvas.setParent(self)
			self.mpl_toolbar = NavigationToolbar(self.canvas, self)
