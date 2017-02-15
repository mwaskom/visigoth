from __future__ import division
import numpy as np
from scipy import stats
from psychopy.visual import ImageStim


class GaussianNoise(object):
    """Noise field with Gaussian statistics parameterized by contrast."""
    def __init__(self, win, contrast=1, pix_per_deg=None, **kwargs):

        self._contrast = contrast
        self._constant = .7  # Approximately matches RMS contrast of grating
        self.mean = win.color.mean(axis=-1)
        self.sd = (self.mean + 1) * self._constant * contrast
        self.rv = stats.norm(self.mean, self.sd)

        self.image = image = ImageStim(win, **kwargs)
        if pix_per_deg is None:
            pix_per_deg = win.pix_per_deg
        self.size = np.ceil(image.size * pix_per_deg).astype(int)

        self.update()

    @property
    def contrast(self):
        """Control on 0-1 scale, approximately matched to a grating."""
        return self._contrast

    @contrast.setter
    def contrast(self, val):
        """Control on 0-1 scale, approximately matched to a grating."""
        self.sd = (self.mean + 1) * self._constant * val
        self.rv = stats.norm(self.mean, self.sd)
        self._contrast = val

    @property
    def opacity(self):
        """Opacity of the stimulus."""
        return self.image.opacity

    @opacity.setter
    def opacity(self, val):
        """Opacity of the stimulus."""
        self.image.opacity = val

    def update(self, rng=None):

        if rng is None:
            rng = np.random.RandomState()

        vals = self.rv.rvs(size=self.size, random_state=rng)
        vals = np.clip(vals, -1, 1)
        self.image.image = vals

    def draw(self):

        self.image.draw()
