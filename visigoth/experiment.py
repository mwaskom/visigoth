"""Definition of the Experiment object that control most things."""
from __future__ import division
import os
import time
import argparse

import yaml
import numpy as np
import pandas as pd

from psychopy import core, visual, monitors

from .ext.bunch import Bunch
from . import stimuli, eyetracker


class Experiment(object):

    def __init__(self, arglist=None):

        self.arglist = [] if arglist is None else arglist

        self.p = None
        self.s = None
        self.win = None
        self.tracker = None
        self.server = None

        self.clock = core.Clock()

        self.trial_data = []

    def run(self):

        # Everything is wrapped in a try block so that errors will exit out
        # properly and not destroy data or leave hanging connections.

        try:

            # Experiment initialization

            self.initialize_params()
            self.initialize_data_output()
            self.initialize_server()
            self.initialize_eyetracker()
            self.initialize_display()
            self.initialize_stimuli()

            # TODO add scanner trigger/dummy scans
            # TODO add clock reset, eyetracker start, other onset code
            self.clock.reset()

            # Main experimental loop

            for trial_info in self.generate_trials():

                trial_info = self.run_trial(trial_info)
                self.trial_data.append(trial_info)
                self.update_client(trial_info)

        finally:

            # Experiment shutdown

            self.save_data()
            self.shutdown_server()
            self.shutdown_eyetracker()
            self.shutdown_display()

    # ==== Study-specific functions ====

    # In most (but not all) cases, these methods will be overloaded by the user

    def define_cmdline_params(self, parser):
        """Augment the command line parser to set params at runtime."""
        pass

    def create_stimuli(self):
        """Initialize study-specific stimulus objects.

        This method must be defined for each study.

        It should return a dictionary that maps stimulus names to the objects
        themselves. The objects can be anything that follow the basic stimulus
        API--namely, they need to define a ``draw`` method. They will end up
        in the Experiment.s namespace.

        """
        raise NotImplementedError

    def generate_trials(self):
        """Generator that yields data for each trial.

        This method must be defined for each study.

        It should be written as a generator, which allows flexibility as to
        whether the trial information will be fully defined before the run
        or on the fly.

        It should yield an object that provides trial-specific parameters.
        This will typically be a pandas Series, but other datatypes are fine
        as long as the ``run_trial`` method knows how to handle it.

        The generator is iterated between each trial, so if it is going to do
        substantial computation, you will need to be mindful to specify a
        sufficient ITI distribution.

        """
        raise NotImplementedError

    def run_trial(self, trial_info):
        """Execute an individual trial of the experiment.

        This method must be defined for each study.

        It should accept a trial_info argument and return the object, possibly
        with updated values or additional data. This can be any type of object
        but it should be coordinated with the other methods. Specifically, the
        handling of the input should correspond with what is yielded by the
        ``generate_trials`` method, and the output should be something that the
        ``update_client`` and ``save_data`` methods knows how to handle. It is
        easiest for this to be a pandas Series, so that those methods do not
        need to be overloaded, but this is not strictly required to allow for
        more complicated designs.

        """
        raise NotImplementedError

    def update_client(self, trial_info):
        """Send the trial results to the experiment client.

        If the object returned by ``run_trial`` is a pandas Series, it's not
        necessary to overload this function. However, it can be defined for each
        study to allow for more complicated data structures.

        """
        pass

    def save_data(self):
        """Write out data files at the end of the run.

        If the object returned by ``run_trial`` is a pandas Series and you
        don't want to do anything special at the end of the experiment, it's
        not necessary to overload this function. Howver, it can be defined for
        each study to allow for more complicated data structures or exit logic.

        """
        if self.trial_data and self.p.save_data:
            data = pd.DataFrame(self.trial_data)
            out_fname = self.output_stem + "_trials.csv"
            data.to_csv(out_fname, index=False)

    # ==== Initialization functions ====

    def initialize_params(self):
        """Determine parameters for this run of the experiment."""

        # Import the params module and extract the params for this run
        import params
        p = Bunch(getattr(params, self.arglist[0]))

        # Define common command-line interface
        parser = argparse.ArgumentParser()
        parser.add_argument("mode")
        parser.add_argument("-subject", default="test")
        parser.add_argument("-run", type=int, default=1)
        parser.add_argument("-nosave", action="store_false", dest="save_data")
        parser.add_argument("-debug", action="store_true")

        # Add study-specific command line arguments
        self.define_cmdline_params(parser)

        # Parse the command line arguments into parameters
        args = parser.parse_args(self.arglist)
        p.update(args.__dict__)

        # Timestamp the execution and add to parameters
        timestamp = time.localtime()
        p.timestamp = timestamp
        p.date = time.strftime("%Y-%m-%d", timestamp)
        p.time = time.strftime("%H-%M-%S", timestamp)

        self.p = p
        self.debug = args.debug

    def initialize_data_output(self):
        """Define stem for output filenames and ensure directory exists."""
        default_template = "data/{subject}/{date}/{time}"
        template = self.p.get("output_template", default_template)
        output_stem = template.format(**self.p)

        output_dir = os.path.dirname(output_stem)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self.output_stem = output_stem

    def initialize_server(self):
        """Start a server in an independent thread for experiment control."""
        pass

    def initialize_eyetracker(self):
        """Connect to and calibrate eyetracker."""
        if self.p.monitor_eye:

            # Determine the screen background color during calibration
            # Currently I'm not sure how to get iohub to apply gamma correction
            # so we need to do that ourselves here.
            with open("displays.yaml") as fid:
                display_info = yaml.load(fid)
            info = display_info[self.p.display_name]
            ratio = self.p.display_luminance / info["max_luminance"]
            color = int(round(ratio ** (1 / info["gamma"]) * 255))

            # Configure and calibrate the eyetracker
            self.tracker = eyetracker.EyeTracker(self, color)
            self.tracker.run_calibration()

    def initialize_display(self):
        """Open the PsychoPy window to begin the experiment."""

        # Extract the relevant display information
        with open("displays.yaml") as fid:
            display_info = yaml.load(fid)
        info = display_info[self.p.display_name]

        # Determine the background color of the display
        color = self.p.display_luminance / info["max_luminance"] * 2 - 1

        # Define information about the monitor
        monitor = monitors.Monitor(name=self.p.display_name,
                                   width=info["width"],
                                   distance=info["distance"],
                                   gamma=info["gamma"],
                                   autoLog=False)
        monitor.setSizePix(info["resolution"])

        # Open the psychopy window
        self.win = win = visual.Window(units="deg",
                                       screen=0,
                                       fullscr=True,
                                       allowGUI=False,
                                       color=color,
                                       size=info["resolution"],
                                       monitor=monitor)

        # Test window performance
        win.setRecordFrameIntervals(True)
        frametime, _, _ = visual.getMsPerFrame(win)
        refresh_hz = 1000 / frametime
        refresh_error = abs(info["refresh_hz"] - refresh_hz)
        if refresh_error > .5:
            text = "Display refresh rate differs from expected by {:.2} Hz"
            raise RuntimeError(text.format(refresh_error))

        win.frametime = frametime
        win.refresh_hz = refresh_hz

        # Initialize the gaze stimulus
        if self.p.monitor_eye and self.p.eye_simulate:
            stimuli.GazeStim(win, self.tracker)

    def initialize_stimuli(self):
        """Setup stimulus objects."""
        self.s = Bunch(self.create_stimuli())

    # ==== Shutdown functions ====

    def shutdown_server(self):
        """Cleanly close down the experiment server process."""
        if self.server is None:
            return

    def shutdown_eyetracker(self):
        """End Eyetracker recording and save eyetracker log files."""
        if self.tracker is not None:
            self.tracker.shutdown()

    def shutdown_display(self):
        """Cleanly exit out of the psychopy window."""
        if self.win is not None:
            self.win.close()

    # === Execution functions

    def wait_until(func, timeout=np.inf, sleep=0, win=None, stims=None,
                   args=(), **kwargs):

        clock = core.Clock()

        stims = [] if stims is None else stims

        while clock.getTime() < timeout:

            func_val = func(*args, **kwargs)

            if func_val:
                return func_val

            if sleep:
                core.wait(sleep, sleep)

            else:
                for stim in stims:
                    stim.draw()
                win.flip()


