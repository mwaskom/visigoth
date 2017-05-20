import version
__version__ = version.__version__

from .experiment import Experiment
from .tools import (AcquireFixation, AcquireTarget,
                    flexible_values, limited_repeat_sequence)
from .ext.bunch import Bunch
