from itertools import cycle

from psychopy.visual import GratingStim
from .points import Point
from ..tools import flexible_values


class FixationTask(object):

    def __init__(self, win, clock, colors, duration, radius, pos=(0, 0)):

        self.clock = clock
        self.colors = cycle(colors)
        self.duration = duration
        self.next_change = flexible_values(duration)
        self.change_times = []

        self.point = Point(
            win=win,
            pos=pos,
            radius=radius,
            color=next(self.colors),
        )

        self.halo = GratingStim(
            win=win,
            pos=pos,
            size=radius * 10,
            mask="gauss",
            tex=None,
            color=win.color,
        )

    def draw(self):

        now = self.clock.getTime()
        if now > self.next_change:
            self.point.color = next(self.colors)
            self.next_change += flexible_values(self.duration)
            self.change_times.append(now)

        self.halo.draw()
        self.point.draw()
