import os, re
import tank
from turret.plugins import UnsupportedPluginError

try:
    import pymel.core as pm
    from turret.mayautils import MayaNodeData
except ImportError:
    raise UnsupportedPluginError()

class CacheDefData(MayaNodeData):
    def __init__(self, name=None, path=None, node=None, index=0):
        self._index = index
        super(CacheDefData, self).__init__(type="MayaCacheDef",
                                            attrib_name="mcdFile",
                                            name=name,
                                            path=path,
                                            node=node)
        start = int(self.node.cacheList[self._index].startIndex.get())
        end = int(self.node.cacheList[self._index].endIndex.get())
        self._frame_range = "%d-%d" % (start, end)

    @property
    def frame_range(self):
        return self._frame_range

    def _readPath(self):
        if self.node is not None:
            cachePath = self.node.cacheList[self._index].fileName.get()
            self.path = tank.util.sequence.get_pattern(cachePath, "SHAKE")

    def _writePath(self, reload):
        if self.node is not None:
            seq = tank.util.sequence.resolve(self.path, self.frame_range)

            start, end, step = (int(x) if x is not None else None for x in re.match("(-?\d+)-(-?\d+)x?(:?-?\d+)?", self.frame_range).groups())

            if self.node.cacheList[self._index].fileName.get() != seq[0]:
                self.node.cacheList[self._index].fileName.set(seq[0])
            if self.node.cacheList[self._index].startIndex.get() != start:
                self.node.cacheList[self._index].startIndex.set(start)
            if self.node.cacheList[self._index].endIndex.get() != end:
                self.node.cacheList[self._index].endIndex.set(end)

    def _createNode(self):
        raise NotImplementedError

def supports_ext(ext):
    return ext == ".mcd"

def get_dependencies(parent):
    return [CacheDefData(node=node, index=index) for node in pm.ls(type="lm_cacheDefBlend") for index in range(0, node.cacheList.numElements()) if node in parent.child_nodes]

