from PyQt4 import QtCore, QtGui

from ...tankscene import Param #IGNORE:F0401
from .model import Columns
from ..browser import BrowserDialog #IGNORE:F0401
from .paramlist import ParamDialog

class AssetsView(QtGui.QTreeView):
    # signals
    selectionModified = QtCore.pyqtSignal(QtGui.QItemSelection, QtGui.QItemSelection)

    def __init__(self, parent, **kwargs):
        super(AssetsView, self).__init__(parent,
                                         sortingEnabled=True,
                                         selectionMode=QtGui.QAbstractItemView.ExtendedSelection,
                                         **kwargs)

        self._settings = QtCore.QSettings()

        for column, width in {Columns.Node: 350,
                              Columns.RevisionType: 100,
                              Columns.Version: 120}.items():
            self.setColumnWidth(column, width)

    @QtCore.pyqtSlot(QtGui.QItemSelection, QtGui.QItemSelection)
    def selectionChanged(self, selected, deselected):
        super(AssetsView, self).selectionChanged(selected, deselected)
        self.updateActions()
        self.selectionModified.emit(selected, deselected)

    #def fitColumnTypeToContents(self):
    #    for column in range(0, self.model().model.columnCount()):
    #        self.resizeColumnToContents(column)

    def setModel(self, model):
        super(AssetsView, self).setModel(model)
        self._initView()

    def _initView(self):
        for column in range(0, Columns.NumColumns):
            # show by default
            default = column in (Columns.Node, Columns.ContainerName, Columns.RevisionType, Columns.Version)
            self.setColumnHidden(column, not self._settings.value("AssetsView/showColumn%d" % column, default).toBool())

        # expand the root node
        self.expand(self.model().index(0, 0))

        for column in range(0, self.model().columnCount()):
            self.resizeColumnToContents(column)

        self._createHeaderActions()

    def _createHeaderActions(self):
        assert self.model()
        for action in self.header().actions():
            self.header().removeAction(action)

        for column in range(0, self.model().columnCount()):
            text = self.model().sourceModel().headerData(column, QtCore.Qt.Horizontal, QtCore.Qt.DisplayRole).toString()
            action = QtGui.QAction(self.header().viewport())
            action.setCheckable(True)
            action.setChecked(not self.isColumnHidden(column))
            action.setText(text)
            action.setData(QtCore.QVariant(column))
            action.triggered.connect(lambda checked, column=column: self.setColumnHidden(column, not checked))
            self.header().addAction(action)
        self.header().setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

    def setColumnHidden(self, column, hide):
        super(AssetsView, self).setColumnHidden(column, hide)
        self._settings.setValue("AssetsView/showColumn%d" % column, not hide)

    def createActions(self):
        for action in self.actions():
            self.removeAction(action)

        # add automatically generated actions defined by the scene
        # use a signal mapper to deliver different actions to the same handler with a string parameter
        mapper = QtCore.QSignalMapper(self)
        for action_id, action_name in self.model().sourceModel().root().action_names.items():
            # map each action in the scene to a action object
            action = QtGui.QAction(action_name, self, enabled=False, objectName=action_id)
            mapper.setMapping(action, action_id)
            action.triggered[()].connect(mapper.map)
            self.addAction(action)
        mapper.mapped[QtCore.QString].connect(self.executeAction)

    @QtCore.pyqtSlot(str)
    def executeAction(self, action_name):
        # use the scene's parameters as a template
        # we can assume all nodes have the same parameter signatures
        action_title = self.model().sourceModel().root().action_names[str(action_name)]

        # get actions for selected items
        actions = [index.data(QtCore.Qt.UserRole).toPyObject().actions[str(action_name)] for index in self.selectionModel().selectedIndexes() if index.column() == 0]

        # use the first item as the template
        params = actions[0].params

        param_values = {}

        # Does the action needs a parameter? (container or revision)
        if len(params) == 1 and params[0].type in (Param.Revision, Param.Container):
            # if we have only one selection, pass it to the browser
            # because we can have several indexes, but with the same node...
            first_selected_node = (index.data(QtCore.Qt.UserRole).toPyObject() for index in self.selectionModel().selectedIndexes()).next()
            first_selected_item = first_selected_node.container

            # grab the revision or container from a browser
            browse_type = {Param.Revision: BrowserDialog.BrowseRevisions,
                           Param.Container: BrowserDialog.BrowseContainers}[params[0].type]
            dlg = BrowserDialog(self.viewport(), modal=True)
            dlg.setWindowTitle(action_title)
            dlg.setBrowseType(browse_type)
            dlg.setSelectedItem(first_selected_item)
            if dlg.exec_() == QtGui.QDialog.Accepted:
                obj = dlg.selectedItem()
                param_values[params[0].name] = obj
            else:
                return

        elif len(params) > 0:
            dlg = ParamDialog(self.viewport())
            dlg.setWindowTitle(action_title)
            dlg.setParams(params)

            if dlg.exec_() == QtGui.QDialog.Accepted:
                param_values.update(dlg.values())
            else:
                return


        for action in actions:
            # set parameters
            for p in action.params:
                # only set the param if the key exists
                # if the key does not exist, we don't want to change the parameter's default
                if param_values.has_key(p.name):
                    p.value = param_values[p.name]

            try:
                QtGui.QApplication.setOverrideCursor(QtCore.Qt.BusyCursor)
                # run the action
                action.execute()
            finally:
                QtGui.QApplication.restoreOverrideCursor()


