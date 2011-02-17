"""
Generic delegate plugin. This delegate is never used and only
exists as a description of the delegate interface.
Delegates are responsible for querying the host application
for the scene, dependencies, or products, and updating
the scene using the host API.
Each delegate supports a single type of asset. For example,
Maya needs delegates for:
* File nodes
* References
* Playblasts
* Renders
* Geocaches
* etc
"""

class Data(object):
    """
    Blind data object returned by the delegate representing
    a single asset. Delegate data is responsible for making
    any changes to the asset through this interface.
    
    .. attribute:: Data.name
    
       The descriptive name of the asset described by this object.
       This is usually the name of the node, reference, or other
       application object.
       
    .. attribute:: Data.path
    
       The filesystem path to the asset.
       
    .. attribute:: Data.frame_range
    
       (optional) The frame range of the asset.
    
    Changes to attributes are not immediately delegated to the application.
    The :meth:`Data.update` is responsible for this.
    """
    
    def __init__(self):
        """
        Data is ONLY constructed by the delegate, so parameters will
        vary.
        """
        pass
    
    def save(self):
        """
        (optional) Saves any changes made to this object in the underlying application.
        """
    
    def update(self, reload):
        """
        (optional) Updates the underlying application object with any changes made to
        object attributes (:attr:`Data.name`, :attr:`Data.path`, etc.)
        """
        pass
        
    def remove(self):
        """
        (optional) Removes the underlying application object.
        """
        pass
        
    def import_(self):
        """
        (optional) Imports the underlying application object.
        """
        pass
    
def supports_ext(ext):
    """
    Tests if a given extension is supported by this delegate.
     
    :param ext: Extension to test in the format returned by os.path.splitext (".ext").
    :rtype: boolean
    """
    return False

def get_dependencies(parent):
    """
    Returns a list of delegate Data objects representing dependencies
    supported by this delegate having a parent delegate of parent.
    
    :param parent: Parent delegate object.
    :type parent: Object matching the Delegate interface.
    :rtype: list of data objects.
    """
    return []

def add_dependency(name, path, frame_range, parent):
    """
    Creates a Data object representing the given dependency with the given
    parent. The asset will be added to the parent when the data object's
    update method is called.
    
    :param name: What to call the asset.
    :param path: Filesystem location of the asset.
    :rtype: data object
    """
    pass
