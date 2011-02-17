import os, shutil
from tempfile import NamedTemporaryFile
from turret.plugins import UnsupportedPluginError

try:
    import pymel.core as pm
    from turret.mayautils import MayaNodeData
except ImportError:
    raise UnsupportedPluginError()

class Data(MayaNodeData):
    def __init__(self):
        # remove old stuff
        try:
            tank_node = pm.ls("__tank")[0]
            tank_node.unlock()
            pm.delete(tank_node)
        except:
            pass


        super(Data, self).__init__(type="MayaScene",
                                   name="scene",
                                   path=pm.sceneName())

        # child nodes are top-level namespace only
        self.child_nodes = pm.ls(":*")

        self._readPath()

    def _readName(self):
        """Read the node name from the scene."""
        # just call it "scene" for simplicity's sake
        self.name = "scene"

    def _readPath(self):
        """Read the node path from the scene."""
        if str(pm.sceneName()) == "":
            self.path = os.path.join(str(pm.workspace.path), "untitled.ma")
        else:
            # pm.sceneName() returns a Path object, which confuses the hell out
            # of Qt. So, we cast it to a string.
            self.path = str(pm.sceneName())

    def select(self):
        """Required for MayaNodeData "select" action."""
        # do nothing
        pass

    def save(self):
        """Save the scene."""
        # we can't just save directly
        # maya attempts to save as self.path + random string, then moves the file to the self.path
        # instead, we'll save to tmp, then use shutil.move to move the file to its final resting place

        original_name = str(pm.sceneName())

        tmpfile = NamedTemporaryFile(suffix=os.path.splitext(original_name)[1])
        tmpname = tmpfile.name
        tmpfile.close()
        pm.saveAs(tmpname)
        try:
            shutil.move(tmpname, self.path)
        except:
            os.remove(tmpname)
        finally:
            pm.renameFile(original_name)

    def _reload(self):
        """Reload scene from the node path."""
        if self.path != str(pm.sceneName()):
            # check if the user has saved (only gui mode)
            if not pm.about(batch=True) and pm.cmds.file(query=True, anyModified=True):
                result = pm.confirmDialog(title="Save Changes",
                                          message="Save changes to " + str(pm.sceneName()) + "?",
                                          button=["Save", "Don't Save", "Cancel"],
                                          defaultButton="Save",
                                          cancelButton="Cancel",
                                          dismissString="Don't Save")

                if result == "Cancel":
                    doit = False
                elif result == "Save":
                    pm.cmds.file(save=True, force=True)
                    doit = True
                else: # "Don't Save"
                    doit = True
            else:
                doit = True

            if doit:
                pm.openFile(self.path, force=True)
                self.path = str(pm.sceneName())

    def update(self, reload):
        """This is called when the path or node name is changed and should
           update the external state to match the node state."""
        # write out our ids and force a reload, if requested
        self._writeIds()
        if reload:
            self._reload()


def supports_ext(ext):
    return ext in (".ma", ".mb")

def get_scene():
    return Data()
