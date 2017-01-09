from psychopy import visual

class Point(object):
    """Wrapper for a single psychopy.visual.Circle.

    This object simplifies setting both the fill and line color, and
    accepts ``None`` as a color to set it to the window background.

    It is intended to be used for, e.g., a fixation point.

    """
    def __init__(self, win, color="white", radius=.15, **kwargs):

        self.win = win
        self.dot = visual.Circle(win,
                                 radius=radius,
                                 fillColor=color,
                                 lineColor=color,
                                 interpolate=True,
                                 autoLog=False,
                                 **kwargs)

        self._color = color

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        if color is None:
            color = self.win.color
        self._color = color
        self.dot.setFillColor(color)
        self.dot.setLineColor(color)

    def draw(self):
        self.dot.draw()


class Points(object):
    """Wrapper for multiple psychopy.visual.Circle objects.

    In addition to the abstractions afforded by the Point object, this object
    also allows you to set the color with a single color or list of colors.

    Performance will suffer for a large number of objects -- in that case, you
    should use an ElementArrayStim.

    It is intended to be used for, e.g., saccade targets.

    """
    def __init__(self, win, pos, color="white", radius=.15):

        self.win = win
        self.dots = []
        for pos_i in pos:
            dot = Point(win, color, radius, pos=pos)
            self.dots.append(dot)

        self._colors = color

    @property
    def color(self):
        return self._colors

    @color.setter
    def color(self, color):
        if isinstance(color, list):
            if len(color) == len(self.dots):
                colors = color
            else:
                raise ValueError("Wrong number of colors")
        else:
            colors = [color for _ in self.dots]

        for color, dot in zip(colors, self.dots):
            dot.color = color

    def draw(self):
        for dot in self.dots:
            dot.draw()
