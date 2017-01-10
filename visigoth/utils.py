import numpy as np
from scipy import stats


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
