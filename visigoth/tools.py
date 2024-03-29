import numpy as np
from scipy import stats
from scipy.spatial import distance

from psychopy import core, event

from .ext.bunch import Bunch


__all__ = [
    "AcquireFixation", "AcquireTarget",
    "check_gaze", "flexible_values", "truncated_sample",
    "limited_repeat_sequence"
]


class AcquireFixation(object):
    """Handler for waiting until subject fixates to begin trial."""
    def __init__(self, exp):

        self.check_eye = exp.p.eye_fixation
        self.check_key = bool(exp.p.key_fixation)

        self.tracker = exp.tracker

        # TODO get from stimulus objects themselves?
        self.fix_pos = exp.p.fix_pos
        self.fix_window = exp.p.fix_window

        if self.check_key:
            key_ready = exp.p.key_fixation
            if not isinstance(key_ready, list):
                key_ready = [key_ready]
            self.keylist = key_ready

        # TODO should probably clear events on initialization

    def __call__(self):
        """Check if fixation has been acquired."""
        fixation = True

        if self.check_key:
            fixation &= bool(event.getKeys(self.keylist))

        if self.check_eye:
            fixation &= self.tracker.check_fixation(self.fix_pos,
                                                    self.fix_window)

        return fixation


class AcquireTarget(object):
    """Handler for waiting until subject makes a eye or key response."""
    def __init__(self, exp, correct_target=None, allow_retry=False):
        self.exp = exp

        self.clock = core.Clock()

        self.check_eye = exp.p.eye_response
        self.check_key = exp.p.key_response
        self.allow_retry = allow_retry

        self.tracker = exp.tracker

        if self.check_eye:
            self.fix_pos = exp.p.fix_pos
            self.fix_window = exp.p.fix_window
            self.target_pos = exp.p.target_pos
            self.target_window = exp.p.target_window
            self.wait_time = self.exp.p.eye_target_wait
            self.hold_time = self.exp.p.eye_target_hold

        if self.check_key:
            self.keylist = exp.p.key_targets  # TODO not a great name?

        self.fix_break_time = None
        self.target_time = None
        self.chosen_target = None
        self.correct_target = correct_target

        # TODO should probably clear events on initialization

    def __call__(self):
        """Check for completion of a valid response."""
        if self.check_key:

            # Check for a press of one of the valid keys
            keys = event.getKeys(self.keyList, timestamped=self.clock)

            # Handle a keypress response
            if keys:

                use_key, use_rt = keys[0]
                response = self.keylist.index(use_key)

                res = Bunch(key_response=True,
                            responded=True,
                            response=response,
                            key=use_key,
                            rt=use_rt)

                if self.correct_target is not None:
                    correct = response == self.correct_target
                    res["correct"] = correct
                    res["result"] = "correct" if correct else "wrong"

                return res

        if self.check_eye:

            now = self.clock.getTime()
            gaze = self.tracker.read_gaze()

            if self.fix_break_time is None:

                if check_gaze(gaze, self.fix_pos, self.fix_window):
                    # The eye is still in the fixation window
                    return False
                else:
                    # The eye has just broken fixation
                    self.fix_break_time = now

            success = False
            failure = False

            for i, pos in enumerate(self.target_pos):

                if check_gaze(gaze, pos, self.target_window):

                    # Check eye has just entered a target window
                    if self.chosen_target is None:
                        self.chosen_target = i
                        self.target_time = now

                    # Check eye used to be on a different target and has moved
                    elif self.chosen_target != i:
                        failure = True

                    # Check eye has successfully held first target
                    if now > (self.target_time + self.hold_time):
                        success = True

                else:

                    # Check eye is no longer holding first target
                    if self.chosen_target == i:
                        failure = True

            # Fail if too much time has elapsed since breaking fixation
            # without landing on a target
            if self.chosen_target is None:
                if now > (self.fix_break_time + self.wait_time):
                    failure = True

            # Handle a successful choice of a target
            # (not neccessarily the right one!)
            if success:

                res = Bunch(eye_response=True,
                            responded=True,
                            response=self.chosen_target,
                            rt=self.fix_break_time,
                            sacc_x=gaze[0],
                            sacc_y=gaze[1])

                if self.correct_target is not None:
                    correct = self.chosen_target == self.correct_target
                    res["correct"] = correct
                    res["result"] = "correct" if correct else "wrong"

                return res

            # Handle a failure to choose a target
            elif failure:

                # Possibly revert from a failed state to a state prior to
                # initiation of the response. Essentially a allow a "retry"
                if self.allow_retry:
                    self.fix_break_time = None
                    self.chosen_target = None
                    self.target_time = None
                    return False

                # Otherwise exit the loop with a "nochoice" result
                res = Bunch(responded=False,
                            result="nochoice",
                            sacc_x=gaze[0],
                            sacc_y=gaze[1])
                return res

            # No determinate result yet
            else:
                return False


