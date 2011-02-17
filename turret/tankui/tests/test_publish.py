from PyQt4.QtCore import *
from PyQt4.QtGui import *

#class SceneData(object):
#    def __init__(self, path, name):
#        self.path = path
#        self.name = name
#
#class ProductData(object):
#    def __init__(self, path, name):
#        self.path = path
#        self.name = name
#
#class DependencyData(object):
#    def __init__(self, path, name):
#        self.path = path
#        self.name = name
#        
#class DummyDelegate(object):
#    def get_scene(self):
#        scene = SceneData("/prod/soe_previz/work/sequences/test/shots/test/anim/markv/scenes/test.ma", "Scene")
#        return scene
#        
#    def get_dependencies(self, parent):
#        if isinstance(parent, SceneData):
#            d1 = DependencyData("/tank/soe_previz/sequences/test/shots/test/anim/images/test_anim_v036-613_113.seq/some_output.#.tif", "d1")
#            d2 = DependencyData("/tank/soe_previz/sequences/test/shots/test/anim/images/test_anim_v017-613_66.seq/some_output.#.tif", "d2")
#            return [d1, d2]
#        else:
#            return []
#        
#    def get_products(self, parent):
#        if isinstance(parent, SceneData):
#            p1 = ProductData("/prod/soe_previz/work/sequences/test/shots/test/anim/markv/images/myoutput.#.tif", "p1")
#            p2 = ProductData("/prod/soe_previz/work/sequences/test/shots/test/anim/markv/images/playblast.#.tif", "p2")
#            return [p1, p2]
#        else:
#            return []
#
#
#def test_publish():
#    delegates.add(DummyDelegate())
#
#    scene = Scene(DummyDelegate())
#    dlg = PublishDialog(scene)
#    dlg.exec_()
