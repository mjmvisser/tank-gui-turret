from PyQt4 import QtCore, QtGui

ANIMATION_DURATION_MSEC = 150

#import sys; sys.path.append("/Developer/Eclipse/plugins/org.python.pydev.debug_1.6.1.2010080312/pysrc/")
#import pydevd; pydevd.settrace(suspend=False)

class FilterViewGrip(QtGui.QWidget):
    def __init__(self, parent, **kwargs):
        super(FilterViewGrip, self).__init__(parent, **kwargs)
        self._originalXLocation = -1
        self.setCursor(QtCore.Qt.SplitHCursor)

    gripMoved = QtCore.pyqtSignal(int)

    def moveGrip(self, offset):
        parentWidget = self.parent()

        # first resize the parent
        oldWidth = parentWidget.width()
        newWidth = oldWidth
        if self.isRightToLeft():
            newWidth -= offset
        else:
            newWidth += offset
        newWidth = max(parentWidget.minimumWidth(), newWidth)
        parentWidget.resize(newWidth, parentWidget.height())

        # Then have the view move the widget
        realOffset = parentWidget.width() - oldWidth
        oldX = parentWidget.x()
        if realOffset != 0:
            self.gripMoved.emit(realOffset)
        if self.isRightToLeft():
            realOffset = -1 * (oldX - parentWidget.x())
        return realOffset


    def paintEvent(self, event):
        super(FilterViewGrip, self).paintEvent(event)
        painter = QtGui.QPainter(self)
        opt = QtGui.QStyleOption()
        opt.initFrom(self)
        self.style().drawControl(QtGui.QStyle.CE_ColumnViewGrip, opt, painter, self)
        event.accept()

    def mouseDoubleClickEvent(self, event):
        parentWidget = self.parent()
        offset = parentWidget.sizeHint().width() - parentWidget.width()
        if self.isRightToLeft():
            offset *= -1
        self.moveGrip(offset)
        event.accept()

    def mousePressEvent(self, event):
        self._originalXLocation = event.globalX()
        event.accept()

    def mouseMoveEvent(self, event):
        offset = event.globalX() - self._originalXLocation
        self._originalXLocation = self.moveGrip(offset) + self._originalXLocation
        event.accept()

    def mouseReleaseEvent(self, event):
        self._originalXLocation = -1
        event.accept()


