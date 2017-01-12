from psychopy import visual


class Point(object):
    """Wrapper for a single psychopy.visual.Circle.

    This object simplifies setting both the fill and line color, and
    accepts ``None`` as a color to set it to the window background.

    It is intended to be used for, e.g., a fixation point.

    """
    def __init__(self, win, radius=.15, color="white", **kwargs):
        """Create the psychopy stimulus object.

        Parameters
        ----------
        win : psychopy Window
            Open PsychoPy window that the stimuli will be linked to.
        radius : float
            Size of the point in ``win`` units.
        color : PsychoPy color
            Initial color for the point.
        kwargs : key, value mappings
            Other keyword arguments are passed to psychopy.visual.Circle.

        """
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
    The ``color`` property will always return a list with the number of colors
    equating to the number of points.

    Performance will suffer for a large number of objects -- in that case, you
    should use an ElementArrayStim.

    It is intended to be used for, e.g., saccade targets.

    """
    def __init__(self, win, pos, radius=.15, color="white", **kwargs):
        """Create the psychopy stimulus objects.

        Parameters
        ----------
        win : psychopy Window
            Open PsychoPy window that the stimuli will be linked to.
        pos : list of tuples
            List of point positions, in ``win`` units.
        color : single PsychoPy color or list of colors.
            Initial color(s) for all or each points.
        radius : float
            Size of the point in ``win`` units.
        kwargs : key, value mappings
            Other keyword arguments are passed to psychopy.visual.Circle.

        """
        self.win = win
        self.dots = []
        for pos_i in pos:
            dot = Point(win, radius=radius, color="white", pos=pos, **kwargs)
            self.dots.append(dot)

        self.color = color

    @property
    def color(self):
        return self._colors

    @color.setter
    def color(self, color):
        """Set point colors as a group or individually for each point."""
        if isinstance(color, list):
            if len(color) == len(self.dots):
                colors = color
            else:
                raise ValueError("Wrong number of colors")
        else:
            colors = [color for _ in self.dots]

        self._colors = colors

        for color, dot in zip(colors, self.dots):
            dot.color = color

    def draw(self):
        for dot in self.dots:
            dot.draw()
