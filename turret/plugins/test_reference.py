import os
from turret.delegate_fixtures import get_references, add_reference, remove_reference

class Data(object):
    def __init__(self, name, path):
        self.name = name
        self.path = path
        
    def save(self):
        pass

    def update(self, reload):
        for name, path in get_references().items():
            if name == self.name:
                path = self.path
                break
        else:
            add_reference(self.name, self.path)

    def remove(self):
        remove_reference(self.name)
    
def supports_ext(ext):
    return os.environ.has_key("TESTING")

def get_dependencies(parent):
    if parent.name == "scene":
        return [Data(name, path) \
                    for name, path in get_references().items()]
    else:
        return []
      
def add_dependency(name, path, parent):
    return Data(name, path)

