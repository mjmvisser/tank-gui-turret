# fake application with load/save/add reference/remove reference

import cPickle

__data = {"filename": None, "refs": {}}

def load(path):
    __data = cPickle.load(path)

def save():
    f = open(__data["filename"], "w")
    cPickle.dump(__data, f)
    f.close()
    
def add_reference(name, path):
    assert name not in __data["refs"].keys()
    __data["refs"][name] = path
    
def remove_reference(name):
    assert name in __data["refs"].keys()
    del __data["refs"][name]

def get_references():
    return __data["refs"]

def rename(path):
    __data["filename"] = path
    
def get_filename():
    return __data["filename"]