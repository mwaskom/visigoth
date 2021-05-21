.. _user_guide:

==========
User Guide
==========

Command-line help
-----------------

``visigoth``
~~~~~~~~~~~~

.. argparse::
   :module: visigoth.commandline
   :func: define_experiment_parser
   :prog: visigoth
   :nodefault:

``visigoth-remote``
~~~~~~~~~~~~~~~~~~~

.. argparse::
   :module: visigoth.commandline
   :func: define_remote_parser
   :prog: visigoth-remote
   :nodefault:


Code example: Random dot task
-----------------------------

.. code-block:: bash

    random_dots/
        experiment.py
        params.py
        remote.py

Experiment module (``experiment.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../examples/random_dots/experiment.py

Parameters module (``params.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../examples/random_dots/params.py

Remote module (``remote.py``)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../examples/random_dots/remote.py
