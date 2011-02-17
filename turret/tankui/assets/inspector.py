from PyQt4 import QtCore, QtGui

from ..browser import BrowserDialog #IGNORE:F0401
from ..revision import RevisionTypeComboBox, VersionComboBox #IGNORE:F0401
from .model import Columns

class InspectorModel(QtCore.QAbstractTableModel): #IGNORE:R0904
    def __init__(self, parent=None, **kwargs):
        self._sourceModel = None
        self._selectionModel = None
        self._selected = []
        self._current = []
        super(InspectorModel, self).__init__(parent, **kwargs)

    def sourceModel(self):
        return self._sourceModel
    def setSourceModel(self, model):
        self.beginResetModel()
        self._sourceModel = model
        self.endResetModel()
        self._sourceModel.modelReset.connect(self.refresh)

    def selectionModel(self):
        return self._selectionModel
    def setSelectionModel(self, selectionModel):
        self.beginResetModel()
        self._selectionModel = selectionModel
        self._selectionModel.selectionChanged.connect(self.changeSelection)
        self._selectionModel.currentChanged.connect(self.changeCurrent)
        self.endResetModel()

    def refresh(self):
        self.beginResetModel()
        self._selected = []
        self._current = []
        self.endResetModel()

    @QtCore.pyqtSlot(QtCore.QModelIndex, QtCore.QModelIndex)
    def changeSelection(self, selected, deselected):
        # reset the model, the view will refresh itself using the updated selection
        self.beginResetModel()
        self._selected = self._selectionModel.selectedIndexes()
        self.endResetModel()

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def changeCurrent(self, sourceIndex):
        self.beginResetModel()
        self._current = [self._sourceModel.index(sourceIndex.row(), col, self._sourceModel.parent(sourceIndex)) for col in range(0, self._sourceModel.columnCount())]
        self.endResetModel()

    def columnCount(self, parent=QtCore.QModelIndex()): #IGNORE:R0201
        return 2

    def rowCount(self, parent=QtCore.QModelIndex()):
        try:
            return self._sourceModel.columnCount()-1
        except AttributeError:
            return 0

    def flags(self, index=QtCore.QModelIndex()):
        flags = super(InspectorModel, self).flags(index)

        flags &= ~QtCore.Qt.ItemIsSelectable

        if len(self._current) > 0:
            if index.column() == 0:
                flags &= ~(QtCore.Qt.ItemIsEnabled|QtCore.Qt.ItemIsEditable)
            elif index.column() == 1:
                if self._current[index.row()+1].flags() & QtCore.Qt.ItemIsEditable:
                    flags |= QtCore.Qt.ItemIsEditable
                else:
                    flags &= ~(QtCore.Qt.ItemIsEditable)

        return flags

    def data(self, index, role=QtCore.Qt.DisplayRole):
        row = index.row()
        col = index.column()
        if col == 0:
            if role == QtCore.Qt.DisplayRole:
                result = self._sourceModel.headerData(row+1, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole).toString() + ":"
            else:
                result = None
        else:
            if role in (QtCore.Qt.DisplayRole, QtCore.Qt.EditRole, QtCore.Qt.UserRole):
                try:
                    result = self._current[row+1].data(role).toPyObject()
                except IndexError:
                    result = None
            elif role == QtCore.Qt.BackgroundRole:
                result = QtGui.QApplication.palette().brush(QtGui.QPalette.Base)
            else:
                result = None

        return QtCore.QVariant(result)

    def setData(self, index, value, role):
        if index.column() == 1 and role == QtCore.Qt.EditRole:
            for current_index in self._current + self._selected:
                if current_index.column()-1 == index.row():
                    self._sourceModel.setData(current_index, value, QtCore.Qt.EditRole)
            self.dataChanged.emit(index, index)
            return True
        else:
            return False

