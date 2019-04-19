import numpy as np
from psychopy import visual, tools


class BoreAperture(object):

    def __init__(self, win, radius, pos):

        pix_w = win.size[0]
        w = tools.monitorunittools.pix2deg(pix_w, win.monitor)

        n_circ = 1024
        a = np.linspace(0, np.pi * 2, n_circ)
        r = np.full(n_circ, radius)

        verts = np.c_[r * np.cos(a), r * np.sin(a)] + pos
        wx, wy = np.add(w, pos)
        exterior = [
            (wx, pos[1]), (wx, wy), (-wx, wy),
            (-wx, -wy), (wx, -wy), (wx, pos[1])
        ]
        verts = np.r_[verts, exterior]

        self.stim = visual.ShapeStim(win,
                                     vertices=verts,
                                     fillColor=-1,
                                     lineColor=-1,
                                     lineWidth=0,
                                     autoLog=False)

    def draw(self):

        self.stim.draw()


class StimAperture(object):

    def __init__(self, win, radius):

        pix_w = win.size[0] / 2
        w = tools.monitorunittools.pix2deg(pix_w, win.monitor)

        n_circ = 512
        a = np.linspace(0, np.pi * 2, n_circ)
        r = np.full(n_circ, radius)

        verts = np.c_[r * np.cos(a), r * np.sin(a)]
        exterior = [(w, 0), (w, w), (-w, w), (-w, -w), (w, -w), (w, 0)]
        verts = np.r_[verts, exterior]

        self.stim = visual.ShapeStim(win,
                                     vertices=verts,
                                     fillColor=win.color,
                                     lineColor=win.color,
                                     lineWidth=0,
                                     autoLog=False)

    def draw(self):

        self.stim.draw()
