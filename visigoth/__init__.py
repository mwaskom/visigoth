import version
__version__ = version.__version__

from .experiment import Experiment
from .tools import AcquireFixation, AcquireTarget, flexible_values
from .ext.bunch import Bunch
