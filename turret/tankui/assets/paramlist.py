from PyQt4 import QtCore, QtGui

import functools

from ...tankscene import Param #IGNORE:F0401

from .revisionlist import RevisionListView
from .nodelist import NodeListView

class ParamDialog(QtGui.QDialog):
    def __init__(self, parent=None, **kwargs):
        if parent is not None:
            super(ParamDialog, self).__init__(parent, **kwargs)
        else:
            super(ParamDialog, self).__init__(**kwargs)

        self._values = {}
        self._params = []

        self.setMinimumWidth(400)

    def values(self):
        return self._values

    def setParams(self, params):
        if self.layout() is not None:
            self.layout().deleteLater()

        layout = QtGui.QGridLayout(self)

        self._params = params
        self._values = {}

        for i, param in enumerate(self._params):
            label = QtGui.QLabel(self, text=param.label+":")
            widget = None
            layout.addWidget(label, i, 0)
            if param.type == Param.Text:
                widget = QtGui.QLineEdit(self)
                widget.setText(param.value)
                widget.textEdited.connect(functools.partial(self._updateParam, index=i))
            elif param.type == Param.RevisionList:
                widget = RevisionListView(self)
                widget.setRevisions(param.value)
                widget.revisionsChanged.connect(functools.partial(self._updateParam, index=i))
            elif param.type == Param.Boolean:
                widget = QtGui.QCheckBox(self)
                widget.setCheckState(QtCore.Qt.Checked if param.value else QtCore.Qt.Unchecked)
                widget.stateChanged.connect(functools.partial(self._updateParam, index=i))
            elif param.type == Param.Integer:
                widget = QtGui.QSpinBox(self)
                widget.setValue(param.value)
                widget.valueChanged[(int)].connect(functools.partial(self._updateParam, index=i))
            elif param.type == Param.NodeList:
                widget = NodeListView(self)
                widget.setRoot(param.node)
                widget.checkedNodesChanged.connect(functools.partial(self._updateParam, index=i))
                widget.setAllChecked()

            if widget is not None:
                layout.addWidget(widget, i, 1)

        buttons = QtGui.QDialogButtonBox(self)
        buttons.setStandardButtons(QtGui.QDialogButtonBox.Ok|QtGui.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons, len(self._params), 0, 1, 2)

        self.setLayout(layout)

    @QtCore.pyqtSlot(int, object)
    def _updateParam(self, value, index):
        param = self._params[index]
        if param.type == Param.Text:
            self._values[param.name] = str(value)
        elif param.type == Param.RevisionList:
            self._values[param.name] = value
        elif param.type == Param.Boolean:
            self._values[param.name] = (value == QtCore.Qt.Checked)
        elif param.type == Param.Integer:
            self._values[param.name] = value
        elif param.type == Param.NodeList:
            self._values[param.name] = value
