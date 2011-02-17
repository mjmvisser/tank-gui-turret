import os

from PyQt4 import QtCore, QtGui

from .ui_browser import Ui_Browser
from .revision_results import RevisionResultsProxyModel

class BrowserDialog(QtGui.QDialog, Ui_Browser):
    BrowseRevisions = 0
    BrowseContainers = 1

    FilterTank = 0
    FilterFiles = 1
    FilterShotgun = 2

    def __init__(self, parent=None, **kwargs):
        self._resultsFilter = RevisionResultsProxyModel.FilterAll
        self._cwd = os.getcwd()
        self._browseType = BrowserDialog.BrowseRevisions

        if parent:
            super(BrowserDialog, self).__init__(parent, **kwargs)
        else:
            super(BrowserDialog, self).__init__(**kwargs)

        self.setupUi(self)

        self._resultsView = self._tankRevisionsView
        self._filterView = self._tankFilterView

        self._tankButton.clicked.connect(lambda: self._switchFilterPage(BrowserDialog.FilterTank))
        self._fileButton.clicked.connect(lambda: self._switchFilterPage(BrowserDialog.FilterFiles))
        self._shotgunButton.clicked.connect(lambda: self._switchFilterPage(BrowserDialog.FilterShotgun))

        # connect selection notification to our handler
        self._tankFilterView.selectionModel().selectionChanged.connect(self._setConstraints)
        self._fileFilterView.selectionModel().selectionChanged.connect(self._setConstraints)
        self._shotgunFilterView.selectionModel().selectionChanged.connect(self._setConstraints)

        # switch to the default page
        self._switchFilterPage(BrowserDialog.FilterTank)

        self._filterAll.clicked.connect(self._changeFilter)
        self._filterRecommended.clicked.connect(self._changeFilter)
        self._filterLatest.clicked.connect(self._changeFilter)

        if self.isModal():
            self._buttons.addButton(QtGui.QDialogButtonBox.Ok)
            self._buttons.addButton(QtGui.QDialogButtonBox.Cancel)
            self._tankRevisionsView.doubleClicked.connect(self.accept)
            self._tankContainersView.doubleClicked.connect(self.accept)
        else:
            self._buttons.addButton(QtGui.QDialogButtonBox.Close)
            self._resultsView.doubleClicked.connect(self._doubleClicked)

        self._settings = QtCore.QSettings()

        self._settings.beginGroup("Browser")
        if not self._settings.value("resultsFilter").isNull():
            self.setResultsFilter(self._settings.value("resultsFilter").toInt()[0])
        self._settings.endGroup()

        # set up search
        self._searchBox.returnPressed.connect(self._search)
        self._searchBox.setEnabled(False)
        self._searchBox.setHidden(True)

    ###
    ### Signals
    ###
    doubleClicked = QtCore.pyqtSignal(object)

    ###
    ### Properties
    ###
    def browseType(self):
        return self._browseType
    def setBrowseType(self, browse_type):
        self._browseType = browse_type
        assert browse_type in (BrowserDialog.BrowseRevisions, BrowserDialog.BrowseContainers)
        self._resultsSwitcher.setCurrentIndex(browse_type)
        if browse_type == BrowserDialog.BrowseRevisions:
            self._resultsView = self._tankRevisionsView
            self._tankFilterView.model().setIncludeRevisionTypes(True)
            self._shotgunFilterView.model().setIncludeRevisionTypes(True)
        else:
            self._resultsView = self._tankContainersView
            self._tankFilterView.model().setIncludeRevisionTypes(False)
            self._shotgunFilterView.model().setIncludeRevisionTypes(False)
        self._tankFilterView.updateActions()

    def hintText(self):
        return self._hintLabel.text()
    def setHintText(self, text):
        self._hintLabel.setText(text)

    def resultsFilter(self):
        return self._tankRevisionsView.filter()
    def setResultsFilter(self, results_filter):
        if results_filter == RevisionResultsProxyModel.FilterAll and not self._filterAll.isChecked():
            self._filterAll.setChecked(True)
        elif results_filter == RevisionResultsProxyModel.FilterRecommended and not self._filterRecommended.isChecked():
            self._filterRecommended.setChecked(True)
        elif results_filter == RevisionResultsProxyModel.FilterLatest and not self._filterLatest.isChecked():
            self._filterLatest.setChecked(True)
        self._tankRevisionsView.setFilter(results_filter)

    def cwd(self):
        return self._cwd
    def setCwd(self, cwd):
        self._cwd = cwd

    def selectedItem(self):
        try:
            return self._resultsView.selectedIndexes()[0].data(QtCore.Qt.UserRole).toPyObject()
        except IndexError:
            return None
    def setSelectedItem(self, item):
        self._tankFilterView.select(item)
        self._shotgunFilterView.select(item)
        self._resultsView.select(item)

    def closeEvent(self, event):
        self._settings.beginGroup("Browser")
        self._settings.setValue("resultsFilter", int(self.resultsFilter()))
        self._settings.endGroup()
        event.accept()

    @QtCore.pyqtSlot(QtGui.QItemSelection, QtGui.QItemSelection)
    def _setConstraints(self, selected, deselected):
        self._resultsView.setConstraints(self._filterView.selectedObjects())

    def _changeFilter(self):
        if self._filterAll.isChecked():
            self.setResultsFilter(RevisionResultsProxyModel.FilterAll)
        elif self._filterRecommended.isChecked():
            self.setResultsFilter(RevisionResultsProxyModel.FilterRecommended)
        elif self._filterLatest.isChecked():
            self.setResultsFilter(RevisionResultsProxyModel.FilterLatest)

    def _switchFilterPage(self, index):
        self._filterSwitcher.setCurrentIndex(index)

        if index == BrowserDialog.FilterTank:
            self._filterView = self._tankFilterView
        elif index == BrowserDialog.FilterFiles:
            self._filterView = self._fileFilterView
        elif index == BrowserDialog.FilterShotgun:
            self._filterView = self._shotgunFilterView

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def _doubleClicked(self, index):
        self.doubleClicked.emit(index.data(QtCore.Qt.UserRole).toPyObject())

    def setIncludeRevisionTypes(self, include_revision_types):
        self._tankFilterView.model().setIncludeRevisionTypes(include_revision_types)

    def setValidContainerTypes(self, valid_container_types):
        self._tankFilterView.model().setValidContainerTypes(valid_container_types)

    def setValidRevisionTypes(self, valid_revision_types):
        self._tankFilterView.model().setValidRevisionTypes(valid_revision_types)


    @QtCore.pyqtSlot()
    def _search(self):
        pass
        #search_string = self._searchBox.text()

        # sadly, there is not yet full-text search available in the tank api