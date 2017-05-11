import importlib
import numpy as np
from PyQt4 import QtCore, QtGui, uic
from matplotlib.backends.backend_ps import FigureCanvas
from matplotlib.backends.backend_qt4agg import (
    FigureCanvasQTAgg as FigureCanvas,
    NavigationToolbar2QT as NavigationToolbar)
from matplotlib.figure import Figure
from matplotlib.pyplot import rcParams
from sympy import *

from methodsUI import Ui_Dialog
from resultset import ResultSet
from table import Table
from util import parseExpr, toLatex

rcParams['mathtext.fontset'] = 'stix'

Ui_MainWindow, QtBaseClass = uic.loadUiType('window2.ui')

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class Main(QtGui.QMainWindow, Ui_MainWindow):
    solveButtonTrigger = QtCore.pyqtSignal()
    plt1 = plt2 = plt3 = None
    Dialog = None
    methodsCheckMap = None
    dialogUI = None
    _canvas = None
    isValidEquation = False
    methodsCheckMapAlias = {}
    tempResultSets = []
    tempBoundaries = []

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.figs = [(Figure(), [self.plt1, self.mplvl1, self.mplwindow1]),
                     (Figure(), [self.plt2, self.mplvl2, self.mplwindow2]),
                     (Figure(), [self.plt3, self.mplvl3, self.mplwindow3])]

        self.drawFigs()

        # self.plt.axis([-6, 6, -1, 1])
        # self.equationField.setValidator(QtGui.QRegExpValidator(QtCore.QRegExp("\w"), self))

        self.solveButton.setEnabled(False)
        self.solveButton.clicked.connect(self.solveEquation)
        self.resultsTabWidget.clear()
        self.methodsButton.clicked.connect(self.handleMethodsButton)
        self.textRadio.toggled.connect(self.handlePushButtons)
        self.textRadio.toggle()
        number_group = QtGui.QButtonGroup(self.latexFrame)  # Number group
        number_group.addButton(self.textRadio)
        number_group.addButton(self.fileRadio)

        self.loadFileButton.setDisabled(True)
        self.loadFileButton.clicked.connect(self.openLoadFileDialog)
        self.fileRadio.toggled.connect(self.handlePushButtons)

        self.equationField.textChanged.connect(self.drawLatex)
        self.Dialog = QtGui.QDialog()
        self.dialogUI = Ui_Dialog()
        self.dialogUI.setupUi(self.Dialog)
        self.methodsCheckMap = {self.dialogUI.bisectionCheckBox: [self.dialogUI.bisectionXlField,
                                                                  self.dialogUI.bisectionXuField],
                                self.dialogUI.falsePositionCheckBox: [self.dialogUI.falsePositionXlField,
                                                                      self.dialogUI.falsePositionXuField],
                                self.dialogUI.fixedPointCheckBox: [self.dialogUI.fixedPointX0Field],
                                self.dialogUI.newtonRaphsonCheckBox: [self.dialogUI.newtonRaphsonX0Field],
                                self.dialogUI.secantCheckBox: [self.dialogUI.secantX0Field,
                                                               self.dialogUI.secantX1Field],
                                self.dialogUI.birgeVietaCheckBox: [self.dialogUI.birgeVietaX0Field],
                                self.dialogUI.generalCheckBox: []}
        self.solveButtonTrigger.connect(self.handleSolveButton)
        self.cloneOptionsMapInfo()
        self.setOptionsHandlers()
        r, g, b, a = self.palette().base().color().getRgbF()

        self._figure = Figure(edgecolor=(r, g, b), facecolor=(r, g, b))
        self._canvas = FigureCanvas(self._figure)
        self.latexLayout.addWidget(self._canvas)
        self.latexLayout.setContentsMargins(0, 0, 0, 0)

    @QtCore.pyqtSlot()
    def solveEquation(self):
        # self.plt.clear()
        self.clearAll()
        equ = parseExpr(str(self.equationField.text()))
        for (key, val) in self.methodsCheckMapAlias.items():
            if val[0]:
                method = str(key.objectName())
                self.drawResultSet(
                    getattr(importlib.import_module('methods.' + method), method)(equ, *[float(i) for i in val[1]]))
        # self.canvas.draw()
        self.plotAll()

    @QtCore.pyqtSlot()
    def handleSolveButton(self):
        chosenMethod = False
        for (state, val) in self.methodsCheckMapAlias.values():
            if state:
                chosenMethod = True
                break
        self.solveButton.setEnabled(self.isValidEquation and chosenMethod)

    @QtCore.pyqtSlot()
    def openLoadFileDialog(self):
        print QtGui.QFileDialog.getOpenFileName(self, 'Open equation',
                                                '', "All (*.*)")

    def clearAll(self):
        count = self.resultsTabWidget.count()
        for i in xrange(count):
            self.resultsTabWidget.widget(i).deleteLater()
        self.tempResultSets[:] = []
        self.tempBoundaries[:] = []
        self.clearPlots()

    def clearPlots(self):
        self.plt1.cla()
        self.plt1.grid(true)
        self.plt1.autoscale(true, tight=false)
        self.plt2.cla()
        self.plt2.grid(true)
        self.plt2.autoscale(true, tight=false)
        self.plt3.cla()
        self.plt3.grid(true)
        self.plt3.autoscale(true, tight=false)

    def setOptionsHandlers(self):
        for (key, val) in self.methodsCheckMap.items():
            key.stateChanged.connect(self.assignReadOnlyHandler)
            key.stateChanged.connect(self.checkForValidInputs)
            for va in val:
                va.textChanged.connect(self.checkForValidInputs)

    def checkForValidInputs(self, text):
        buttonState = False
        for (key, vals) in self.methodsCheckMap.items():
            if key.isChecked():
                tempState = True
                for val in vals:
                    if val.validator().validate(val.text(), 0)[0] != QtGui.QValidator.Acceptable:
                        tempState = False
                        break
                if not tempState:
                    buttonState = False
                    break
                else:
                    buttonState = True
        self.dialogUI.buttonBox.button(QtGui.QDialogButtonBox.Ok).setEnabled(buttonState)

    def assignReadOnlyHandler(self, state):
        checkBox = self.sender()
        for val in self.methodsCheckMap[checkBox]:
            val.setReadOnly(True) if not checkBox.isChecked() else val.setReadOnly(False)

    def cloneOptionsMapInfo(self):
        for (key, val) in self.methodsCheckMap.items():
            vals = []
            for va in val:
                vals.append(str(va.text()))
            self.methodsCheckMapAlias[key] = (key.isChecked(), vals)

    def pasteToOptionsMapInfo(self):
        for (key, val) in self.methodsCheckMapAlias.items():
            key.setChecked(val[0])
            for i in range(len(val[1])):
                self.methodsCheckMap[key][i].setText(val[1][i])

    def handlePushButtons(self):
        self.equationField.setReadOnly(True) if not self.textRadio.isChecked() else self.equationField.setReadOnly(
            False)
        self.loadFileButton.setDisabled(True) if not self.fileRadio.isChecked() else self.loadFileButton.setDisabled(
            False)

    def handleMethodsButton(self):
        if self.Dialog.exec_():
            self.cloneOptionsMapInfo()
            self.solveButtonTrigger.emit()
        else:
            self.pasteToOptionsMapInfo()

    def initTableWidget(self):
        qWidget = QtGui.QWidget()
        qVbox = QtGui.QVBoxLayout()
        qTable = QtGui.QTableWidget()
        qTable.setObjectName("Table")
        qWidget2 = QtGui.QWidget()
        hBox = QtGui.QHBoxLayout()
        hBox.setMargin(0)
        rootLabel = QtGui.QLabel()
        rootLabel.setText("Root")
        rootField = QtGui.QLineEdit()
        rootField.setObjectName("Root")
        rootField.setReadOnly(True)
        hBox.addWidget(rootLabel)
        hBox.addWidget(rootField)
        qWidget2.setLayout(hBox)
        qWidget3 = QtGui.QWidget()
        hBox2 = QtGui.QHBoxLayout()
        hBox2.setMargin(0)
        precisionLabel = QtGui.QLabel()
        precisionLabel.setText("Precision")
        precisionField = QtGui.QLineEdit()
        precisionField.setObjectName("Precision")
        precisionField.setReadOnly(True)
        timeLabel = QtGui.QLabel()
        timeLabel.setText("Time")
        timeField = QtGui.QLineEdit()
        timeField.setObjectName("Time")
        timeField.setReadOnly(True)
        hBox2.addWidget(precisionLabel)
        hBox2.addWidget(precisionField)
        hBox2.addWidget(timeLabel)
        hBox2.addWidget(timeField)
        qWidget3.setLayout(hBox2)
        qVbox.addWidget(qTable)
        qVbox.addWidget(qWidget2)
        qVbox.addWidget(qWidget3)
        qWidget.setLayout(qVbox)
        return qWidget

    def drawLatex(self, text):
        self._figure.clear()
        self.isValidEquation, latexText = toLatex(text)
        text = self._figure.suptitle(
            latexText,
            size=QtGui.QApplication.font(self).pointSize() * 1.8)
        self._canvas.draw()
        self.solveButtonTrigger.emit()

    def drawFigs(self):
        i = 0
        for (fig, ls) in self.figs:
            ls[0] = fig.add_subplot(111)
            ls[0].grid(true)
            canvas = FigureCanvas(fig)
            canvas.setObjectName("canvas" + str(i))
            ls[1].addWidget(canvas)
            toolbar = NavigationToolbar(canvas,
                                        ls[2], coordinates=True)
            ls[1].addWidget(toolbar)
            ls[0].autoscale(true, tight=false)
            i += 1

        self.plt1 = self.figs[0][1][0]
        self.plt2 = self.figs[1][1][0]
        self.plt3 = self.figs[2][1][0]

    def plotAll(self):
        for i in xrange(3):
            self.graphTabWidget.findChild(FigureCanvas, 'canvas' + str(i)).draw()

    def plotFunction(self, equation):
        xs = np.arange(-100.0, 100.0, 0.1)
        if equation.is_vertical:
            return self.plotVLines(equation.get_eqn())
        else:
            return self.plt1.plot(xs, equation.get_eqn()(xs), c=np.random.rand(3, 1))

    def plotVLines(self, vLines):
        return self.plt1.axvline(x=vLines, c=np.random.rand(3, 1))

    def plotHLines(self, hLines):
        assert type(hLines) is list, "hLines is not of type list!: " + str(type(hLines))
        for line in hLines:
            self.plt1.axhlne(y=line, c=np.random.rand(3, 1))

    def plotPoints(self, xs, ys):
        # plt = self.fig1.add_subplot(111)
        for i in xrange(len(xs)):
            self.plt1.scatter(xs[i], ys[i], marker="x", s=100, c=np.random.rand(3, 1))

    def plotError(self, errors):
        err = []
        its = []
        for i in xrange(1, len(errors)):
            err.append(errors[i][1])
            its.append(errors[i][0])
        self.plt2.plot(its, err, c=np.random.rand(3, 1))

    def plotRoot(self, roots):
        root = []
        its = []
        for (i, r) in roots:
            root.append(r)
            its.append(i)
        self.plt3.plot(its, root, c=np.random.rand(3, 1))

    def drawTable(self, table):
        assert type(table) is Table, "table is not of type Table!: " + str(type(table))
        qWidget = self.initTableWidget()
        self.resultsTabWidget.addTab(qWidget, QtCore.QString(table.getTitle()))
        qTable = self.resultsTabWidget.findChild(QtGui.QTableWidget, "Table")
        setattr(self, 'Table%d' % self.resultsTabWidget.count(), qTable)

        qTable.setColumnCount(len(table.getHeader()))
        qTable.setHorizontalHeaderLabels(table.getHeader())
        qTable.setEditTriggers(QtGui.QTableWidget.NoEditTriggers)
        qTable.setSelectionBehavior(QtGui.QTableWidget.SelectRows)
        qTable.setSelectionMode(QtGui.QTableWidget.SingleSelection)
        qTable.itemSelectionChanged.connect(self.plotTempBoundaries)
        qTable.setRowCount(len(table.getData()))
        for row in xrange(len(table.getData())):
            for column in xrange(len(table.getHeader())):
                qTable.setItem(row, column,
                               QtGui.QTableWidgetItem(str(('%g' % table.getData()[row][column]) if type(
                                   table.getData()[row][column]) is float else table.getData()[row][column])))

        return qWidget

    def plotTempBoundaries(self):
        for bound in self.tempBoundaries:
            bound.remove()
        self.tempBoundaries[:] = []
        i = self.resultsTabWidget.currentIndex()
        item = getattr(self, 'Table%d' % (i + 1)).selectedItems()[0]
        for bound in self.tempResultSets[i].getBoundaries()[item.row()]:
            self.tempBoundaries.append(self.plotFunction(bound))
        self.plotAll()

    def drawRoot(self, root, rootField):
        assert type(root) is float or int, "root is not of type float nor int!: " + str(type(root))
        assert type(rootField) is QtGui.QLineEdit, "rootField is not of type QtGui.QLineEdit!: " + str(type(rootField))
        rootField.setText(str(root))

    def drawPrecision(self, precision, precisionField):
        assert type(precision) is float or int, "precision is not of type float nor int!: " + str(type(precision))
        assert type(precisionField) is QtGui.QLineEdit, "precisionField is not of type QtGui.QLineEdit!: " + str(
            type(precisionField))
        precisionField.setText(str(precision))

    def drawTime(self, time, timeField):
        assert type(time) is float or int, "time is not of type float nor int!: " + str(type(time))
        assert type(timeField) is QtGui.QLineEdit, "timeField is not of type QtGui.QLineEdit!: " + str(type(timeField))
        timeField.setText(str(('%g' % time)))

    def drawResultSet(self, resultSet):
        assert type(resultSet) is ResultSet, "table is not of type Table!: " + str(type(resultSet))
        self.tempResultSets.append(resultSet)
        self.plotFunction(resultSet.getEquation())
        qWidget = self.drawTable(resultSet.getTable())
        self.drawRoot(resultSet.getRoot(), qWidget.findChild(QtGui.QLineEdit, "Root"))
        self.drawPrecision(resultSet.getPrecision(), qWidget.findChild(QtGui.QLineEdit, "Precision"))
        self.drawTime(resultSet.getExecutionTime(), qWidget.findChild(QtGui.QLineEdit, "Time"))
        self.plotError(resultSet.getErrors())
        self.plotRoot(resultSet.getRoots())


if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)
    main = Main()
    main.show()
    main.showMaximized()
    sta = 'bisection'
    # print getattr(importlib.import_module(sta), sta)(1, 0, parseExpr('x^3'))
    # print func(sta)
    # main.drawResultSet(false_position(-5, 5, parseExpr("x^3 ")))

    sys.exit(app.exec_())