#        # Does the action needs a parameter? (container or revision)
#        if len(params) == 1 and params[0].type in (Param.Revision, Param.Container):
#            selected_item = None
#            # if we have only one selection, pass it to the browser
#            # because we can have several indexes, but with the same node...
#            node_set = set([index.data(QtCore.Qt.UserRole).toPyObject() for index in self.selectionModel().selectedIndexes()])
#            if len(node_set) == 1:
#                selected_node = node_set.pop()
#                selected_item = selected_node.container
#
#            # grab the revision or container from a browser
#            browse_type = {Param.Revision: BrowserDialog.BrowseRevisions,
#                           Param.Container: BrowserDialog.BrowseContainers}[params[0].type]
#            dlg = BrowserDialog(self.viewport(), modal=True)
#            dlg.setBrowseType(browse_type)
#            dlg.setSelectedItem(selected_item)
#            if dlg.exec_() == QDialog.Accepted:
#                obj = dlg.selectedItem()
#                param_values[params[0].name] = obj
#        # also, we handle a single text item
#        elif len(params) == 1 and params[0].type == Param.Text:
#            description, ok = QInputDialog.getText(self.viewport(), params[0].title, params[0].label, QLineEdit.Normal, params[0].value)
#            if ok:
#                param_values[params[0].name] = str(description)
#        # TODO: arbitrary parameter lists

#        # get actions for selected item
#        actions = set(index.data(QtCore.Qt.UserRole).toPyObject().actions[str(action_name)] for index in self.selectionModel().selectedIndexes())
#
#        for action in actions:
#            # set parameters
#            for p in action.params:
#                # only set the param if the key exists
#                # if the key does not exist, we don't want to change the parameter's default
#                if param_values.has_key(p.name):
#                    p.value = param_values[p.name]
#
#            # run the action
#            action.execute()

    def updateActions(self):
        selection = self.selectionModel().selection()
        indexes = selection.indexes()

        for action in self.actions():
            if action.objectName() == "edit_selected":
                action.setEnabled(len(selection) > 0)
            else:
                action_id = str(action.objectName())
                if len(selection) > 0:
                    supported = True
                    for index in indexes:
                        node = index.data(QtCore.Qt.UserRole).toPyObject()
                        if not node.actions.has_key(action_id) or node.actions[action_id].func is None:
                            supported = False
                            break
                else:
                    supported = False
                action.setEnabled(supported)

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
            super(AssetsView, self).keyPressEvent(event)

