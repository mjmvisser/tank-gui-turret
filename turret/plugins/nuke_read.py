from turret.plugins import UnsupportedPluginError

try:
    import nuke
    from turret.nukeutils import NukeNodeData, SUPPORTED_IMAGE_EXTS
except ImportError:
    raise UnsupportedPluginError()

class Data(NukeNodeData):
    def __init__(self, name=None, path=None, frame_range=None, node=None):
        super(Data, self).__init__(dtype="NukeRead",
                                   node_type=nuke.nodes.Read,
                                   knob_name="file",
                                   name=name,
                                   path=path,
                                   frame_range=frame_range,
                                   node=node)

def supports_ext(ext):
    return ext in SUPPORTED_IMAGE_EXTS

def get_dependencies(parent):
    if parent.type == "NukeScript":
        return [Data(node=node) for node in nuke.root().nodes() if node.Class() == "Read"]
    else:
        return []

def add_dependency(name, path, frame_range, parent):
    return Data(name=name, path=path, frame_range=frame_range)

#