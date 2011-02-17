import os
import imagepath
from turret.plugins import UnsupportedPluginError

try:
    import pymel.core as pm
    from turret.mayautils import MayaNodeData
except ImportError:
    raise UnsupportedPluginError()

class CacheXMLData(MayaNodeData):
    def __init__(self, name=None, path=None, node=None):
        super(CacheXMLData, self).__init__(type="MayaCacheXML",
                                                   attrib_name="xmlFile",
                                                   name=name,
                                                   path=path,
                                                   node=node)

    def _readPath(self):
        if self.node is not None:
            cacheName = self.node.attr("cacheName").get()
            cachePath = self.node.attr("cachePath").get()
            self.path = os.path.join(cachePath, cacheName + ".xml")

    def _writePath(self, reload):
        if self.node is not None:
            dir, filename = os.path.split(self.path)
            name, ext = os.path.splitext(filename)

            if self.node.attr("cacheName").get() != name:
                self.node.attr("cacheName").set(name)
            if self.node.attr("cachePath").get() != dir:
                self.node.attr("cachePath").set(dir)

    def _createNode(self):
        raise NotImplementedError


class CacheFileData(MayaNodeData):
    def __init__(self, name=None, path=None, node=None):
        super(CacheFileData, self).__init__(type="MayaCacheFile",
                                            attrib_name="mcFile",
                                            name=name,
                                            path=path,
                                            node=node)
        start = int(self.node.attr("originalStart").get())
        end = int(self.node.attr("originalEnd").get())
        self._frame_range = "%d-%d" % (start, end)

    @property
    def frame_range(self):
        return self._frame_range

    def _readPath(self):
        assert self.node is not None
        cacheName = self.node.attr("cacheName").get()
        cachePath = self.node.attr("cachePath").get()
        self.path = os.path.join(cachePath, cacheName + "Frame@.mc")

    def _writePath(self, reload):
        assert self.node is not None
        seq = imagepath.get_sequence(self.path)
        path, range = imagepath.get_sequence_parts(seq)
        dir, name, separator, frame_def, ext = imagepath.split(path)

        start, end = (float(t) for t in range.split('-'))

        if self.node.attr("cacheName").get() != name:
            self.node.attr("cacheName").set(name)
        if self.node.attr("cachePath").get() != dir:
            self.node.attr("cachePath").set(dir)
        if self.node.attr("originalStart").get() != start:
            self.node.attr("originalStart").set(start)
        if self.node.attr("originalEnd").get() != end:
            self.node.attr("originalEnd").set(end)

    def _createNode(self):
        raise NotImplementedError

def supports_ext(ext):
    return ext in (".xml", ".mc")

def get_dependencies(parent):
    return [CacheXMLData(node=node) for node in pm.ls(type="cacheFile", long=True) if node in parent.child_nodes]

