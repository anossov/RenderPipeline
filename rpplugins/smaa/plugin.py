"""

RenderPipeline

Copyright (c) 2014-2016 tobspr <tobias.springer1@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

"""

from panda3d.core import SamplerState

from rpcore.globals import Globals
from rpcore.pluginbase.base_plugin import BasePlugin

from .smaa_stage import SMAAStage

class Plugin(BasePlugin):

    name = "SMAA (Antialiasing)"
    author = "tobspr <tobias.springer1@gmail.com>"
    description = ("This plugin adds support for SMAA, a post process "
                   "antialiasing technique.")
    version = "1.5"

    def on_stage_setup(self):
        if self.get_setting("use_reprojection"):
            self._jitter_index = 0
            self._compute_jitters()

        self._pipeline.stage_mgr.define("SMAA_HISTORY_LENGTH", self.history_length)

        self._smaa_stage = self.create_stage(SMAAStage)
        self._smaa_stage.use_reprojection = self.get_setting("use_reprojection")
        self._load_textures()

    def on_pre_render_update(self):
        # Apply jitter for temporal aa
        if self.get_setting("use_reprojection"):
            jitter = self._jitters[self._jitter_index]
            Globals.base.camLens.set_film_offset(jitter)
            self._smaa_stage.set_jitter_index(self._jitter_index)

            # Increase jitter index
            self._jitter_index += 1
            if self._jitter_index >= len(self._jitters):
                self._jitter_index = 0

    def _compute_jitters(self):
        """ Internal method to compute the SMAA sub-pixel frame offsets """
        self._jitters = []

        scale = 1.0 / float(Globals.base.win.get_x_size())
        # scale *= 0

        # for x, y in ((-0.5, 0.25), (0.5, -0.25), (0.25, 0.5), (-0.25, -0.5)):
        for x, y in ((-0.25, 0.25), (0.25, -0.25)):
            # The get_x_size() for both dimensions is not an error - its due to
            # how the OrtographicLens works internally.
            jitter_x = (x * 2 - 1) * scale * 0.5
            jitter_y = (y * 2 - 1) * scale * 0.5
            self._jitters.append((jitter_x, jitter_y))

    @property
    def history_length(self):
        if self.get_setting("use_reprojection"):
            return len(self._jitters)
        return 1

    def _load_textures(self):
        """ Loads all required textures """
        search_tex = Globals.loader.load_texture(self.get_resource("search_tex.png"))
        area_tex = Globals.loader.load_texture(self.get_resource("area_tex.png"))

        for tex in [search_tex, area_tex]:
            tex.set_minfilter(SamplerState.FT_linear)
            tex.set_magfilter(SamplerState.FT_linear)
            tex.set_wrap_u(SamplerState.WM_clamp)
            tex.set_wrap_v(SamplerState.WM_clamp)

        self._smaa_stage.area_tex = area_tex
        self._smaa_stage.search_tex = search_tex
