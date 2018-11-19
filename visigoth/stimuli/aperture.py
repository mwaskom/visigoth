from psychopy import visual


class BoreAperture(object):

    def __init__(self, win, radius, color):

        self.rect = visual.Rect(win,
                                units="norm",
                                width=1,
                                height=1,
                                fillColor=-1,
                                linecolor=-1)

        self.circle = visual.Circle(win,
                                    radius=radius,
                                    edges=256,
                                    lineColor=color,
                                    fillColor=color,
                                    autoLog=False)

    def draw(self):

        self.rect.draw()
        self.circle.draw()
