import os
import imagepath
from turret.plugins import UnsupportedPluginError

try:
    import pymel.core as pm
    from turret.mayautils import MayaNodeData
except ImportError:
    raise UnsupportedPluginError()

class Data(MayaNodeData):
    def __init__(self, name=None, path=None, node=None):
        super(Data, self).__init__(type="MayaDiskCache",
                                   attrib_name="cacheFileName",
                                   name=name,
                                   path=path,
                                   node=node)

    def _readPath(self):
        if self.node is not None:
            cache_name = self.node.attr("cacheName").get()
            dir, filename = os.path.split(cache_name)
            if dir in ("", "data"):
                dir = os.path.join(str(pm.workspace.path), "data")
            self.path = os.path.join(dir, filename)

            self._writePath(False)

    def _writePath(self, reload):
        if self.node is not None:
            attrib = self.node.attr("cacheName")
            if attrib.get() != self.path:
                if attrib.isLocked():
                    attrib.unlock()
                attrib.set(self.path)
                # maya has a "feature" that changes this attribute when the scene is saved
                # locking it prevents that from happening!
                attrib.lock()

    def _createNode(self):
        raise NotImplementedError

def supports_ext(ext):
    return ext == ".mchp"

def get_dependencies(parent):
    return [Data(node=node) for node in pm.ls(type="diskCache", long=True) if node in parent.child_nodes]
