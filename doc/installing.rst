.. _installing:

==========
Installing
==========

``visigoth`` depends on `psychopy <https://www.psychopy.org/>`_ and its
dependencies and on some libraries from the broader scientific Python ecosystem,
including numpy, scipy, and pandas. See the ``psychopy`` `install docs`_ for up-to-date
information on the best way to install it. Note that you will *not* want to
use a "Standalone" installation. The suggested approach is to install using
``conda`` into a dedicated `environment`_.

Getting eye tracking working will also require the SR Research ``pylink``
library which, last checked, had to be downloaded (as bytecode) from
the SR research support forums. There is more information in the
`psychopy docs <https://www.psychopy.org/api/hardware/pylink.html>`_.

Once the dependencies are satisfied, visigoth should be installed by doing
``pip install .`` from a local source checkout.


.. _install docs: https://www.psychopy.org/download.html#manual-installations
.. _environment: https://conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html