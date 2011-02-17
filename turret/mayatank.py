import os
import pymel.core as pm
import maya.cmds as cmds
from PyQt4 import QtCore, QtGui
import mayaqt

from .tankscene import Scene
from .tankui.publish import PublishDialog
from .tankui.assets import AssetsWindow
from .tankui.browser import BrowserDialog
from . import plugins, sandbox
from . import mayautils

plugins.initialize()

mayaqt.initialize()

mayaqt.app.setOrganizationName("LumiereVFX")
mayaqt.app.setOrganizationDomain("lumierevfx.com")
mayaqt.app.setApplicationName("turret")

# define these up here so they aren't deleted automatically when no longer referenced
viewAssetsWindow = None
publishFramesDialog = None

mayaqt.app.setStyleSheet("""
QDialog { background-color: rgb(216, 216, 216); }
QAbstractItemView { background-color: rgb(216, 216, 216);
                    color: rgb(0, 0, 0);
                    selection-background-color: rgb(0, 0, 0);
                    selection-color: rgb(216, 216, 216) }
QWidget { background-color: rgb(216, 216, 216);
        color: rgb(0, 0, 0);
        selection-background-color: rgb(0, 0, 0);
        selection-color: rgb(216, 216, 216) }
QLineEdit { background-color: rgb(255, 255, 255); }
QTableView { gridline-color: rgb(0, 0, 0); }
QLineEdit > QToolButton { background-color: rgb(255, 255, 255); }
QMenu { border: 1px solid rgb(0, 0, 0); }
""")

# helper for creating menu items
def menuitem(label, parent, optionBox=False, overlayLabel=None):
    def decorator(func):
        pm.menuItem(parent=parent,
                         label=label,
                         command=lambda arg: func())
        if optionBox:
            pm.menuItem(parent=parent,
                             label="Opt ",
                             optionBox=True,
                             command=lambda arg: func(optionBox=True),
                             imageOverlayLabel=overlayLabel)

        return func
    return decorator

# add a tank menu
tank_menu = pm.menu(parent="MayaWindow", label="Tank", tearOff=True)

@menuitem("Set Project...", parent=tank_menu)
def setProject():
    try:
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.BusyCursor)
        container = sandbox.get(pm.workspace.path)[0]
    except:
        container = None
    finally:
        QtGui.QApplication.restoreOverrideCursor()

    dialog = BrowserDialog(modal=True)
    dialog.setBrowseType(BrowserDialog.BrowseContainers)
    dialog.setHintText("Select a container.")
    dialog.setCwd(pm.workspace.path)
    dialog.setSelectedItem(container)

    if dialog.exec_() == QtGui.QDialog.Accepted:
        container = dialog.selectedItem()

        if not container:
            return

        work_root = sandbox.get_path(container)

        # set the project
        mayautils.setProject(work_root)

        print "Set project to %s" % work_root

        # rename the scene to something sane
        # otherwise, the scene will be named something in the previous project
        pm.renameFile(os.path.join(pm.workspace.path, pm.workspace.fileRules["scene"], pm.sceneName().name))

        # check if we have start_frame and end_frame properties available
        for l in container.labels.values():
            if "frame_start" in l.properties and "frame_end" in l.properties:
                frame_start = l.properties.frame_start
                frame_end = l.properties.frame_end
                if frame_start is not None and frame_end is not None:
                    pm.playbackOptions(animationStartTime=frame_start, minTime=frame_start,
                                       animationEndTime=frame_end, maxTime=frame_end)
                    pm.currentTime(frame_start)
                    print "Set frame range to: %d-%d" % (frame_start, frame_end)
                    break


@menuitem("Open Asset...", parent=tank_menu)
def openAsset():
    try:
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.BusyCursor)
        container = sandbox.get(pm.workspace.path)[0]
    except:
        container = None
    finally:
        QtGui.QApplication.restoreOverrideCursor()

    dialog = BrowserDialog(modal=True)
    dialog.setBrowseType(BrowserDialog.BrowseRevisions)
    dialog.setHintText("Select a revision.")
    dialog.setCwd(pm.workspace.path)
    dialog.setSelectedItem(container)

    if dialog.exec_() == QtGui.QDialog.Accepted:
        revision = dialog.selectedItem()

        if not revision:
            return

        container = revision.container

        work_root = sandbox.get_path(container)

        # set the project
        mayautils.setProject(work_root)

        # check if the user has saved
        if cmds.file(query=True, anyModified=True):
            result = pm.confirmDialog(title="Save Changes",
                                           message="Save changes to " + pm.sceneName() + "?",
                                           button=["Save", "Don't Save", "Cancel"],
                                           defaultButton="Save",
                                           cancelButton="Cancel",
                                           dismissString="Don't Save")
            if result == "Cancel":
                return
            elif result == "Save":
                cmds.file(save=True, force=True)
            else: # "Don"t Save"
                pass

        # get revision path
        tank_path = revision.system.vfs_full_paths[0]
#            tank_root, tank_filename = os.path.split(tank_path)
#            tank_filename, tank_ext = os.path.splitext(tank_filename)
#
#            # remove "-v006-1451_96" from end of filename
#            tank_filename = re.sub(r"-v[0-9]+-[0-9_]+$", "", tank_filename)
#
        # open revision
        pm.openFile(tank_path, force=True)


@menuitem("View Assets...", parent=tank_menu)
def viewAssets():
    # need to use a global here, otherwise python destroys the object as soon as it is dereferenced
    global viewAssetsWindow #IGNORE:W0603


#    try:
#        QApplication.setOverrideCursor(Qt.BusyCursor)
#        container = sandbox.get(pm.workspace.path)[0]
#    except:
#        container = None
#    finally:
#        QApplication.restoreOverrideCursor()

    scene = Scene(plugins.get_one_delegate(name="maya_scene"))
    viewAssetsWindow = AssetsWindow()
    viewAssetsWindow.setCwd(pm.workspace.path)
    viewAssetsWindow.setScene(scene)
    viewAssetsWindow.show()

@menuitem("Publish Frames...", parent=tank_menu)
def publishFrames():
    # need to use a global here, otherwise python destroys the object as soon as it is dereferenced
    global publishFramesDialog #IGNORE:W0603

    try:
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.BusyCursor)
        container = sandbox.get(pm.workspace.path)[0]
    except:
        container = None
    finally:
        QtGui.QApplication.restoreOverrideCursor()

    scene = Scene(plugins.get_one_delegate(name="maya_scene"))

    publishFramesDialog = PublishDialog()
    publishFramesDialog.setCwd(os.path.split(scene.path)[0])
    if scene.last_revision is not None:
        publishFramesDialog.setContainer(scene.last_revision.container)
    else:
        publishFramesDialog.setContainer(container)
    publishFramesDialog.setSourceRevision(scene.last_revision)
    publishFramesDialog.show()
