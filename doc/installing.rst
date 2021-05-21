.. _installing:

==========
Installing
==========

visigoth depends on `psychopy <https://www.psychopy.org/>`_ and its
dependencies and on some libraries from the broader scientific Python ecosystem,
including numpy, scipy, and pandas. See the `psychopy` docs for up-to-date
information on the best way to install it. Note that you will *not* want to
use a "Standalone" installation. The suggested approach is to install using
``conda`` into a dedicated environment.

Getting eye tracking working will also require the SR Research ``pylink``
library which, last checked, had to be downloaded (in compiled bytecode) from
the SR research support forums. There is more information in the
`psychopy docs <https://www.psychopy.org/api/hardware/pylink.html>`_.

Once the dependencies are satisfied, visigoth should be installed from a
local source checkout using ``pip install .``.
