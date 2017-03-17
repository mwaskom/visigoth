import numpy as np

from psychopy.visual import ElementArrayStim


class RandomDotMotion(object):

    def __init__(self, win,
                 shape="square", size=.05, color=1,
                 density=16.7, speed=5, interval=3,
                 aperture_pos=(0, 0), aperture_size=5, elliptical=True,
                 ):
        """Classical Random Dot Motion stimulus ("Movshon noise").

        """

        shape = None if shape == "square" else shape

        if np.isscalar(aperture_size):
            aperture_size = [aperture_size] * 2 
        self.aperture_size = ax, ay = np.asarray(aperture_size)

        self.n_dots = int(np.round(density * ax * ay / win.framerate))

        array = ElementArrayStim(win,
                                 fieldPos=aperture_pos,
                                 nElements=self.n_dots,
                                 sizes=size,
                                 colors=color,
                                 elementMask=shape,
                                 elementTex=None,
                                 xys=self._random_xys(),
                                 )

        self.array = array
                                 

    def _random_xys(self, n=None):

        if n is None:
            n = self.n_dots

        # TODO allow set random seed
        halfx = self.aperture_size[1] / 2.0
        x = np.random.uniform(-halfx, halfx, n)
        
        halfy = self.aperture_size[0] / 2.0
        y = np.random.uniform(-halfy, halfy, n)

        return np.column_stack([x, y])

    def reset(self):

        pass

    def update(self, direction, coherence):

        self.array.xys = self._random_xys()

    def draw(self):

        self.array.draw()
