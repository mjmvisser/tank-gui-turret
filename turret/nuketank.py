import os
import nuke
import nukeqt
from PyQt4 import QtCore, QtGui

from .tankscene import Scene
from .tankui.publish import PublishDialog
from .tankui.assets import AssetsWindow
from .tankui.browser import BrowserDialog
from . import plugins, sandbox

plugins.initialize()

app = nukeqt.initialize()

nukeqt.app.setOrganizationName("LumiereVFX")
nukeqt.app.setOrganizationDomain("lumierevfx.com")
nukeqt.app.setApplicationName("turret")

# define these up here so they aren't deleted automatically when no longer referenced
viewAssetsWindow = None
publishFramesDialog = None

nukeqt.app.setStyleSheet("""
QDialog { background-color: rgb(50, 50, 50); }
QAbstractItemView { background-color: rgb(100, 100, 100);
                    alternate-background-color: rgb(76, 76, 76);
                    color: rgb(243, 243, 243);
                    selection-background-color: rgb(247, 146, 30);
                    selection-color: rgb(243, 243, 243) }
QWidget { background-color: rgb(50, 50, 50);
        color: rgb(243, 243, 243);
        selection-background-color: rgb(247, 146, 30);
        selection-color: rgb(243, 243, 243) }
QLineEdit { background-color: rgb(100, 100, 100); }
QTableView { gridline-color: rgb(39, 39, 39);
             background-color: rgb(50, 50, 50); }
QTableView::item { background-color: rgb(100, 100, 100); }
QTableView::item::disabled { background-color: rgb(50, 50, 50); }
QComboBox { background-color: rgb(76, 76, 76); }
QLineEdit > QToolButton { background-color: rgb(100, 100, 100); }
QToolButton:checked { background-color: rgb(77, 77, 77); }
QMenu { border: 1px solid rgb(0, 0, 0); }
QMenu::item:disabled { color: rgb(100, 100, 100); }
QFrame#line { color: rgb(0, 0, 0); }
""")

# decorator for creating menu items
def menuitem(label, parent, shortcut=None, spacer=False, wrapper=None):
    def decorator(func):
        if spacer:
            parent.addCommand("-", "", "")
        if wrapper:
            parent.addCommand(label, lambda wrapper=wrapper, func=func: wrapper(func), shortcut)
        else:
            parent.addCommand(label, lambda func=func: func(), shortcut)
        return func
    return decorator

# add a tank menu
tank_menu = nuke.menu("Nuke").addMenu("&Tank")

window = None

@menuitem("&Set Project...", parent=tank_menu)
def setProject():
    try:
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.BusyCursor)
        container = sandbox.get(os.getcwd())[0]
    except:
        container = None
    finally:
        QtGui.QApplication.restoreOverrideCursor()

    dialog = BrowserDialog(modal=True)
    dialog.setBrowseType(BrowserDialog.BrowseContainers)
    dialog.setHintText("Select a container.")
    dialog.setSelectedItem(container)

    if dialog.exec_() == QtGui.QDialog.Accepted:
        container = dialog.selectedItem()

        if not container:
            return

        work_root = sandbox.get_path(container)

        # create the directory
        if not os.path.exists(work_root):
            os.makedirs(work_root)

        # create subdirectories
        # TODO: move this into a plugin or something
        for subdir in ("scripts", "images", "scenes", "dailies"):
            if not os.path.exists(os.path.join(work_root, subdir)):
                os.makedirs(os.path.join(work_root, subdir))

        # cd
        os.chdir(work_root)

        print "Set project to %s" % work_root


@menuitem("&Open...", parent=tank_menu)
def openAsset():
    try:
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.BusyCursor)
        container = sandbox.get(os.getcwd())[0]
    except:
        container = None
    finally:
        QtGui.QApplication.restoreOverrideCursor()

    dialog = BrowserDialog(modal=True)
    dialog.setBrowseType(BrowserDialog.BrowseRevisions)
    dialog.setHintText("Select a revision.")

    if dialog.exec_() == QtGui.QDialog.Accepted:
        revision = dialog.selectedItem()

        if not revision:
            return

        container = revision.container

        work_root = sandbox.get_path(container)

        # create the directory
        if not os.path.exists(work_root):
            os.makedirs(work_root)

        # create subdirectories
        # TODO: move this into a plugin or something
        for subdir in ("scripts", "images", "scenes", "dailies"):
            if not os.path.exists(os.path.join(work_root, subdir)):
                os.makedirs(os.path.join(work_root, subdir))

        # cd
        os.chdir(work_root)

        # get revision path
        tank_path = revision.system.vfs_full_paths[0]

        # open
        nuke.scriptOpen(tank_path)

@menuitem("View Assets...", parent=tank_menu)
def viewAssets():
    # need this to be global, otherwise the window is destroyed immediately
    global viewAssetsWindow #IGNORE:W0603

#    try:
#        QtGui.QApplication.setOverrideCursor(QtCore.Qt.BusyCursor)
#        container = sandbox.get(os.getcwd())[0]
#    except:
#        container = None
#    finally:
#        QtGui.QApplication.restoreOverrideCursor()

    scene = Scene(plugins.get_one_delegate(name="nuke_script"))
    viewAssetsWindow = AssetsWindow()
    viewAssetsWindow.setScene(scene)
    viewAssetsWindow.show()

@menuitem("Publish Frames...", parent=tank_menu)
def publishFrames():
    # need this to be global, otherwise the window is destroyed immediately
    global publishFramesDialog #IGNORE:W0603
    scene = Scene(plugins.get_one_delegate(name="nuke_script"))

    publishFramesDialog = PublishDialog()
    publishFramesDialog.setCwd(os.path.split(scene.path)[0])
    publishFramesDialog.setSourceRevision(scene.last_revision)
    publishFramesDialog.show()
