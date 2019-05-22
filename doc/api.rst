.. currentmodule:: visigoth
.. _api:

=============
API Reference
=============

Experiment
----------

Main interface
~~~~~~~~~~~~~~

.. autosummary::
   :toctree: api/
   
   Experiment

Methods that must be defined for each study
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: api/

   Experiment.create_stimuli
   Experiment.generate_trials
   Experiment.run_trial

Methods that can be overridden to control execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: api/

   Experiment.define_cmdline_params
   Experiment.serialize_trial_info
   Experiment.save_data
   Experiment.compute_performance
   Experiment.show_performance

Execution methods
~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: api/

   Experiment.trial_count
   Experiment.trial_info
   Experiment.check_abort
   Experiment.wait_until
   Experiment.iti_end
   Experiment.draw
   Experiment.frame_range
   Experiment.check_fixation
   Experiment.show_feedback
   Experiment.flicker

Initialization methods
~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: api/

   Experiment.initialize_params
   Experiment.initialize_data_output
   Experiment.initialize_sounds
   Experiment.initialize_server
   Experiment.initialize_eyetracker
   Experiment.initialize_display
   Experiment.initialize_stimuli
   
Shutdown methods
~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: api/

   Experiment.shutdown_server
   Experiment.shutdown_eyetracker
   Experiment.shutdown_display

Networking methods
~~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: api/

   Experiment.sync_remote_screen
   Experiment.sync_remote_trials
   Experiment.sync_remote_params

Internal execution methods
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: api/

   Experiment.run
   Experiment.wait_for_trigger
   Experiment.wait_for_exit


Tools
-----

.. autosummary::
   :toctree: api/

   AcquireFixation
   AcquireTarget
   check_gaze
   flexible_values
   truncated_sample
   limited_repeat_sequence


Stimuli
-------

Fixation points, saccade targets, and spatial cues
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: api/

   stimuli.Point
   stimuli.Points
   stimuli.LineCue
   stimuli.PointCue
   stimuli.FixationTask

Random dot motion
~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: api/

   stimuli.RandomDotMotion
   stimuli.RandomDotColorMotion

Gratings, hyperplaids, and noise fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: api/

   stimuli.Grating
   stimuli.ElementArray
   stimuli.Pattern
   stimuli.GaussianNoise
   stimuli.UniformNoise

Apertures
~~~~~~~~~

.. autosummary::
   :toctree: api/

   stimuli.BoreAperture
   stimuli.StimAperture

Simulated gaze position
~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: api/

   stimuli.GazeStim

Eye Tracking
------------

.. autosummary::
   :toctree: api/

   eyetracker.EyeTracker
