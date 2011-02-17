import os
import tank
from turret.plugins import UnsupportedPluginError

#from bundle import Bundle

try:
    import pymel.core as pm
    import maya.cmds as cmds
    from turret.mayautils import MayaNodeData
except ImportError:
    raise UnsupportedPluginError()

# load the tankBundle plugin
if not cmds.pluginInfo("tankBundle.py", query=True, loaded=True):
    cmds.loadPlugin("tankBundle.py")

class Data(MayaNodeData):
    def __init__(self, name=None, path=None, node=None):
        super(Data, self).__init__(type="TankBundle",
                                   attrib_name="fileName",
                                   name=name,
                                   path=path,
                                   node=node)
    def _createNode(self):
        # override this for non-standard node creation
        assert self.node is None
        assert self.name is not None
        return pm.createNode("tankBundle", name=self.name)

    @property
    def child_nodes(self):
        return self.node.members()

    def _reload(self, children):
        parent_revision = tank.find(self.path)

        # go through each revision in the bundle
        # find matching connected reference with same container
        # update
        for child_revision in self._bundle.revisions:
            if os.path.splitext(child_revision.system.filesystem_location)[1] in (".ma", ".mb"):
                for ref_node in self.node.members():
                    ref = pm.FileReference(ref_node)
                    r2 = tank.find(ref.path)
                    if str(r2) == str(child_revision):
                        # same reference, done with this revision
                        break
                    elif str(r2.container) == str(child_revision.container):
                        # same container, different revision
                        # replace the revision with this one
                        ref.replaceWith(child_revision.system.vfs_full_paths[0])
                        break

        # now go through connected reference nodes
        # if one is connected, but doesn't belong, unlink it
        # NOTE: we don't remove it -- leave it up to the user to do that
        for ref_node in self.node.members():
            ref = pm.FileReference(ref_node)
            revision = tank.find(ref.path)
            if not revision in self._bundle.revisions:
                self.node.remove(ref_node)

    def update(self, reload):
        super(Data, self).update(reload)

        # go through connected reference nodes
        # if one is connected, but doesn't belong, unlink it
        for ref_node in self.node.members():
            if not ref_node in self.child_nodes:
                self.node.remove(ref_node)

        # now make sure all valid children are linked
        #for child_data in children:
        #    self.node.add(child_data.node)


def supports_ext(ext):
    return ext == ".bundle"

def get_dependencies(parent):
    return [Data(node=node) for node in pm.ls(type="tankBundle") if node in parent.child_nodes]

def add_dependency(name, path, frame_range, parent):
    return Data(name=name, path=path)
