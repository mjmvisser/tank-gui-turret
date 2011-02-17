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
        super(Data, self).__init__(type="DLFMShader",
                                   attrib_name="shaderFile",
                                   name=name,
                                   path=path,
                                   node=node)

    def _createNode(self):
        assert self.node is None
        assert self.name is not None
        # first determine the shader type
        shader_type = pm.delightShaderInfo(file=self.path, type=True)

        # we only support creating displacement, surface, light and imager shaders
        # volume shaders map to either interior or atmosphere, with no way to determine which
        if shader_type == "volume":
            raise NotImplementedError("volume shaders are not supported")

        node_type = {"surface": "delightSurfaceShader",
                     "displacement": "delightDisplacementShader",
                     "light": "delightLightShader",
                     "imager": "delightImagerShader"}[shader_type]
        # create the shader
        return pm.ls(pm.mel.DSN_create(self.path, 0, node_type))[0]

def supports_ext(ext):
    return ext == ".sdl"

def get_dependencies(parent):
    # find all dlfm shader nodes
    shaders = [pm.ls(type=shader_type) for shader_type in ("delightSurfaceShader",
                                                           "delightDisplacementShader",
                                                           "delightInteriorShader",
                                                           "delightAtmosphereShader",
                                                           "delightImagerShader",
                                                           "delightLightShader")]
    shaders = [shader for sublist in shaders for shader in sublist]
    return [Data(node=node) for node in shaders if node in parent.child_nodes]

def add_dependency(name, path, frame_range, parent):
    return Data(name=name, path=path)

