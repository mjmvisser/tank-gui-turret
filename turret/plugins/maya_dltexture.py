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
    def __init__(self, name=None, path=None, node=None):
        super(Data, self).__init__(type="DLFMFile",
                                   attrib_name="textureName",
                                   name=name,
                                   path=path,
                                   node=node)

    def _createNode(self):
        assert self.node is None
        assert self.name is not None
        # create a new dl_textureMap node with our name and path
        # need to call shadingNode, as the File constructor calls createNode instead of shadingNode
        # this results in a node that can't be seen in the hypershade
        return pm.shadingNode("dl_textureMap", name=self.name, asTexture=True)

def supports_ext(ext):
    return ext in (".tdl", ".tif")

def get_dependencies(parent):
    # find all "dl_textureMap" nodes
    return [Data(node=node) for node in pm.ls(type="dl_textureMap") if node in parent.child_nodes and node.textureName.get() != ""]

def add_dependency(name, path, frame_range, parent):
    return Data(name=name, path=path)

