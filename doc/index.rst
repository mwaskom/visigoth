.. raw:: html

  <div style="clear: both"></div>
  <div class="container-fluid">
    <div class="row">
      <div class="jumbotron">

========
visigoth
========

Psychophysics experiment control in Python

.. raw:: html

      </div>
    </div>
    <div class="row">
      <div class="col-md-4">
        <div class="panel panel-default">
          <div class="panel-heading">
            <h2 class="panel-title">Documentation Contents</h3>
          </div>
          <div class="panel-body">


.. toctree::
   :maxdepth: 1

   installing
   demo
   commandline
   api

.. raw:: html

          </div>
        </div>
      </div>
      <div class="col-md-8">

``visigoth`` is a library for controlling psychophysics experiments in Python.
It is based on `PsychoPy <https://psychopy.org/>`_ and allows one to fully script
experiments with minimal boilerplate.

To implement an experiment in ``visigoth`` one simply needs to define the logic of
(1) setting up the stimuli, (2) generating parameters for a new trial, and (3)
executing a single trial. All other operations are controlled by ``visigoth``,
although many can be modified by setting parameters or writing code plugins.

``visigoth`` is designed to permit online monitoring of performance and offers a
"remote control" application with real-time display of eyetracker position and
trialwise response data. Additionally, ``visigoth`` offers a library of custom
stimulus classes and functions that are useful for scripting experiments, such
as handling saccadic and manual responses.

.. raw:: html

      </div>
    </div>
  </div>
