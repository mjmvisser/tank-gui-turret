import os
import tank
import turret.plugins as plugins
from turret.tankscene import Scene
import turret.delegate_fixtures as app

#from nose.tools import assert_raises

os.environ["USER"] = "unknown"

class SceneTestBase(object):
    def setup(self):
        self._delegate = plugins.get_one_delegate(name="test_scene")
        self._scene = Scene(self._delegate)

    def teardown(self):
        self._delegate = None
        self._scene = None

class TestCommitAndPublish(SceneTestBase):
    def setup(self):
        super(TestCommitAndPublish, self).setup()
        app.rename("/tmp/scene.test")
        open("/tmp/ref1.test", "w").close()
        app.add_reference("ref1", "/tmp/ref1.test")
        open("/tmp/ref2.test", "w").close()
        app.add_reference("ref2", "/tmp/ref2.test")
        app.save()

        self._scene = Scene(self._delegate)

    def test_dependencies_match(self):
        assert len(self._scene.dependencies) == 2
        assert self._scene.dependencies[0].data.name == "ref1"
        assert self._scene.dependencies[1].data.name == "ref2"

        scene = self._scene
        ref1 = self._scene.dependencies[0]
        ref2 = self._scene.dependencies[1]

        scene.container = tank.find("animation(shot(sh_0000), sequence(seq_001), department(animation))")
        scene.revision_type = tank.find("xml")
        ref1.container = tank.find("animation(shot(sh_0001), sequence(seq_001), department(animation))")
        ref1.revision_type = tank.find("xml")
        ref2.container = tank.find("animation(shot(sh_0002), sequence(seq_001), department(animation))")
        ref2.revision_type = tank.find("xml")

        scene.publish(description="test")