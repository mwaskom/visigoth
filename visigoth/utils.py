import numpy as np
from scipy import stats
from scipy.spatial import distance

from psychopy import core, event


class AcquireFixation(object):

    def __init__(self, exp):

        self.check_eye = exp.p.get("eye_fixation", False)
        self.check_key = exp.p.get("key_fixation", False)

        self.tracker = exp.tracker

        # TODO get from stimulus objects themselves?
        self.fix_pos = exp.p.get("fix_pos", (0, 0))
        self.fix_window = exp.p.get("fix_window", 2)

        key_ready = exp.p.get("key_ready", "space")
        if not isinstance(key_ready, list):
            key_ready = [key_ready]
        self.keylist = key_ready

        event.clearEvents()

    def __call__(self):

        fixation = False

        if self.check_key:
            fixation &= bool(event.getKeys(self.keylist))

        if self.check_eye:
            fixation &= self.tracker.check_fixation(self.fix_pos,
                                                    self.fix_window)

        return fixation


class AcquireTarget(object):

    def __init__(self, exp):

        self.clock = core.Clock()

        self.check_eye = exp.p.get("eye_response", False)
        self.check_key = exp.p.get("key_response", False)

        self.tracker = exp.tracker

        if self.check_eye:
            self.fix_pos = exp.p.get("fix_pos", (0, 0))
            self.fix_window = exp.p.fix_window
            self.target_pos = exp.p.target_pos
            self.target_window = exp.p.target_window

        if self.check_key:
            self.keylist = exp.p.key_targets

        self.wait_time = self.exp.p.eye_target_wait
        self.hold_time = self.exp.p.eye_target_hold

        self.fix_break_time = None
        self.target_time = None
        self.chosen_target = None

        event.clearEvents()

    def __call__(self):

        if self.check_key:

            keys = event.getKeys(self.keyList)
            if keys:
                for key in keys:
                    choice = self.keylist.index(key)
                    return (True, choice)

        if self.check_eye:

            now = self.clock.getTime()
            gaze = self.tracker.read_gaze()

            if self.fix_break_time is None:

                if check_gaze(gaze, self.fix_pos, self.fix_window):
                    # The eye is still in the fixation window
                    return False
                else:
                    # The eye has just broken fixation
                    self.fix_break_time = self.clock.getTime()

            success = False
            failure = False

            for i, pos in enumerate(self.target_pos):

                if check_gaze(gaze, pos, self.target_window):

                    if self.chosen_target is None:
                        # The eye has just entered a target window
                        self.chosen_target = i
                        self.target_time = now
                    elif self.chosen_target != i:
                        # The eye used to be on a different target and has moved
                        failure = True

                    if now > (self.target_time + self.hold_time):
                        # The eye has successfully held the target
                        success = True

                else:

                    if self.chosen_target == i:
                        # The eye had acquired this target but then lost it
                        failure = True

            if success:
                return True, self.first_target
            elif failure:
                return True, None
            elif now > (self.fix_break_time + self.wait_time):
                # The time to find a target has elapsed unsuccessfully
                return (True, None)
            else:
                # No determinate result yet
                return False


def wait_until(func, timeout=np.inf, sleep=0, win=None, stims=None,
               args=(), **kwargs):

    clock = core.Clock()

    stims = [] if stims is None else stims

    while clock.getTime() < timeout:

        func_val = func(*args, **kwargs)

        if func_val:
            return func_val

        if sleep:
            core.wait(sleep, sleep)

        else:
            for stim in stims:
                stim.draw()
            win.flip()


def check_gaze(gaze, point, window):
    """Check whether gaze coordinates are on the point."""
    if np.isnan(gaze).any():
        return False
    delta = distance.euclidean(gaze, point)
    return delta < window


def flexible_values(val, size=1, random_state=None, min=-np.inf, max=np.inf):
    """Flexibly determine a number of values.
    Input format can be:
        - A numeric value, which will be used exactly.
        - A list of possible values, which will be randomly chosen from.
        - A tuple of (dist, arg0[, arg1, ...]), which will be used to generate
          random observations from a scipy random variable.
    """
    if random_state is None:
        random_state = np.random.RandomState()

    if np.isscalar(val):
        out = np.ones(size, np.array(val).dtype) * val
    elif isinstance(val, list):
        out = random_state.choice(val, size=size)
    elif isinstance(val, tuple):
        rv = getattr(stats, val[0])(*val[1:])
        out = truncated_sample(rv, size, min, max, random_state=random_state)
    else:
        raise TypeError("`val` must be scalar, set, or tuple")

    if size == 1:
        out = out.item()

    return out


def truncated_sample(rv, size=1, min=-np.inf, max=np.inf, **kws):
    out = np.empty(np.prod(size))
    replace = np.ones(np.prod(size), np.bool)
    while replace.any():
        out[replace] = rv.rvs(replace.sum(), **kws)
        replace = (out < min) | (out > max)
    return out.reshape(size)
