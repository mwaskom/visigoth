from __future__ import division
import itertools
import numpy as np
from colorspacious import cspace_converter

from psychopy.visual import ElementArrayStim


class RandomDotMotion(object):

    def __init__(self, win,
                 shape="square", size=.05, color=1,
                 density=16.7, speed=5, interval=3,
                 pos=(0, 0), aperture=5, elliptical=True,
                 ):
        """Classical Random Dot Motion stimulus ("Movshon noise").

        """
        if np.isscalar(aperture):
            aperture = [aperture] * 2
        self.aperture = ax, ay = np.asarray(aperture)
        self.elliptical = elliptical

        self.norm = speed * interval / win.framerate
        self.speed = speed
        self.interval = interval
        self.n_dots = int(np.round(density * ax * ay / win.framerate))
        self.reset()

        shape = None if shape == "square" else shape

        array = ElementArrayStim(
            win,
            fieldPos=pos,
            nElements=self.n_dots,
            sizes=size,
            colors=color,
            elementMask=shape,
            elementTex=None,
            xys=next(self.dotpos),
            )

        self.array = array

    def _random_xys(self, n=None):
        """Generate random dot positions within the stimulus aperature."""
        # TODO allow specified random seed
        if n is None:
            n = self.n_dots

        halfx, halfy = self.aperture / 2
        x = np.random.uniform(-halfx, halfx, n)
        y = np.random.uniform(-halfy, halfy, n)

        return np.column_stack([x, y])

    def _update_positions(self, direction, coherence):

        # Get the dots to be drawn on the next frame
        xys = next(self.dotpos)

        # Identify signal dots
        signal = np.random.rand(self.n_dots) < coherence

        # Displace the signal dots
        theta = direction / 180 * np.pi
        dxdy = np.array([[np.cos(theta), -np.sin(theta)]]) * self.norm
        xys[signal] += dxdy

        # Randomly reposition the noise dots
        xys[~signal] = self._random_xys(np.sum(~signal))

        # Wrap-around dots that were displaced out of bounds
        oob = np.any(np.abs(xys) > (self.aperture / 2), axis=1)
        rotmat = np.array([[np.cos(theta), -np.sin(theta)],
                           [np.sin(theta), np.cos(theta)]])
        refmat = np.array([[-1, 0], [0, -1]])
        xfm = np.linalg.inv(rotmat).dot(refmat).dot(rotmat)
        xys[oob] = np.dot(xys[oob] - dxdy, xfm)

        # Identify dots in the corners of an elliptical aperture
        x, y = xys.T
        if self.elliptical:
            a, b = (self.aperture / 2) ** 2
            show = (x ** 2 / a + y ** 2 / b) < 1
        else:
            show = np.ones(self.n_dots)

        # Update the Psychopy object
        self.array.xys = xys
        self.array.opacities = show.astype(float)

        # TODO log dot position somewhere in this object

    def reset(self):
        """Generate random starting positions for each set of dots."""
        self.dotpos = itertools.cycle(
            [self._random_xys() for _ in range(self.interval)]
            )

    def update(self, direction, coherence):
        """Advance the dot animation one frame."""
        self._update_positions(direction, coherence)

    def draw(self):
        """Draw the Psychopy object to the window."""
        self.array.draw()


class RandomDotColorMotion(RandomDotMotion):

    def __init__(self, win,
                 shape="square", size=.05,
                 density=16.7, speed=5, interval=3,
                 lightness=50, chromacity=50,
                 pos=(0, 0), aperture=5, elliptical=True,
                 ):
        """Classical random dot motion stimulus with randomly colored dots.

        """
        init_color = 1
        super(RandomDotColorMotion, self).__init__(
            win, shape, size, init_color, density, speed, interval,
            pos, aperture, elliptical,
            )
        self.lightness = lightness
        self.chromacity = chromacity
        self.jch_to_rgb = cspace_converter("JCh", "sRGB1")

    def jch_to_psychopy_rgb(self, jch):
        """Convert JCh colors to RGB in [-1, 1]."""
        return np.clip(self.jch_to_rgb(jch), 0, 1) * 2 - 1

    def _random_rgbs(self, n=None):
        """Generate random PsychoPy RGB hues with fixed J/C.

        This function will clip RGB values outside of [0, 1]. It's up to the
        user to pick lightness/chromacity values that will keep all colors in
        the gamut if they need exact pairwise color distances.

        """
        # TODO fixed random seed
        if n is None:
            n = self.n_dots

        j = np.ones(n) * self.lightness
        c = np.ones(n) * self.chromacity
        h = np.random.uniform(0, 360, n)
        jch = np.c_[j, c, h]
        rgbs = self.jch_to_psychopy_rgb(jch)

        return rgbs

    def _update_colors(self, hue, coherence):

        # Identify signal dots
        signal = np.random.rand(self.n_dots) < coherence

        # Generate dot colors
        rgbs = self._random_rgbs()
        signal_jch = self.lightness, self.chromacity, hue
        signal_rgb = self.jch_to_psychopy_rgb(signal_jch)
        rgbs[signal] = signal_rgb

        # Update the Psychopy object
        self.array.colors = rgbs

    def update(self, direction, motion_coherence, hue, color_coherence):
        """Advance the dot animation one frame."""
        self._update_positions(direction, motion_coherence)
        self._update_colors(hue, color_coherence)
