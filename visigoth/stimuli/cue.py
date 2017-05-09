# TODO BOTH CLASSES HERE NEED DOCUMENTATION
import numpy as np
from psychopy import visual


class LineCue(object):

    def __init__(self, win, extent=(0, 1), width=5, color=1, **kwargs):

        self.extent = extent
        stim = visual.Line(win,
                           lineWidth=width,
                           lineColor=color,
                           autoLog=False,
                           **kwargs)

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


class PointCue(object):

    def __init__(self, win, norm, radius, color=1, **kwargs):

        self.norm = norm
        stim = visual.Circle(win,
                             radius=radius,
                             fillColor=color,
                             lineColor=color,
                             interpolate=True,
                             autoLog=False,
                             **kwargs)
        self.stim = stim

    @property
    def pos(self):

        return self._pos

    @pos.setter
    def pos(self, val):

        self._pos = val
        val = np.asarray(val)
        direction = val / np.linalg.norm(val)
        self.stim.pos = direction * self.norm

    def draw(self):

        self.stim.draw()