class InspectorHeader(QtGui.QWidget):
    def __init__(self, parent, **kwargs):
        self._selected = []
        self._current = None
        self._model = None
        self._selectionModel = None
        super(InspectorHeader, self).__init__(parent, **kwargs)

        pal = self.palette()
        pal.setColor(QtGui.QPalette.Base, QtGui.QApplication.palette().color(QtGui.QPalette.Base))
        self.setPalette(pal)

        layout = QtGui.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._nodeLabel = QtGui.QLabel(self)
        layout.addWidget(self._nodeLabel)

        self._nodeEdit = QtGui.QLineEdit(self)
        self._nodeEdit.returnPressed.connect(self._renameCurrent)
        layout.addWidget(self._nodeEdit, 1)

        self._nodeSelector = QtGui.QComboBox(self)
        self._nodeSelector.currentIndexChanged[int].connect(self._changeCurrent)
        layout.addWidget(self._nodeSelector, 1)

    ## SIGNALS
    currentChanged = QtCore.pyqtSignal(QtCore.QModelIndex)

    def setModel(self, model):
        self._model = model

    def setSelectionModel(self, selectionModel):
        self._selectionModel = selectionModel
        self._selectionModel.selectionChanged.connect(self.changeSelection)
        self._selectionModel.currentChanged.connect(self.changeCurrent)

    ## SLOTS
    @QtCore.pyqtSlot(QtGui.QItemSelection, QtGui.QItemSelection)
    def changeSelection(self, selected, deselected):
        self._selected = [index for index in self._selectionModel.selectedIndexes() if index.column() == 0]
        self._nodeSelector.clear()
        for index in self._selected:
            self._nodeSelector.addItem(self._model.data(index).toString(), QtCore.QVariant(index))
        self._update()

    @QtCore.pyqtSlot(QtCore.QModelIndex)
    def changeCurrent(self, index):
        col0_index = self._model.index(index.row(), 0, self._model.parent(index))
        self._nodeEdit.setText(self._model.data(col0_index).toString())
        self._current = col0_index
        self._update()

    @QtCore.pyqtSlot()
    def _renameCurrent(self):
        self._model.setData(self._current, str(self._nodeEdit.text()))

    @QtCore.pyqtSlot(int)
    def _changeCurrent(self, i):
        if i != -1:
            index = self._nodeSelector.itemData(i).toPyObject()
            self._selectionModel.setCurrentIndex(index, QtGui.QItemSelectionModel.Current)

    def _update(self):
        if len(self._selected) > 1:
            self._nodeLabel.setText("%d nodes selected:" % len(self._selected))
            self._nodeSelector.setVisible(True)
            self._nodeEdit.setVisible(False)
        else:
            self._nodeLabel.setText("Node:")
            self._nodeSelector.setVisible(False)
            self._nodeEdit.setVisible(True)


class InspectorView(QtGui.QAbstractItemView): #IGNORE:R0904
    def __init__(self, parent=None, **kwargs):
        super(InspectorView, self).__init__(parent, frameShape=QtGui.QFrame.NoFrame,
                                            editTriggers=QtGui.QAbstractItemView.SelectedClicked,
                                            **kwargs)

        pal = self.palette()
        pal.setColor(QtGui.QPalette.Base, self.palette().color(QtGui.QPalette.Window))
        self.setPalette(pal)

        self._header = InspectorHeader(self.viewport())
        line = QtGui.QFrame(self.viewport(), frameShape=QtGui.QFrame.HLine, objectName="line")
        self._table = QtGui.QTableView(self.viewport(), frameShape=QtGui.QFrame.NoFrame)
        self._table.horizontalHeader().pyqtConfigure(stretchLastSection=True)
        pal = self._table.palette()
        pal.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, pal.color(QtGui.QPalette.Normal, QtGui.QPalette.Text))
        self._table.setPalette(pal)
        layout = QtGui.QVBoxLayout(self.viewport())
        layout.addWidget(self._header)
        layout.addWidget(line)
        layout.addWidget(self._table, 100)
        self.viewport().setLayout(layout)
        self._table.horizontalHeader().setVisible(False)
        self._table.verticalHeader().setVisible(False)

        self._inspectorModel = InspectorModel(self)
        self._table.setModel(self._inspectorModel)
        self._inspectorModel.modelReset.connect(self._currentChanged)

        delegate = InspectorItemDelegate()
        self._table.setItemDelegate(delegate)

    def resizeEvent(self, event):
        super(InspectorView, self).resizeEvent(event)
        self._table.resizeRowsToContents()

    @QtCore.pyqtSlot()
    def _currentChanged(self):
        self._table.resizeRowsToContents()

    def model(self):
        return self._sourceModel
    def setModel(self, model):
        self._inspectorModel.setSourceModel(model)
        self._header.setModel(model)
        self._table.resizeColumnToContents(0)

    def setSelectionModel(self, selectionModel):
        self._inspectorModel.setSelectionModel(selectionModel)
        self._header.setSelectionModel(selectionModel)

    def verticalOffset(self):
        return self._table.verticalOffset()

    def horizontalOffset(self):
        return self._table.horizontalOffset()

    def indexAt(self, point):
        return self._table.indexAt(point)

    def visualRect(self, index):
        return self._table.visualRect(index)

    def moveCursor(self, cursorAction, modifiers):
        return self._table.moveCursor(cursorAction, modifiers)

    def scrollTo(self, index, hint=QtGui.QAbstractItemView.EnsureVisible):
        return self._table.scrollTo(index, hint)

    def visualRegionForSelection(self, selection):
        return self._table.visualRegionForSelection(selection)

    def copy(self):
        if self.selectionModel():
            index = self.selectionModel().currentIndex()
            if index:
                text = index.data().toString()
                QtGui.QApplication.clipboard().setText(text, QtGui.QClipboard.Clipboard)

    def keyPressEvent(self, event):
        if event.matches(QtGui.QKeySequence.Copy):
            self.copy()
        else:
            super(InspectorView, self).keyPressEvent(event)