def check_gaze(gaze, point, window):
    """Check whether gaze coordinates are on the point.

    Parameters
    ----------
    gaze : 2 tuple
        Gaze coordinates, (x, y).
    point : 2 tuple
        Target location coordiantes, (x, y).
    window : float
        Radius of circular window around ``point`` for accepting gaze location.

    Returns
    -------
    valid : bool
        True if the gaze is within the window of the point.

    """
    if np.isnan(gaze).any():
        return False
    delta = distance.euclidean(gaze, point)
    return delta < window


def flexible_values(val, size=None, random_state=None,
                    min=-np.inf, max=np.inf):
    """Flexibly determine a number of values.

    Input format can be:
        - A numeric value, which will be used exactly.
        - A list of possible values, which will be randomly chosen from.
        - A tuple of (dist, arg0[, arg1, ...]), which will be used to generate
          random observations from a scipy random variable.

    Parameters
    ----------
    val : float, list, or tuple
        Flexibile specification of value, set of values, or distribution
        parameters. See above for more information.
    size : int or tuple, optional
        Output shape. A ``size`` of None implies a scalar result.
    random_state : numpy.random.RandomState object, optional
        Object to allow reproducible random values.
    min, max : float
        Exclusive limits on the return values that are enforced using rejection
        sampling.

    Returns
    -------
    out : scalar or array
        Output values with shape ``size``, or a scalar if ``size`` is 1.

    """
    if random_state is None:
        random_state = np.random.RandomState()

    if isinstance(val, range):
        val = list(val)

    if np.isscalar(val):
        out = np.ones(size, np.array(val).dtype) * val
    elif isinstance(val, list):
        if np.ndim(val) > 1:
            indices = list(range(len(val)))
            idx = random_state.choice(indices, size=size)
            if size is None:
                out = val[idx]
            else:
                out = np.array([val[i] for i in idx])
        else:
            out = random_state.choice(val, size=size)
    elif isinstance(val, tuple):
        rv = getattr(stats, val[0])(*val[1:])
        out = truncated_sample(rv, size, min, max, random_state=random_state)
    else:
        raise TypeError("`val` must be scalar, list, or tuple")

    return out


def truncated_sample(rv, size=1, min=-np.inf, max=np.inf, **kwargs):
    """Iteratively sample from a random variate rejecting values outside limits.

    Parameters
    ----------
    rv : random variate object
        Must have a ``.rvs`` method for generating random samples.
    size : int or tuple, optional
        Output shape.
    min, max : float
        Exclusive limits on the distribution values.
    kwargs : key, value mappings
        Other keyword arguments are passed to ``rv.rvs()``.

    Returns
    -------
    out : array
        Samples from ``rv`` that are within (min, max).

    """
    sample_size = int(1 if size is None else np.prod(size))
    out = np.empty(sample_size)
    replace = np.ones(sample_size, np.bool)
    while replace.any():
        out[replace] = rv.rvs(replace.sum(), **kwargs)
        replace = (out < min) | (out > max)
    if size is None:
        return out.item()
    else:
        return out.reshape(size)


def limited_repeat_sequence(values, max_repeats, random_state=None):
    """Infinite generator with a constraint on number of repeats of each item.

    Parameters
    ----------
    values : list
        Possible values for the sequence.
    max_repeats : int
        Maximum number of times a given value can appear in a row.
    random_state : numpy RandomState, optional
        Object to control random execution.

    """
    if random_state is None:
        random_state = np.random.RandomState()

    def choose_value():
        return values[random_state.randint(0, len(values))]

    first_value = choose_value()
    seqstate = first_value, 1
    yield first_value

    while True:

        next_value = choose_value()

        if seqstate[0] == next_value:
            if seqstate[1] == max_repeats:
                continue
            else:
                seqstate = next_value, seqstate[1] + 1
        else:
            seqstate = next_value, 1

        yield seqstate[0]
