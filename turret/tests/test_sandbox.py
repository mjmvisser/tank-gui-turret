import tank
from turret import sandbox

class _TestSandbox(object):
    def setup(self):
        self.container = tank.find("Block(Color(red), Shape(square))")
        filename = "/usr/tmp/foo.test"
        open(filename, "w").close()
        Em = tank.server.Em()
        fp = tank.server.FilePublisher(Em.find("EntityType=Test"),
                                       Em.find(str(self.container)),
                                       filename)
        fp.set_property("created_by", Em.find("user=tank"))
        r = fp.publish()

        self.revision = Em.find(str(r))

    def test_get_path_container(self):
        path = sandbox.get_path(self.container)

        assert sandbox.get(path)[0] == self.container and sandbox.get(path)[1] is None

    def test_get_path_revision(self):
        path = sandbox.get_path(self.revision)

        assert sandbox.get(path) == (self.container, None)

    def test_get(self):
        path = sandbox.get_path(self.container)
        container = sandbox.get(path)[0]
        assert container == self.container

