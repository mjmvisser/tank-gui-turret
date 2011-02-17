from PyQt4 import QtCore, QtGui

import tank

class ContainerTypeComboBox(QtGui.QComboBox):
    def __init__(self, parent, **kwargs):
        super(ContainerTypeComboBox, self).__init__(parent, **kwargs)
        self._validContainerTypes = self.setValidContainerTypes(sorted((tank.find(ct) for ct in tank.list_container_types()), key=lambda l: l.system.name))
        self.currentIndexChanged.connect(self._emitCurrentContainerTypeChanged)

    currentContainerTypeChanged = QtCore.pyqtSignal(object)

    def _emitCurrentContainerTypeChanged(self, index):
        container_type = self.itemData(index).toPyObject()
        self.currentContainerTypeChanged.emit(container_type)

    def validContainerTypes(self):
        return self._validContainerTypes
    def setValidContainerTypes(self, valid_container_types):
        self._validContainerTypes = valid_container_types
        self.clear()
        self.addItem("<none>", None)
        for ct in self._validContainerTypes:
            self.addItem(ct.system.name, ct)

    def currentContainerType(self):
        return self.itemData(self.currentIndex()).toPyObject()
    def setCurrentContainerType(self, container_type):
        if container_type != self.currentContainerType():
            self.setCurrentIndex(self.findData(QtCore.QVariant(container_type)))

class ValidLabelFilterProxyModel(QtGui.QSortFilterProxyModel): #IGNORE:R0904
    def __init__(self, parent, **kwargs):
        self._labelType = None
        self._labelTypes = []
        self._labels = []
        self._containerType = None
        self._validLabels = []
        self._selectionModel = None
        super(ValidLabelFilterProxyModel, self).__init__(parent, **kwargs)

    def setSelectionModel(self, selection_model):
        self._selectionModel = selection_model
        self.invalidateFilter()

    def labelType(self):
        return self._labelType
    def setLabelType(self, label_type):
        self._labelType = label_type
        self._updateValidLabels()
        self.invalidateFilter()

    def labels(self):
        return self._labels
    def setLabels(self, labels):
        self._labels = labels
        self._updateValidLabels()
        self.invalidateFilter()

    def containerType(self):
        return self._containerType
    @QtCore.pyqtSlot(object)
    def setContainerType(self, container_type):
        self._containerType = container_type
        self._labelTypes = sorted((d["type"] for d in self._containerType.label_types.values()))
        self._updateValidLabels()
        self.invalidateFilter()

    def _updateValidLabels(self):
        self._validLabels = tank.label_cross_search(self.labelType(), self.labels(), self.containerType()).fetch_all()

    def filterAcceptsRow(self, source_row, source_parent):
        label = self.sourceModel().index(source_row, 0, source_parent).data(QtCore.Qt.UserRole+1).toPyObject()
        selected_label = self._selectionModel.currentIndex().data(QtCore.Qt.UserRole+1).toPyObject()

        # these rules are damn complicated...

        if label is None:
            # always show "<none>"
            return True
        elif len(self._labels) == 0:
            # show everything if no labels have been selected
            return True
        elif selected_label in self._validLabels:
            # show everything if the selected label is valid
            return True
        else:
            # otherwise only show the label if it is valid
            return label in self._validLabels