class FilterHeader(QtGui.QHeaderView):
    def __init__(self, view, parent=None, **kwargs):
        super(FilterHeader, self).__init__(QtCore.Qt.Horizontal, parent, **kwargs)
        self._view = view

    closed = QtCore.pyqtSignal("const QModelIndex&")

    def paintEvent(self, event):
        super(FilterHeader, self).paintEvent(event)

        # draw the icon at right edge of the column
        painter = QtGui.QPainter(self.viewport())
        view_size = self.viewport().size()

        icon = self.style().standardIcon(QtGui.QStyle.SP_TitleBarCloseButton)
        actual_size = icon.actualSize(QtCore.QSize(view_size.height(), view_size.height()))
        pixmap = icon.pixmap(actual_size)
        painter.drawPixmap(view_size.width()-actual_size.width()-1, (view_size.height()-actual_size.height())/2+1, pixmap)

    def paintSection(self, painter, rect, logicalIndex):
        if not rect.isValid():
            return

        # get the state of the section
        opt = QtGui.QStyleOptionHeader()
        self.initStyleOption(opt)
        state = QtGui.QStyle.State_None
        if self.isEnabled():
            state |= QtGui.QStyle.State_Enabled
        if self.window().isActiveWindow():
            state |= QtGui.QStyle.State_Active

        if self.isSortIndicatorShown() and self.sortIndicatorSection() == logicalIndex:
            opt.sortIndicator = QtGui.QStyleOptionHeader.SortDown if self.sortIndicatorOrder() == QtCore.Qt.AscendingOrder else QtGui.QStyleOptionHeader.SortUp

        # setup the style options structure
        opt.rect = rect
        opt.section = logicalIndex
        opt.state |= state
        opt.textAlignment = QtCore.Qt.AlignLeft

        opt.iconAlignment = QtCore.Qt.AlignVCenter|QtCore.Qt.AlignLeft

        opt.text = self.model().data(self.rootIndex(), QtCore.Qt.DisplayRole).toString()
        if self.textElideMode() != QtCore.Qt.ElideNone:
            opt.text = opt.fontMetrics.elidedText(opt.text, self.textElideMode(), rect.width() - 4)

        icon = self.model().data(self.rootIndex(), QtCore.Qt.DecorationRole)
        try:
            if icon.canConvert(QtCore.QVariant.Icon):
                opt.icon = icon.convert(QtCore.QVariant.Icon)
            elif icon.canConvert(QtCore.QVariant.Pixmap):
                opt.icon = icon.convert(QtCore.QVariant.Pixmap)
        except:
            pass
        foregroundBrush = self.model().data(self.rootIndex(), QtCore.Qt.ForegroundRole)
        if foregroundBrush.canConvert(QtCore.QVariant.Brush):
            opt.palette.setBrush(QtGui.QPalette.ButtonText, foregroundBrush.convert(QtCore.QVariant.Brush))

        oldBO = painter.brushOrigin()
        backgroundBrush = self.model().data(self.rootIndex(), QtCore.Qt.BackgroundRole)
        if backgroundBrush.canConvert(QtCore.QVariant.Brush):
            opt.palette.setBrush(QtGui.QPalette.Button, backgroundBrush.convert(QtCore.QVariant.Brush))
            opt.palette.setBrush(QtGui.QPalette.Window, backgroundBrush.convert(QtCore.QVariant.Brush))
            painter.setBrushOrigin(opt.rect.topLeft())

        self.style().drawControl(QtGui.QStyle.CE_Header, opt, painter, self)

        painter.setBrushOrigin(oldBO)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self._pressPos = event.pos()
            event.accept()
        else:
            super(FilterHeader, self).mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            view_size = self.viewport().size()

            icon = self.style().standardIcon(QtGui.QStyle.SP_TitleBarCloseButton)
            actual_size = icon.actualSize(QtCore.QSize(view_size.height(), view_size.height()))
            pixmap = icon.pixmap(actual_size)
            target = QtCore.QRect(view_size.width()-actual_size.width()-1, (view_size.height()-actual_size.height())/2+1, pixmap.width(), pixmap.height())

            if target.contains(self._pressPos) and target.contains(event.pos()):
                # send the "closed" signal
                self.closed.emit(self._view.rootIndex())
            event.accept()
        else:
            super(FilterHeader, self).mouseReleaseEvent(event)


