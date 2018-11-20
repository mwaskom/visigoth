from psychopy import visual


class BoreAperture(object):

    def __init__(self, win, color, radius, pos):

        self.rect = visual.Rect(win,
                                units="norm",
                                width=2,
                                height=2,
                                fillColor=-1,
                                lineColor=-1)

        self.circle = visual.Circle(win,
                                    radius=radius,
                                    pos=pos,
                                    edges=256,
                                    fillColor=color,
                                    lineColor=color,
                                    autoLog=False)

    def draw(self):

        self.rect.draw()
        self.circle.draw()