# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GUI_STSviewer.ui'
#
# Created: Wed Mar 16 22:40:18 2016
#      by: PyQt4 UI code generator 4.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.resize(1114, 728)
        self.centralwidget = QtGui.QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.comboBox = QtGui.QComboBox(self.centralwidget)
        self.comboBox.setGeometry(QtCore.QRect(10, 10, 181, 20))
        self.comboBox.setObjectName(_fromUtf8("comboBox"))
        self.listWidget = QtGui.QListWidget(self.centralwidget)
        self.listWidget.setGeometry(QtCore.QRect(10, 40, 181, 601))
        self.listWidget.setObjectName(_fromUtf8("listWidget"))
        self.widget = QtGui.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(210, 10, 891, 651))
        self.widget.setObjectName(_fromUtf8("widget"))
        self.label = QtGui.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(10, 650, 111, 20))
        self.label.setObjectName(_fromUtf8("label"))
        self.DV = QtGui.QDoubleSpinBox(self.centralwidget)
        self.DV.setGeometry(QtCore.QRect(121, 650, 71, 22))
        self.DV.setDecimals(3)
        self.DV.setMinimum(0.001)
        self.DV.setSingleStep(0.1)
        self.DV.setProperty("value", 0.1)
        self.DV.setObjectName(_fromUtf8("DV"))
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1114, 21))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "STSviewer", None))
        self.label.setText(_translate("MainWindow", "Bandbroadening (ΔV):", None))