class FilterView(QtGui.QAbstractItemView):
    def __init__(self, parent=None, **kwargs):
        super(FilterView, self).__init__(parent,
                                         selectionMode=QtGui.QAbstractItemView.MultiSelection,
                                         editTriggers=QtGui.QAbstractItemView.NoEditTriggers,
                                         **kwargs)

        self._currentAnimation = QtCore.QPropertyAnimation()
        self._columns = []
        self._showResizeGrips = True
        self._offset = 0

        self.setTextElideMode(QtCore.Qt.ElideMiddle)

        self._currentAnimation.setDuration(ANIMATION_DURATION_MSEC)
        self._currentAnimation.setTargetObject(self.horizontalScrollBar())
        self._currentAnimation.setPropertyName("value")
        self._currentAnimation.setEasingCurve(QtCore.QEasingCurve.InOutQuad)

        self.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        self._label = QtGui.QLabel("", self.viewport())

        self._doLayout()
        self._updateScrollbars()


    # properties
    def resizeGripsVisible(self):
        return self._showResizeGrips
    def setResizeGripsVisible(self, visible):
        if self._showResizeGrips == visible:
            return
        self._showResizeGrips = visible
        for view in self._columns:
            if visible:
                grip = FilterViewGrip(view)
                view.setCornerWidget(grip)
                grip.gripMoved.connect(self._gripMoved)
            else:
                widget = view.cornerWidget()
                view.setCornerWidget(0)
                widget.deleteLater()

    # signals
    updatePreviewWidget = QtCore.pyqtSignal("const QModelIndex&")

    def setModel(self, model):
        if model == self.model():
            return
        self._closeColumns()
        super(FilterView, self).setModel(model)

    def setRootIndex(self, index):
        if self.model() is None:
            return
        self._closeColumns()
        assert len(self._columns) == 0

        if self.model().canFetchMore(index):
            self.model().fetchMore(index)

        self._label.setText(self.model().data(index).toString())

        super(FilterView, self).setRootIndex(index)
        self._updateScrollbars()
        self.updateActions()

    def updateActions(self):
        for action in self.actions():
            self.removeAction(action)

        for row in range(0, self.model().rowCount(self.rootIndex())):
            child = self.model().index(row, 0, self.rootIndex())
            action = QtGui.QAction(self.model().data(child).toString(), self, checkable=True, checked=False)#, toggled=self.toggleFilter)
            # FIXME: lambda is to pass action to toggleFilter as self.sender() is broken until later 4.7
            action.toggled.connect(lambda checked, action=action: self.toggleFilter(checked, action))
            action.setData(row)
            self.addAction(action)

    def toggleFilter(self, checked, action):
        #action = self.sender()
        command = QtGui.QItemSelectionModel.Select if checked else QtGui.QItemSelectionModel.Deselect
        # update the selection, which will be handled by selectionChanged and add or remove
        # columns appropriately
        row = action.data().toPyObject()

        index = self.model().index(row, 0, self.rootIndex())

        self.selectionModel().select(index, command)

    def isIndexHidden(self, index):
        return False

    def indexAt(self, point):
        for view in self._columns:
            topLeft = view.frameGeometry().topLeft()
            adjustedPoint = QtCore.QPoint(point.x() - topLeft.x(), point.y() - topLeft.y())
            index = view.indexAt(adjustedPoint)
            if index.isValid():
                return index
        return QtCore.QModelIndex()

    def visualRect(self, index):
        if not index.isValid():
            return QtCore.QRect()

        for view in self._columns:
            rect = view.visualRect(index)
            if not rect.isNull():
                rect.translate(view.frameGeometry().topLeft())
                return rect

        return QtCore.QRect()

    def scrollContentsBy(self, dx, dy):
        if len(self._columns) == 0 or dx == 0:
            return

        dx = -dx if self.isRightToLeft() else dx
        for view in self._columns:
            view.move(view.x() + dx, 0)
        self._label.move(self._label.x() + dx, self._label.y())
        self._offset += dx
        super(FilterView, self).scrollContentsBy(dx, dy)

    def scrollTo(self, index, hint=QtGui.QAbstractItemView.EnsureVisible):
        if not index.isValid() or len(self._columns) == 0:
            return

        if self._currentAnimation.state() == QtCore.QPropertyAnimation.Running:
            return

        self._currentAnimation.stop()

        # Find the left edge of the column that contains index
        leftEdge = 0
        for currentColumn in self._columns:
            if index == currentColumn.rootIndex():
                break
            # check children as well
            for row in range(0, self.model().rowCount(index)):
                if index == self.model().index(row, 0, index):
                    break
            leftEdge += currentColumn.width()

        # Find the width of what we want to show (i.e. the right edge)
        visibleWidth = currentColumn.width()

        rightEdge = leftEdge + visibleWidth
        if self.isRightToLeft():
            leftEdge = self.viewport().width() - leftEdge
            rightEdge = leftEdge - visibleWidth
            rightEdge, leftEdge = leftEdge, rightEdge

        # If it is already visible don't animate
        if leftEdge > -self.horizontalOffset() and \
           rightEdge <= ( -self.horizontalOffset() + self.viewport().size().width()) and \
           index != currentColumn.rootIndex():
            currentColumn.scrollTo(index)
            return

        newScrollbarValue = 0
        if self.isRightToLeft():
            if leftEdge < 0:
                # scroll to the right
                newScrollbarValue = self.viewport().size().width() - leftEdge
            else:
                # scroll to the left
                newScrollbarValue = rightEdge + self.horizontalOffset()
        else:
            if leftEdge > -self.horizontalOffset():
                # scroll to the right
                newScrollbarValue = rightEdge - self.viewport().size().width()
            else:
                # scroll to the left
                newScrollbarValue = leftEdge

        self._currentAnimation.setEndValue(newScrollbarValue)
        self._currentAnimation.start()

    def moveCursor(self, cursorAction, modifiers):
        # the child views which have focus get to deal with this first and if
        # they don't accept it then it comes up this view and we only grip left/right
        if not self.model():
            return QtCore.QModelIndex()

        current = self.currentIndex()
        if self.isRightToLeft():
            if cursorAction == QtGui.QAbstractItemView.MoveLeft:
                cursorAction = QtGui.QAbstractItemView.MoveRight
            elif cursorAction == QtGui.QAbstractItemView.MoveRight:
                cursorAction = QtGui.QAbstractItemView.MoveLeft

        if cursorAction == QtGui.QAbstractItemView.MoveLeft:
            if current.parent().isValid() and current.parent() != self.rootIndex():
                return current.parent()
            else:
                return current

        elif cursorAction == QtGui.QAbstractItemView.MoveRight:
            if self.model().hasChildren(current):
                return self.model().index(0, 0, current)
            else:
                return current.sibling(current.row() + 1, current.column())

        return QtCore.QModelIndex()


    def resizeEvent(self, event):
        self._doLayout()
        self._updateScrollbars()
        if not self.isRightToLeft():
            diff = event.oldSize().width() - event.size().width()
            if diff < 0 and self.horizontalScrollBar().isVisible() \
               and self.horizontalScrollBar().value() == self.horizontalScrollBar().maximum():
                self.horizontalScrollBar().setMaximum(self.horizontalScrollBar().maximum() + diff)

        super(FilterView, self).resizeEvent(event)


    def _updateScrollbars(self):
        if self._currentAnimation.state() == QtCore.QPropertyAnimation.Running:
            return

        # find the total horizontal length of the laid out columns
        horizontalLength = 0
        if not len(self._columns) == 0:
            horizontalLength = (self._columns[-1].x() + self._columns[-1].width()) - self._columns[0].x()
            if horizontalLength <= 0: # reverse mode
                horizontalLength = (self._columns[0].x() + self._columns[0].width()) - self._columns[-1].x()

        horizontalLength += self._label.sizeHint().width()

        viewportSize = self.viewport().size()
        if horizontalLength < viewportSize.width() and self.horizontalScrollBar().value() == 0:
            self.horizontalScrollBar().setRange(0, 0)
        else:
            visibleLength = min(horizontalLength + self.horizontalOffset(), viewportSize.width())
            hiddenLength = horizontalLength - visibleLength
            if hiddenLength != self.horizontalScrollBar().maximum():
                self.horizontalScrollBar().setRange(0, hiddenLength)

        if len(self._columns) > 0:
            pageStepSize = self._columns[0].width()
            if pageStepSize != self.horizontalScrollBar().pageStep():
                self.horizontalScrollBar().setPageStep(pageStepSize)

        visible = self.horizontalScrollBar().maximum() > 0
        if visible != self.horizontalScrollBar().isVisible():
            self.horizontalScrollBar().setVisible(visible)

    def horizontalOffset(self):
        return self._offset

    def verticalOffset(self):
        return 0

    def visualRegionForSelection(self, selection):
        ranges = selection.count()

        if ranges == 0:
            return QtGui.QRegion()

        # Note that we use the top and bottom functions of the selection range
        # since the data is stored in rows.
        firstRow = selection[0].top()
        lastRow = selection[0].top()
        for range in selection:
            firstRow = min(firstRow, range.top())
            lastRow = max(lastRow, range.bottom())

        firstIdx = self.model().index(min(firstRow, lastRow), 0, self.rootIndex())
        lastIdx = self.model().index(max(firstRow, lastRow), 0, self.rootIndex())

        if firstIdx == lastIdx:
            return QtGui.QRegion(self.visualRect(firstIdx))

        firstRegion = self.visualRect(firstIdx)
        lastRegion = self.visualRect(lastIdx)
        return QtGui.QRegion(firstRegion.unite(lastRegion))

    #def setSelection(self, rect, command):

    def sizeHint(self):
        sizeHint = QtCore.QSize()
        for view in self._columns:
            sizeHint += view.sizeHint()

        return sizeHint.expandedTo(super(FilterView, self).sizeHint())

    @QtCore.pyqtSlot(int)
    def _gripMoved(self, offset):
        grip = self.sender()
        assert grip is not None

        if self.isRightToLeft():
            offset = -1 * offset

        found = False
        for view in self._columns:
            view.setColumnWidth(0, view.width())
            if not found and view.cornerWidget() == grip:
                found = True
                if self.isRightToLeft():
                    view.move(view.x() + offset, 0)
                continue

            if not found:
                continue

            view.move(view.x() + offset, 0)

        self._label.move(self._label.x() + offset, self.viewport().height()/2-self._label.height()/2)

        self._updateScrollbars()


    # close the column indicated by parentIndex
    @QtCore.pyqtSlot("const QModelIndex&")
    def _closeColumn(self, parentIndex):
        if len(self._columns) == 0:
            return

        # deselect everything in the view
        start = self.model().index(0, 0, parentIndex)
        end = self.model().index(self.model().rowCount(parentIndex)-1, 0, parentIndex)
        self.selectionModel().select(QtGui.QItemSelection(start, end), QtGui.QItemSelectionModel.Deselect)
        self.selectionModel().select(parentIndex, QtGui.QItemSelectionModel.Deselect)

        # find the column to close
        for view in self._columns:
            if view.rootIndex() == parentIndex:
                self._columns.remove(view)
                view.setVisible(False)
                view.deleteLater()
                break

        # layout the columns
        self._doLayout()

        # clean up the scrollbar
        if len(self._columns) == 0:
            self._offset = 0

        self._updateScrollbars()

    def _closeColumns(self):
        if len(self._columns) == 0:
            return

        for view in self._columns:
            self._columns.remove(view)
            view.setVisible(False)
            view.deleteLater()

    @QtCore.pyqtSlot("const QModelIndex&")
    def _columnClicked(self, index):
        parent = index.parent()
        columnClicked = None
        for view in self._columns:
            if view.rootIndex() == parent:
                columnClicked = view
                break

        if self.selectionModel() is not None and columnClicked is not None:
            self.selectionModel().setCurrentIndex(index, QtGui.QItemSelectionModel.NoUpdate)

    @QtCore.pyqtSlot(QtGui.QItemSelection, QtGui.QItemSelection)
    def _columnSelectionChanged(self, selected, deselected):
        # update our selection model
        self.selectionModel().select(selected, QtGui.QItemSelectionModel.Select)
        self.selectionModel().select(deselected, QtGui.QItemSelectionModel.Deselect)

    def _createColumn(self, index):
        if not self.model().hasChildren(index):
            return

        view = QtGui.QTreeView(self.viewport())
        view.setHeader(FilterHeader(view, parent=self.viewport(), closed=self._closeColumn))

        self._initializeColumn(view)

        view.setRootIndex(index)
        if self.model().canFetchMore(index):
            self.model().fetchMore(index)

        # initialize the column's selection with any selected item below the root
        for row in range(0, self.model().rowCount(index)):
            child_index = self.model().index(row, 0, index)
            if self.selectionModel().isSelected(child_index):
                view.selectionModel().select(child_index, QtGui.QItemSelectionModel.Select)
                view.scrollTo(child_index)
                break

        view.clicked.connect(self._columnClicked)
        view.selectionModel().selectionChanged.connect(self._columnSelectionChanged)

        view.activated.connect(self.activated)
        view.clicked.connect(self.clicked)
        view.doubleClicked.connect(self.doubleClicked)
        view.entered.connect(self.entered)
        view.pressed.connect(self.pressed)

        view.setFocusPolicy(QtCore.Qt.NoFocus)
        view.setVisible(True)
        view.setParent(self.viewport())

        # Setup corner grip
        if self._showResizeGrips:
            grip = FilterViewGrip(view)
            view.setCornerWidget(grip)
            grip.gripMoved.connect(self._gripMoved)

        # TODO: compute width from contents?
        view.setGeometry(0, 0, 100, self.viewport().height())

        # insert the column so the order of self._columns matches the model
        i = 0
        for row in range(0, self.model().rowCount()):
            if i < len(self._columns) and self._columns[i].rootIndex() == self.model().index(row, 0):
                i += 1
            if self.model().index(row, 0) == index:
                # found it!
                break
        self._columns.insert(i, view)

        self._doLayout()
        self._updateScrollbars()
        return view

    def _initializeColumn(self, column):
        column.setFrameShape(QtGui.QFrame.NoFrame)
        column.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        column.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        column.setMinimumWidth(100)
        column.setAttribute(QtCore.Qt.WA_MacShowFocusRect, False)

        column.setDragDropMode(self.dragDropMode())
        column.setDragDropOverwriteMode(self.dragDropOverwriteMode())
        column.setDropIndicatorShown(self.showDropIndicator())

        column.setRootIsDecorated(False)
        column.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)

        column.setAlternatingRowColors(self.alternatingRowColors())
        column.setAutoScroll(self.hasAutoScroll())
        column.setEditTriggers(self.editTriggers())
        column.setHorizontalScrollMode(self.horizontalScrollMode())
        column.setIconSize(self.iconSize())
        column.setSelectionBehavior(self.selectionBehavior())
        column.setTabKeyNavigation(self.tabKeyNavigation())
        column.setTextElideMode(self.textElideMode())
        column.setVerticalScrollMode(self.verticalScrollMode())

        column.setModel(self.model())

        # Copy the custom delegate per row

        for row in range(0, self.model().rowCount()):
            delegate = self.itemDelegateForRow(row)
            column.setItemDelegateForRow(row, delegate)

        # set the delegate to be the columnview delegate
        delegate = column.itemDelegate()
        column.setItemDelegate(self.itemDelegate())

    def rowsInserted(self, parent, start, end):
        super(FilterView, self).rowsInserted(parent, start, end)
        #self._checkColumnCreation(parent)

    def currentChanged(self, current, previous):
        # TODO: do something useful here
        return

    @QtCore.pyqtSlot(QtGui.QItemSelection, QtGui.QItemSelection)
    def selectionChanged(self, selected, deselected):
        super(FilterView, self).selectionChanged(selected, deselected)

        for index in deselected.indexes():
            # handle deselected top-level items
            if not self.model().parent(index).isValid():
                # un-check their actions
                for action in self.actions():
                    row = action.data().toInt()[0]
                    if row == index.row() and action.isChecked():
                        action.setChecked(False)
                # remove their columns
                self._closeColumn(index)

        for index in selected.indexes():
            # handle selected top-level items
            if not self.model().parent(index).isValid():
                # check their actions
                for action in self.actions():
                    row = action.data().toInt()[0]
                    if row == index.row() and not action.isChecked():
                        action.setChecked(True)
                # add their columns
                self._createColumn(index)

    def selectAll(self):
        if not self.model() or not self.selectionModel():
            return

        selection = QtGui.QItemSelection()

        for view in self._columns:
            parentIndex = view.rootIndex()
            for row in range(0, self.model().rowCount(parentIndex)):
                index = self.model().index(row, 0, parentIndex)
                selection.append(QtGui.QItemSelectionRange(index, index))

        self.selectionModel().select(selection, QtGui.QItemSelectionModel.ClearAndSelect)

    def _doLayout(self):
        if not self.model():
            return

        viewportWidth = self.viewport().width()
        viewportHeight = self.viewport().height()

        if self.isRightToLeft():
            x = self.viewport().width() + self.horizontalOffset()
            for view in self._columns:
                x -= view.width()
                if x != view.x() or viewportHeight != view.height():
                    view.setGeometry(x, 0, view.width(), viewportHeight)
        else:
            x = self.horizontalOffset()
            for view in self._columns:
                currentColumnWidth = view.width()
                if x != view.x() or viewportHeight != view.height():
                    view.setGeometry(x, 0, currentColumnWidth, viewportHeight)
                x += currentColumnWidth

        labelWidth = self._label.sizeHint().width()
        labelHeight = self._label.sizeHint().height()

        self._label.setGeometry(x + max(0, (viewportWidth-x)/2-labelWidth/2), viewportHeight/2 - labelHeight/2, labelWidth, labelHeight)

if __name__ == "__main__":
    app = QtGui.QApplication([])
    model = QtGui.QStandardItemModel(4, 1)
    for row in range(0, 4):
        item = QtGui.QStandardItem("row %d" % row)
        model.setItem(row, 0, item)
        for child in range(0, 4):
            child_item = QtGui.QStandardItem("%d sub-row %d" % (row, child))
            item.setChild(child, 0, child_item)

    fv = FilterView()
    fv.setModel(model)
    fv.show()

    app.exec_()
