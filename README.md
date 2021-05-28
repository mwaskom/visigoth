# Visigoth: psychophysics experiment presentation

``visigoth`` is a library for controlling psychophysics experiments in Python.
It is based on PsychoPy and allows one to fully script experiments with minimal boilerplate.

To implement an experiment in ``visigoth`` one simply needs to define the logic of (1) setting up the stimuli, (2) generating parameters for a new trial, and (3) executing a single trial. All other operations are controlled by visigoth, although many can be modified by setting parameters or writing code plugins.

``visigoth`` is designed to permit online monitoring of performance and offers a “remote control” application with real-time display of eyetracker position and trial-wise response data. Additionally, visigoth offers a library of custom stimulus classes and functions that are useful for scripting experiments, such as handling saccadic and manual responses.
