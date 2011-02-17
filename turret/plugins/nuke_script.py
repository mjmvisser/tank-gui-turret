import os

from turret.plugins import UnsupportedPluginError

try:
    import nuke
    from turret.nukeutils import NukeNodeData
except ImportError:
    raise UnsupportedPluginError()

class Data(NukeNodeData):
    def __init__(self, path=None):
        super(Data, self).__init__(dtype="NukeScript",
                                   node_type=None,
                                   knob_name=None,
                                   name="script",
                                   path=path,
                                   node=nuke.root())

    # override
    def _readName(self):
        """Read the script name from nuke."""
        # just call it "script"
        self.name = "script"

    def _readPath(self):
        """Read the script path from nuke."""
        try:
            name = nuke.root().name()
            if name == "Root":
                self.path = os.path.join(os.getcwd(), "untitled.nk")
            else:
                self.path = name
        except:
            # in the PLE, nuke.root() returns None
            self.path = os.path.join(os.getcwd(), "untitled.nk")

    def _readFrameRange(self):
        pass

    def _writeName(self):
        """Write the script name."""
        # do nothing
        pass
    
    def _writePath(self):
        """Write the script path."""
        pass
        # do nothing, we don't want to rename the script
        
    def _writeFrameRange(self):
        pass

    def save(self):
        try:
            try:
                name = nuke.root().name()
                if name == "Root":
                    current_path = os.path.join(os.getcwd(), "untitled.nk")
                else:
                    current_path = name
            except:
                # in the PLE, nuke.root() returns None
                current_path = os.path.join(os.getcwd(), "untitled.nk")

            nuke.scriptSaveAs(self.path, 1)
        finally:
            # restore the original path
            nuke.root()['name'].setValue(current_path)
        
    def update(self, reload):
        super(Data, self).update(reload)

        if reload:
            nuke.scriptOpen(self.path)
        

def supports_ext(ext):
    return ext in (".nk", ".nkple")

def get_scene():
    return Data()
