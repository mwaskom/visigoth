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
   Experiment.run

Methods that must be defined for each study
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
   :toctree: api/

   Experiment.create_stimuli
   Experiment.generate_trials
   Experiment.run_trial

Methods that can be overidden to control execution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
   Experiment.initialize_display_info
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

   Experiment.wait_for_trigger
   Experiment.wait_for_exit


Experiment tools
----------------

.. autosummary::
   :toctree: api/

   AcquireFixation
   AcquireTarget
   check_gaze
   flexible_values
   truncated_sample
   limited_repeat_sequence
