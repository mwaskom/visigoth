"""Contrast pattern created by averaging gratings at different orientations.

"""
import numpy as np
from .elementarray import ElementArray


class Pattern(object):
    """Contrast pattern created by averaging oriented gratings."""
    def __init__(self, win, n, pos=(0, 0), contrast=None, **kwargs):
        """Initialize the psychopy object.

        This object ultimately wraps a PsychoPy ElementArrayStim object,
        which draws a number of GratingStim objects with high performance.

        Keyword arguments should correspond to ElementArrayStim.

        """
        self.n = n

        opacities = 1 / np.linspace(1, n, n)
        oris = np.linspace(0, 180, n + 1)[:n]
        xys = np.tile(pos, n).reshape(n, 2)

        # The main object is our own wrapper around the Psychopy
        # ElementArrayStim object, which takes the luminance pedestal from
        # the window background
        array = ElementArray(win,
                             xys=xys,
                             oris=oris,
                             opacities=opacities,
                             nElements=n,
                             **kwargs
                             )
        self.array = array

        if contrast is None:
            contrast = 1 / np.sqrt(n)
        self.contrast = contrast
        self.randomize_phases()

    @property
    def contrast(self):
        """Visual contrast of the pattern.

        This corresponds to the Michelson contrast of a single grating with a
        similar RMS contrast to the pattern stimulus.

        """
        return self._contrast

    @contrast.setter
    def contrast(self, val):
        """Set the contrast value, adjusting for the number of elements.

        Note that the contrast cannot exceed 1 / sqrt(n) or else it is possible
        that there will be pixel values out of range.

        """
        individual_val = val * np.sqrt(self.n)
        if individual_val > 1:
            raise ValueError("Illegal contrast value")
        self.array.pedestal_contrs = individual_val
        self._contrast = val

    @property
    def pos(self):
        """Position of the elements."""
        return self._pos

    @pos.setter
    def pos(self, val):
        """Set the position of the elements."""
        xys = np.tile(val, self.n).reshape(self.n, 2)
        self.array.xys = xys
        self._pos = val

    def draw(self):
        """Draw the element array on the window."""
        self.array.draw()

    def randomize_phases(self, rng=None):
        """Set the phase of each underlying grating to a random value."""
        if rng is None:
            rng = np.random.RandomState()
        self.phases = rng.uniform(0, 1, self.n)
        self.array.phases = self.phases
