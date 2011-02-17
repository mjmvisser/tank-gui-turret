from turret.plugins import UnsupportedPluginError

try:
    import pymel.core as pm
    from turret.mayautils import MayaNodeData
except ImportError:
    raise UnsupportedPluginError()

# requires the 3delight plugin
mayaVersion = pm.about(version=True).split()[0]
plugin = '3delight_for_maya' + mayaVersion
if not pm.pluginInfo(plugin, query=True, loaded=True):
    raise UnsupportedPluginError()


class Data(MayaNodeData):
    def __init__(self, attrib_name="Xtex", name=None, path=None, node=None):
        super(Data, self).__init__(type="DLFMTriplanar",
                                   attrib_name=attrib_name,
                                   name=name,
                                   path=path,
                                   node=node)

    def _readName(self):
        if self.node is not None and self._attrib_name is not None:
            self.name = self.node.name() + "_" + self._attrib_name

    def _writeName(self):
        if self.node is not None and self._attrib_name is not None:
            current_name = self.node.name() + "_" + self._attrib_name
            if current_name != self.name:
                new_name = self.name.replace("_" + self._attrib_name, "")
                self.node.rename(new_name)

    def _createNode(self):
        assert self.node is None
        assert self.name is not None
        # create a new dl_triplanar node with our name and path
        # need to call shadingNode, as the File constructor calls createNode instead of shadingNode
        # this results in a node that can't be seen in the hypershade
        return pm.shadingNode("dl_triplanar", name=self.name, asTexture=True)

def supports_ext(ext):
    return ext in (".tdl", ".tif")

def get_dependencies(parent):
    # find all "dl_triplanar" nodes and create a data node for each channel's texture map (if non-empty)
    nodes = [node for node in pm.ls(type="dl_triplanar") if node in parent.child_nodes]

    return [Data(node=node, attrib_name=attrib_name) \
                for node in nodes \
                    for attrib_name in ("Xtex", "Ytex", "Ztex") \
                        if node.attr(attrib_name).get() != ""]

def add_dependency(name, path, frame_range, parent):
    return Data(name=name, path=path)
