import os
from PyQt4.QtGui import *
from PyQt4.QtCore import *

from .tankscene import Scene
from .tankui.publish import PublishDialog
from .tankui.assets import AssetsWindow
from . import plugins
from mayatank import tank_menu, menuitem

# define this up here so it isn't deleted automatically
dialog = None


def viewAssets():
    global dialog

    address = None

    scene = Scene(plugins.get_one_delegate(name="test_scene"))
    dialog = AssetsWindow(scene, type_filter=TypeFilters.ALL, address=address, cwd=pm.workspace.path)
    dialog.show()

@menuitem("Publish Assets...", parent=tank_menu)
def publishAssets():
    global dialog
    scene = Scene(plugins.get_one_delegate(name="test_scene"))
    dialog = PublishDialog(scene)
    dialog.show()

@menuitem("Publish Product...", parent=tank_menu)
def publishProduct():
    global dialog
    scene = Scene(plugins.get_one_delegate(name="test_scene"))

    dialog = PublishDialog(cwd=os.path.split(scene.path)[0],
                           container=scene.container,
                           source_revision=scene.last_revision)
    dialog.show()

