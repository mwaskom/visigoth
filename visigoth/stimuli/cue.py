import numpy as np
from psychopy import visual


class LineCue(object):

    def __init__(self, win, extent=(0, 1), width=5, color=1):

        self.extent = extent
        stim = visual.Line(win,
                           lineWidth=width,
                           lineColor=color)

        self.stim = stim

    @property
    def pos(self):

        return self._pos

    @pos.setter
    def pos(self, val):

        self._pos = val
        val = np.asarray(val)
        direction = val / np.linalg.norm(val)
        self.stim.start = direction * self.extent[0]
        self.stim.end = direction * self.extent[1]

    def draw(self):

        self.stim.draw()
