import os, traceback

from PyQt4 import QtCore, QtGui

from ... import plugins #IGNORE:E0611
from ...tankscene import NoVFSRuleError #IGNORE:F0401

from ..progress import ProgressDialog #IGNORE:F0401
from ..browser import BrowserDialog #IGNORE:F0401
from ..utils import pyqtOverrideCursor #IGNORE:F0401

from .model import AssetsModel, SortFilterAssetsModel, Filters
from .ui_assets import Ui_AssetsWindow

class AssetsWindow(QtGui.QWidget, Ui_AssetsWindow):
    def __init__(self, parent=None, **kwargs):
        self._cwd = os.getcwd()
        if parent is not None:
            super(AssetsWindow, self).__init__(parent, **kwargs)
        else:
            super(AssetsWindow, self).__init__(**kwargs)

        self.setupUi(self)

        self._model = AssetsModel(parent)
        self._model.setEditingEnabled(True)

        self._proxyModel = SortFilterAssetsModel(parent)
        self._proxyModel.setSourceModel(self._model)

        self._view.setModel(self._proxyModel)

        self._inspector.setModel(self._proxyModel)
        self._inspector.setSelectionModel(self._view.selectionModel())

        #self._buttons.accepted.connect(self.accept)
        self._buttons.button(QtGui.QDialogButtonBox.Apply).clicked.connect(self.apply)
        self._buttons.button(QtGui.QDialogButtonBox.Close).clicked.connect(self.close)
        #self._buttons.button(QDialogButtonBox.Discard).clicked.connect(self.refresh)
        #self._view.dataChanged.connect(self.updateButtons)

        # connect filter buttons
        self._filterAll.toggled.connect(self._changeFilter)
        self._filterWorking.toggled.connect(self._changeFilter)
        self._filterRevision.toggled.connect(self._changeFilter)
        self._filterOther.toggled.connect(self._changeFilter)

        # set up search
        self._searchBox.returnPressed.connect(self._search)

        self._addWindow = None

    def scene(self):
        return self._model.root()
    def setScene(self, scene):
        self._model.setRoot(scene)
        self._view.expand(self._view.model().index(0, 0))
        # set up actions
        self._updateGearMenu()

    def cwd(self):
        return self._cwd
    def setCwd(self, cwd):
        self._cwd = cwd
    cwd = QtCore.pyqtProperty(int, fget=cwd, fset=setCwd)

    def typeFilter(self):
        return self._proxyModel.typeFilter()
    def setTypeFilter(self, type_filter):
        self._proxyModel.setTypeFilter(type_filter)

#    @QtCore.pyqtSlot(bool)
#    def updateButtons(self, valid):
#        self._buttons.button(QDialogButtonBox.Ok).setEnabled(valid)
#        self._buttons.button(QDialogButtonBox.Apply).setEnabled(valid)

    @QtCore.pyqtSlot()
    def _changeFilter(self):
        if self._filterAll.isChecked():
            self.setTypeFilter(Filters.All)
        elif self._filterWorking.isChecked():
            self.setTypeFilter(Filters.Working)
        elif self._filterRevision.isChecked():
            self.setTypeFilter(Filters.Revision)
        elif self._filterOther.isChecked():
            self.setTypeFilter(Filters.Other)

    @QtCore.pyqtSlot(QtGui.QAbstractButton)
    def buttonPressed(self, button):
        if self._buttons.buttonRole(button) == QtGui.QDialogButtonBox.ApplyRole:
            self.apply()
        elif self._buttons.buttonRole(button) == QtGui.QDialogButtonBox.AcceptRole:
            self.apply()
            self.close()
        elif self._buttons.buttonRole(button) == QtGui.QDialogButtonBox.RejectRole:
            self.close()

    @QtCore.pyqtSlot()
    @pyqtOverrideCursor(QtCore.Qt.BusyCursor)
    def apply(self):
        progress = ProgressDialog(parent=self)
        progress.setWindowTitle("Update Progress")

        self._model.root().commit(callbacks=progress)

        self.refresh()

        progress.close()

    def _updateGearMenu(self):
        self._view.createActions()

        action_menu = QtGui.QMenu(self)

        for action in self._view.actions():
            action_menu.addAction(action)

        self._gearButton.setMenu(action_menu)
        self._gearButton.setPopupMode(QtGui.QToolButton.InstantPopup)

    @QtCore.pyqtSlot(object)
    def _addRevision(self, revision):
        try:
            path = revision.system.vfs_full_paths[0]
        except IndexError:
            raise NoVFSRuleError(revision)

        ext = os.path.splitext(path)[1]

        delegates = plugins.get_delegates(ext=ext, attrs=("add_dependency",))

        if len(delegates) == 0:
            delegate = None
        elif len(delegates) == 1:
            delegate = delegates[0]
        else:
            # show delegate chooser
            # TODO: maybe add this as a new pane in the browser?
            t, ok = QtGui.QInputDialog.getItem(self, "Choose type to add", "Type", [d.__name__ for d in delegates], editable=False)
            if ok:
                # find matching type
                delegate = (d for d in delegates if d.__name__ == t).next()
            else:
                return

        try:
            self._model.addDependency(path, delegate)
        except Exception, e:
            print str(e)
            traceback.print_exc()
            dlg = QtGui.QMessageBox(QtGui.QMessageBox.Critical, "Error", str(e), QtGui.QMessageBox.Ok, self)
            dlg.show()

        self._view.expand(self._view.model().index(0, 0))
        self._updateGearMenu()

    @QtCore.pyqtSlot()
    def add(self):
        # can't use a local variable, as the window will be garbage collected by python and destroyed
        self._addWindow = BrowserDialog(modal=False)
        self._addWindow.setWindowTitle("Add...")
        self._addWindow.setBrowseType(BrowserDialog.BrowseRevisions)
        self._addWindow.setHintText("Double-click a revision to add it to the scene.")
        self._addWindow.setSelectedItem(self._model.root().container)
        self._addWindow.setCwd(self._cwd)
        self._addWindow.doubleClicked.connect(self._addRevision)
        self._addWindow.show()

    @QtCore.pyqtSlot()
    def removeSelected(self):
        selection = self._view.selectionModel().selection()
        source_selection = self._view.model().mapSelectionToSource(selection)
        source_indexes = source_selection.indexes()
        try:
            self._model.remove(source_indexes)
        except Exception, e:
            print str(e)
            traceback.print_exc()
            dlg = QtGui.QMessageBox(QtGui.QMessageBox.Critical, "Error", str(e), QtGui.QMessageBox.Ok, self)
            dlg.show()

        self._view.expand(self._view.model().index(0, 0))
        self._updateGearMenu()

    @QtCore.pyqtSlot(QtGui.QItemSelection, QtGui.QItemSelection)
    def updateButtons(self, selected, deselected):
        self._remove_button.setEnabled(len(selected) > 0)

    @QtCore.pyqtSlot()
    def refresh(self):
        self._model.refresh()
        self._view.expand(self._view.model().index(0, 0))
        self._updateGearMenu()

    @QtCore.pyqtSlot()
    def _search(self):
        text = str(self._searchBox.text())
        if len(text) == 0:
            text = None
        self._view.model().setSearchString(text)
