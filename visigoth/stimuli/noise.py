from __future__ import division
import numpy as np
from scipy import stats
from psychopy.visual import ImageStim


class Noise(object):

    def __init__(self, win, contrast, pix_per_deg, **kwargs):

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

        vals = self.rv.rvs(size=self.size, random_state=rng)
        vals = np.clip(vals, -1, 1)
        self.image.image = vals

    def draw(self):
        """Draw the stimulus to the window."""
        self.image.draw()


class GaussianNoise(Noise):
    """Noise field with Gaussian statistics parameterized by contrast."""
    def __init__(self, win, contrast=1, pix_per_deg=None, **kwargs):

        self._constant = .7  # Approximately matches RMS contrast of grating
        self.mean = win.color.mean(axis=-1)
        self.contrast = contrast

        super(GaussianNoise, self).__init__(
            win, contrast, pix_per_deg, **kwargs)

        self.update()

    def _set_rv(self, contrast):

        self.sd = (self.mean + 1) * self._constant * contrast
        self.rv = stats.norm(self.mean, self.sd)


class UniformNoise(Noise):
    """Noise field with uniform statistics parameterized by contrast."""
    def __init__(self, win, contrast=1, pix_per_deg=None, **kwargs):

        self.mean = win.color.mean(axis=-1)
        self.contrast = contrast

        super(UniformNoise, self).__init__(
            win, contrast, pix_per_deg, **kwargs)

        self.update()

    def _set_rv(self, contrast):

        mean = (self.mean + 1) / 2
        range = contrast * (2 * mean)
        low = mean - range / 2
        low, range = low * 2 - 1, range * 2
        self.rv = stats.uniform(low, range)
