from __future__ import division
import numpy as np
from scipy import stats
from psychopy.visual import ImageStim


class Noise(object):

    def __init__(self, win, contrast, pix_per_deg, **kwargs):

        self.win = win
        self.image = ImageStim(win, **kwargs)
        if pix_per_deg is None:
            pix_per_deg = win.pix_per_deg
        self.size = np.ceil(self.image.size * pix_per_deg).astype(int)

    @property
    def contrast(self):
        """Control on 0-1 scale, approximately matched to a grating."""
        return self._contrast

    @contrast.setter
    def contrast(self, val):
        """Control on 0-1 scale, approximately matched to a grating."""
        self._set_rv(val)
        self._contrast = val

    # TODO we should be able to automatically generate these interface methods
    @property
    def opacity(self):
        """Opacity of the stimulus."""
        return self.image.opacity

    @opacity.setter
    def opacity(self, val):
        """Opacity of the stimulus."""
        self.image.opacity = val

    @property
    def pos(self):
        """Position of the stimulus."""
        return self.image.pos

    @pos.setter
    def pos(self, val):
        """Position of the stimulus."""
        self.image.pos = val

    def update(self, rng=None):
        """Generate new random values."""
        if rng is None:
            rng = np.random.RandomState()

        # TODO add flag to force an update on draw() if contrast has changed?

        vals = self.rv.rvs(size=self.size, random_state=rng)

        # TODO this clip doesn't account for drawing on nonzero background
        vals = np.clip(vals, -1, 1)
        self.image.image = vals

    def draw(self):
        """Draw the stimulus to the window."""
        self.win.blendMode = "add"
        self.image.draw()
        self.win.blendMode = "avg"


class GaussianNoise(Noise):
    """Noise field with Gaussian statistics parameterized by contrast."""
    def __init__(self, win, contrast=1, pix_per_deg=None, **kwargs):

        super(GaussianNoise, self).__init__(
            win, contrast, pix_per_deg, **kwargs)

        self._constant = .7  # Approximately matches RMS contrast of grating
        self.mean = 0
        self.contrast = contrast

        self.update()

    def _set_rv(self, contrast):

        # Scale "Michelson contrast" by background
        scaling_factor = self.win.background_color + 1

        # Convert from "Michelson" contrast to gaussian RMS
        self.sd = scaling_factor * self._constant * contrast

        self.rv = stats.norm(self.mean, self.sd)


class UniformNoise(Noise):
    """Noise field with uniform statistics parameterized by contrast."""
    def __init__(self, win, contrast=1, pix_per_deg=None, **kwargs):

        super(UniformNoise, self).__init__(
            win, contrast, pix_per_deg, **kwargs)

        self.mean = 0
        self.contrast = contrast

        self.update()

    def _set_rv(self, contrast):

        # Scale Michelson contrast by background
        scaling_factor = self.win.background_color + 1

        # Determine width and the lower bound of the interval
        # (This is the scipy parameterization not [low, high])
        width = scaling_factor * contrast
        low = self.mean - width / 2

        # Multiply by 2 as values are in [-1, 1]
        low, width = low * 2, width * 2

        self.rv = stats.uniform(low, width)
