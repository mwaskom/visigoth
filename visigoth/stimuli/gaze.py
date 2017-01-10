import numpy as np
from psychopy.visual.grating import GratingStim


class GazeStim(GratingStim):
    """Stimulus linked to eyetracker that shows gaze location."""
    def __init__(self, win, tracker):

        self.tracker = tracker
        super(GazeStim, self).__init__(win,
                                       autoDraw=True,
                                       autoLog=False,
                                       color="skyblue",
                                       mask="gauss",
                                       size=1,
                                       tex=None)

    def draw(self):

        gaze = self.tracker.read_gaze(log=False, apply_offsets=False)
        if np.isfinite(gaze).all():
            self.pos = gaze
            self.opacity = 1
        else:
            self.opacity = 0
        super(GazeStim, self).draw()
