import os
from turret.plugins import UnsupportedPluginError

try:
    import pymel.core as pm
    from turret.mayautils import MayaNodeData
except ImportError:
    raise UnsupportedPluginError()

if not pm.pluginInfo("Fur", query=True, loaded=True):
    raise UnsupportedPluginError()

class Data(MayaNodeData):
    def __init__(self, node, attrib):
        self._attrib = attrib
        super(Data, self).__init__(type="MayaFurAttrib",
                                   attrib_name=attrib.name(includeNode=False),
                                   node=node)

    def _readName(self):
        if self.node is not None and self._attrib is not None:
            self.name = self.node.name() + "_" + self._attrib.array().name(includeNode=False) + str(self._attrib.index())

    def _writeName(self):
        if self.node is not None and self._attrib is not None:
            name = self.node.name() + "_" + self._attrib.array().name(includeNode=False) + str(self._attrib.index())
            if name != self.name:
                name = self.name.replace("_" + self._attrib.array().name(includeNode=False) + str(self._attrib.index()), "")
                self.node.rename(name)

    def _createNode(self):
        raise NotImplementedError


def supports_ext(ext):
    return ext in (".tif", ".iff", ".rgb", ".sgi", ".jpg", ".exr")

def get_dependencies(parent):
    data = []
    for node in pm.ls(type="FurDescription"):
        if node in parent.child_nodes:
            # each of these is an array
            for attrib_name in ("BaseColorMap", "TipColorMap",
                                "BaseAmbientColorMap", "TipAmbientColorMap",
                                "SpecularColorMap",
                                "LengthMap",
                                "SpecularSharpnessMap",
                                "BaldnessMap",
                                "BaseOpacityMap", "TipOpacityMap",
                                "BaseWidthMap", "TipWidthMap",
                                "SegmentsMap",
                                "BaseCurlMap", "TipCurlMap",
                                "ScraggleMap", "ScraggleFrequencyMap", "ScraggleCorrelationMap",
                                "ClumpingMap", "ClumpShapeMap",
                                "InclinationMap", "RollMap", "PolarMap",
                                "AttractionMap", "OffsetMap",
                                "CustomEqualizerMap"):
                array_attrib = node.attr(attrib_name)
                for index in range(0, array_attrib.getNumElements()):
                    attrib = array_attrib.elementByPhysicalIndex(index)
                    if attrib.get() is not None and len(attrib.get()) != 0:
                        data.append(Data(node, attrib))
    return data