class InspectorItemDelegate(QtGui.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(InspectorItemDelegate, self).__init__(parent)
        self._pencilIcon = QtGui.QIcon(":images/pencil.png")

    def initStyleOption(self, option, index):
        super(InspectorItemDelegate, self).initStyleOption(option, index)
        column = index.row() + 1
        if column == Columns.Path:
            # override the elideMode to put the ellipsis on the left for the PATH so
            # the filename is visible
            option.textElideMode = QtCore.Qt.ElideLeft

    def createEditor(self, parent, option, index):
        column = index.row() + 1
        if column == Columns.Container:
            editor = BrowserDialog(parent, modal=True)
            editor.setIncludeRevisionTypes(False)
            editor.setBrowseType(BrowserDialog.BrowseContainers)
            return editor
        elif column == Columns.Revision:
            editor = BrowserDialog(parent, modal=True)
            editor.setBrowseType(BrowserDialog.BrowseRevisions)
            return editor
        elif column == Columns.RevisionType:
            editor = RevisionTypeComboBox(parent)
            return editor
        elif column == Columns.Version:
            editor = VersionComboBox(parent)
            return editor
        else:
            return super(InspectorItemDelegate, self).createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        column = index.row() + 1
        if column == Columns.Container:
            current_container = index.data(QtCore.Qt.EditRole).toPyObject()
            editor.setSelectedItem(current_container)
        if column == Columns.Revision:
            current_revision = index.data(QtCore.Qt.EditRole).toPyObject()
            valid_revision_types = index.model().data(index, QtCore.Qt.UserRole).toPyObject().valid_revision_types
            editor.setValidRevisionTypes(valid_revision_types)
            editor.setSelectedItem(current_revision)
        elif column == Columns.RevisionType:
            current_revision_type = index.data(QtCore.Qt.EditRole).toPyObject()
            valid_revision_types = index.data(QtCore.Qt.UserRole).toPyObject().valid_revision_types
            editor.setValidRevisionTypes(valid_revision_types)
            editor.setCurrentRevisionType(current_revision_type)
        elif column == Columns.Version:
            current_revision = index.data(QtCore.Qt.EditRole).toPyObject()
            editor.setRevision(current_revision)
        else:
            super(InspectorItemDelegate, self).setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        column = index.row() + 1
        if column == Columns.Container:
            model.setData(index, editor.selectedItem(), QtCore.Qt.EditRole)
        elif column == Columns.Revision:
            model.setData(index, editor.selectedItem(), QtCore.Qt.EditRole)
        elif column == Columns.RevisionType:
            model.setData(index, editor.currentRevisionType(), QtCore.Qt.EditRole)
        elif column == Columns.Version:
            model.setData(index, editor.version(), QtCore.Qt.EditRole)
        else:
            super(InspectorItemDelegate, self).setModelData(editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        column = index.row() + 1
        if column in (Columns.Container, Columns.Revision):
            pass
        else:
            editor.setGeometry(option.rect)

    def paint(self, painter, option, index):
        super(InspectorItemDelegate, self).paint(painter, option, index)
        if index.flags() & QtCore.Qt.ItemIsEditable:
            self._pencilIcon.paint(painter, option.rect, QtCore.Qt.AlignRight|QtCore.Qt.AlignVCenter)
