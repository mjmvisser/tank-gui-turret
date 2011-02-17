from turret.plugins import UnsupportedPluginError

try:
    import pymel.core as pm
    from turret.mayautils import MayaNodeData
except ImportError:
    raise UnsupportedPluginError()

class Data(MayaNodeData):
    def __init__(self, name=None, path=None, node=None):
        super(Data, self).__init__(type="MayaFile",
                                   attrib_name="imageName",
                                   name=name,
                                   path=path,
                                   node=node)

    def _createNode(self):
        try:
            cam = pm.ls(sl=True, type="camera")[0]
        except:
            raise AttributeError("Please select a camera shape!")

        node = pm.nodetypes.ImagePlane()

        # adapted from cameraImagePlaneUpdate.mel
        node.message.connect(cam.imagePlane, nextAvailable=True)
        cam.horizontalFilmAperture.connect(node.sizeX)
        cam.verticalFilmAperture.connect(node.sizeY)
        cam.orthographicWidth.connect(node.width)
        cam.orthographicWidth.connect(node.height)
        node.attr("center").set(cam.getWorldCenterOfInterest())
        for item in pm.listRelatives(cam, parent=True):
            pm.showHidden(item, below=True)

        for modelPanel in pm.getPanel(type="modelPanel"):
            modelCamera = pm.modelPanel(modelPanel, query=True)
            if modelCamera != "":
                for shape in pm.listRelatives(modelCamera, shapes=True):
                    if shape == cam:
                        editor = pm.modelPanel(modelPanel, query=True, modelEditor=True)
                        pm.modelEditor(editor, edit=True, updateColorMode=True)
                        break

        return node


def supports_ext(ext):
    return ext in (".jpg", ".jpeg", ".tif", ".tiff", ".sgi", ".hdr", ".tdl", ".iff", ".rgb")

def get_dependencies(parent):
    # find all "imagePlane" nodes
    return [Data(node=node) for node in pm.ls(type="imagePlane") if node in parent.child_nodes]

def add_dependency(name, path, frame_range, parent):
    return Data(name=name, path=path)