class LabelComboBox(QtGui.QComboBox):
    def __init__(self, parent, **kwargs):
        self._containerType = None
        self._labelType = None
        self._labels = []
        self._optional = None
        super(LabelComboBox, self).__init__(parent, sizeAdjustPolicy=QtGui.QComboBox.AdjustToContents, **kwargs)

        model = QtGui.QStandardItemModel(self)

        proxy_model = ValidLabelFilterProxyModel(self)
        proxy_model.setSourceModel(model)
        self.setModel(proxy_model)

        proxy_model.setSelectionModel(self.view().selectionModel())

        self.currentIndexChanged.connect(self._emitCurrentLabelChanged)

    currentLabelChanged = QtCore.pyqtSignal(object)

    def _emitCurrentLabelChanged(self, index):
        label = self.itemData(index, QtCore.Qt.UserRole+1).toPyObject()
        self.currentLabelChanged.emit(label)

    def labelType(self):
        return self._labelType
    def setLabelType(self, label_type, optional=False):
        self._labelType = label_type
        self._optional = optional
        item = QtGui.QStandardItem("<none>")
        self.model().sourceModel().clear()
        self.model().sourceModel().appendRow(item)
        labels = sorted(tank.label_cross_search(self._labelType, self._labels, container_type=self._containerType).fetch_all(), key=lambda l: l.system.name)
        for l in labels:
            item = QtGui.QStandardItem(l.system.name)
            item.setData(l, QtCore.Qt.UserRole+1)
            self.model().sourceModel().appendRow(item)

        self.model().setLabelType(self._labelType)

    def currentLabel(self):
        return self.itemData(self.currentIndex(), QtCore.Qt.UserRole+1).toPyObject()
    def setCurrentLabel(self, label):
        index = self.findData(QtCore.QVariant(label))
        self.setCurrentIndex(index)

    def labels(self):
        return self._labels
    def setLabels(self, labels):
        self._labels = labels
        self.model().setLabels(labels)

    def containerType(self):
        return self._containerType
    def setContainerType(self, container_type):
        self._containerType = container_type
        self.model().setContainerType(container_type)


class LabelsWidget(QtGui.QWidget):
    def __init__(self, parent, **kwargs):
        super(LabelsWidget, self).__init__(parent, **kwargs)
        layout = QtGui.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        self._labelCBs = []
        self._containerType = None
        self._labelTypes = None

    currentLabelsChanged = QtCore.pyqtSignal(object)

    def containerType(self):
        return self._containerType
    def setContainerType(self, container_type):
        self._containerType = container_type
        if self._containerType is not None:
            self._labelTypes = container_type.label_types
        else:
            self._labelTypes = {}

        # clear the existing label widgets
        hlayout = self.layout()
        for item in [hlayout.itemAt(i) for i in range(0, hlayout.count())]:
            if item.widget() is not None:
                item.widget().deleteLater()
            hlayout.removeItem(item)
        self._labelCBs = []

        def sort_by_num_children(left, right):
            num_children_left = len(tank.get_children(left[1]["type"]).fetch_all())
            num_children_right = len(tank.get_children(right[1]["type"]).fetch_all())
            if num_children_left < num_children_right:
                return -1
            elif num_children_left > num_children_right:
                return 1
            else:
                return 0

        # iterate through the valid label types for the current container type
        first = True
        for ln, lt in sorted(self._labelTypes.items(), cmp=sort_by_num_children):
            # create the label type text
            if first:
                first = False
                separator = ""
            else:
                separator = ", "
            l = QtGui.QLabel(separator + ln + "(", self)
            hlayout.addWidget(l)

            # create the label combo box
            cb = LabelComboBox(self)
            cb.setLabelType(lt['type'], lt['is_optional'])
            cb.currentLabelChanged.connect(self._emitCurrentLabelsChanged)
            self.currentLabelsChanged.connect(cb.setLabels)

            hlayout.addWidget(cb)
            self._labelCBs.append(cb)

        self.currentLabelsChanged.emit(self.currentLabels())

    @QtCore.pyqtSlot()
    def _emitCurrentLabelsChanged(self):
        self.currentLabelsChanged.emit(self.currentLabels())

    def currentLabels(self):
        return [cb.currentLabel() for cb in self._labelCBs if cb.currentLabel() is not None]
    def setCurrentLabels(self, labels):
        for cb in self._labelCBs:
            try:
                cb.setCurrentLabel((l for l in labels if cb.labelType() == l.system.type).next())
            except StopIteration:
                cb.setCurrentLabel(None)
        self.currentLabelsChanged.emit(self.currentLabels())


