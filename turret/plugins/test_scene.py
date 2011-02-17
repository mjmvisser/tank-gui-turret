import os
from turret.delegate_fixtures import get_filename, rename, save

class Data(object):
    def __init__(self, name, path):
        self.name = name
        self.path = path
        
    def save(self):
        save()

    def update(self, reload):
        if self.path != get_filename():
            rename(self.path) 

def supports_ext(ext):
    return os.environ.has_key("TESTING")
    
def get_scene():
    return Data("scene", get_filename())

