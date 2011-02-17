import re, os
import nuke

SUPPORTED_IMAGE_EXTS = (".cin", ".dpx", ".exr", ".gif", ".hdr", ".hdri", ".iff",
                        ".jpg", ".jpeg", ".iff", ".png", ".png16", ".psd",
                        ".sgi", ".rgb", ".rgba", ".sgi16", ".pic",
                        ".tif", ".tiff", ".tif16", ".tiff16", ".ftif", ".ftiff",
                        ".tga", ".targa", ".rla", ".xpm", ".yuv")

SUPPORTED_GEO_EXTS = (".obj", ".fbx")

# TODO: move this into tank's sequence plugin?
def convert_to_shake_path(path):
    def convert_to_shake(mobj):
        if mobj.group(3) != None:
            if int(mobj.group(3)) == 4:
                pad = "#"
            else:
                pad = "@"*int(mobj.group(3))
            return mobj.group(1) + pad + mobj.group(4)
        else:
            return mobj.group(1) + mobj.group(3)

    dir, filename = os.path.split(path)
    filename = re.sub(r"(.*[.])(%([0-9]+)d)?([.].*)", convert_to_shake, filename)
    return os.path.join(dir, filename)

def convert_to_nuke_path(path):
    def convert_to_nuke(mobj):
        if mobj.group(2) != None:
            if mobj.group(2) == '#':
                pad = 4
            else:
                # @@@@
                pad = len(mobj.group(2))
            return mobj.group(1) + "%0" + str(pad) + "d" + mobj.group(3)
        else:
            return mobj.group(1) + mobj.group(3)

    dir, filename = os.path.split(path)
    filename = re.sub(r"(.*[.])(@+|#)([.].*)", convert_to_nuke, filename)
    return os.path.join(dir, filename)


class NukeNodeData(object):
    def __init__(self, dtype, node_type, knob_name, name=None, path=None, frame_range=None, node=None):
        # path is expected to be in Nuke format (blah.%04d.ext or blah.ext)
        self.type = dtype
        self.node_type = node_type
        self._knob_name = knob_name
        self.name = name
        self.node = node
        self.path = path
        self.frame_range = frame_range
        self.container_id = None
        self.revision_type_id = None
        self.last_revision_id = None

        if self.node is not None and self._knob_name is not None:
            # get frame range and path from node
            self._path = self.node.knob(self._knob_name).value()

            if "first" in self.node.knobs().keys() and "last" in self.node.knobs().keys():
                self.frame_range = "%g-%g" % (self.node.knob("first").value(), self.node.knob("last").value())

        if self._knob_name is not None:
            self._container_id_knob_name = "__container__" + self._knob_name
            self._revision_type_id_knob_name = "__revisionType__" + self._knob_name
            self._last_revision_id_knob_name = "__lastRevision__" + self._knob_name
        else:
            self._container_id_knob_name = "__container"
            self._revision_type_id_knob_name = "__revisionType"
            self._last_revision_id_knob_name = "__lastRevision"

        # if the node exists (it may not yet!) read the relevant attributes
        if self.node is not None:
            # container and revision id
            self._readIds()
            # node name
            self._readName()
            # frame range
            self._readFrameRange()
            # path
            self._readPath()

    def __eq__(self, other):
        if type(other) is type(self):
            return self.__dict__ == other.__dict__
        else:
            return False

    def _readKnob(self, name):
        assert self.node is not None

        if name in self.node.knobs().keys():
            return self.node.knob(name).value()
        else:
            return None

    def _writeKnob(self, name, value):
        assert self.node is not None

        if name not in self.node.knobs().keys():
            knob = nuke.String_Knob(name)
            self.node.addKnob(knob)
            knob.setVisible(False)
        else:
            knob = self.node.knob(name)
        knob.setValue(value)

    def _readIds(self):
        self.revision_type_id = self._readKnob(self._revision_type_id_knob_name)
        self.container_id = self._readKnob(self._container_id_knob_name)
        self.last_revision_id = self._readKnob(self._last_revision_id_knob_name)

    def _readName(self):
        self.name = self.node.name()

    def _readPath(self):
        assert self._knob_name is not None
        path = self._readKnob(self._knob_name)
        self.path = convert_to_shake_path(path)

    def _readFrameRange(self):
        start = self._readKnob("first")
        end = self._readKnob("last")
        frame_range = "%d-%d" % (start, end)
        if self.frame_range != frame_range:
            self.frame_range = frame_range

    def _writeIds(self):
        # set ids
        for name, value in zip((self._container_id_knob_name,
                                self._revision_type_id_knob_name,
                                self._last_revision_id_knob_name),
                               (self.container_id,
                                self.revision_type_id,
                                self.last_revision_id)):
            self._writeKnob(name, value)

    def _writeName(self):
        assert self.node is not None
        if self.node.name() != self.name:
            self.node.setName(self.name, uncollide=True)

    def _writePath(self):
        assert self.node is not None
        path = convert_to_nuke_path(self.path)
        if self._readKnob(self._knob_name) != path:
            self._writeKnob(self._knob_name, path)

    def _writeFrameRange(self):
        assert self.node is not None
        if self.frame_range is not None:
            start, end = (int(i) for i in self.frame_range.split("-"))
            if self.node.knob("first").value() != start:
                self.node.knob("first").setValue(start)
            if self.node.knob("last").value() != end:
                self.node.knob("last").setValue(end)

    def update(self, reload):
        # create the node if it doesn't exist
        if self.node is None:
            self.node = self.node_type()

        # write ids, node name and path
        self._writeIds()
        self._writeName()
        self._writePath()
        self._writeFrameRange()

    def remove(self):
        if self.node is not None:
            nuke.delete(self.node)
            self.node = None

#