class ContainerEdit(QtGui.QWidget):
    def __init__(self, parent, **kwargs):
        super(ContainerEdit, self).__init__(parent, **kwargs)
        hlayout = QtGui.QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        hlayout.setSpacing(0)

        # container type
        self._containerTypeCB = ContainerTypeComboBox(self)
        self._containerTypeCB.currentContainerTypeChanged.connect(self.setCurrentContainerType)
        hlayout.addWidget(self._containerTypeCB)

        # (
        hlayout.addWidget(QtGui.QLabel("("))

        # optional name
        self._nameCB = QtGui.QComboBox(sizeAdjustPolicy=QtGui.QComboBox.AdjustToContents)
        self._nameCB.setHidden(True)
        hlayout.addWidget(self._nameCB)

        self._comma = QtGui.QLabel(", ")
        self._comma.setHidden(True)
        hlayout.addWidget(self._comma)

        # labels
        self._labelsWidget = LabelsWidget(self)
        hlayout.addWidget(self._labelsWidget)

        # )
        hlayout.addWidget(QtGui.QLabel(")"))

        self.setLayout(hlayout)

    def _updateNameEdit(self):
        current_container_type = self.currentContainerType()
        if current_container_type is None or not current_container_type.properties.use_name:
            self._nameCB.setHidden(True)
        else:
            # populate it with all matching containers
            current_name = self._nameCB.currentText()
            self._nameCB.clear()
            matching_containers = tank.get_children(self.currentContainerType(), ["labels contains %s" % str(l) for l in self._labelsWidget.currentLabels() if l is not None]).fetch_all()
            valid_names = sorted(list(set(c.system.name for c in matching_containers)))
            self._nameCB.addItems(valid_names)
            self._nameCB.setEditText(current_name)
            self._nameCB.setHidden(False)

    currentContainerChanged = QtCore.pyqtSignal(object)

    def validContainerTypes(self):
        return self._containerTypeCB.validContainerTypes()
    def setValidContainerTypes(self, valid_container_types):
        self._containerTypeCB.setValidContainerTypes(sorted((ct for ct in valid_container_types if ct is not None), key=lambda ct: ct.system.name))

    def currentContainerType(self):
        return self._containerTypeCB.currentContainerType()
    def setCurrentContainerType(self, container_type):
        self._containerTypeCB.setCurrentContainerType(container_type)
        self._labelsWidget.setContainerType(container_type)
        self._updateNameEdit()
        self.currentContainerChanged.emit(self.currentContainer())

    def currentName(self):
        try:
            if self._containerTypeCB.currentContainerType().properties.use_name:
                return str(self._nameCB.currentText())
            else:
                return None
        except AttributeError:
            return None
    def setCurrentName(self, name):
        try:
            if self._containerTypeCB.currentContainerType().properties.use_name:
                self._nameCB.setCurrentIndex(self._nameCB.findText(name))
        except:
            pass
        self.currentContainerChanged.emit(self.currentContainer())

    def currentContainer(self):
        if self.currentContainerType() is None:
            return None
        else:
            try:
                return tank.find_ex(self.currentContainerType(), name=self.currentName(), labels=self._labelsWidget.currentLabels())
            except (tank.common.TankNotFound, tank.common.TankError):
                return None
    def setCurrentContainer(self, container):
        if container is None:
            self.setCurrentContainerType(None)
            self.setCurrentName(None)
            self._labelsWidget.setCurrentLabels([])
        else:
            self.setCurrentContainerType(container.system.type)
            self.setCurrentName(container.system.name)
            self.labelsWidget.setCurrentLabels(container.labels.values())
        self.currentContainerChanged.emit(container)
        self._updateNameEdit()


if __name__ == "__main__":
    qapp = QtGui.QApplication([])

    w = QtGui.QWidget()
    lt = QtGui.QHBoxLayout(w)

    c = ContainerEdit(w)
    c.setValidContainerTypes([tank.find(ct) for ct in tank.list_container_types()])
    lt.addWidget(c)

#    ccb = ContainerTypeComboBox(w)
#    lt.addWidget(ccb)

#    lw = LabelsWidget(w)
#    lt.addWidget(lw)

#    ccb.currentContainerTypeChanged.connect(lw.setContainerType)

    w.show()

    qapp.exec_()
