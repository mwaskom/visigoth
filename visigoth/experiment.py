"""Definition of the Experiment object that control most things."""
from __future__ import division
import os
import re
import time
import json
import Queue as queue

import yaml
import numpy as np
import pandas as pd

from psychopy import core, tools, visual, event, monitors

from .ext.bunch import Bunch
from . import stimuli, feedback, eyetracker, commandline, clientserver


class Experiment(object):

    def __init__(self, arglist=None):

        self.arglist = [] if arglist is None else arglist

        self.p = None
        self.s = None
        self.win = None
        self.tracker = None
        self.server = None

        self.clock = core.Clock()

        # TODO feedback implementation needs to be improved
        self.auditory_feedback = feedback.AuditoryFeedback()

        self.trial_data = []

    def run(self):

        # Everything is wrapped in a try block so that errors will exit out
        # properly and not destroy data or leave hanging connections.

        try:

            # Experiment initialization

            self.initialize_params()
            self.initialize_data_output()
            self.initialize_eyetracker()
            self.initialize_server()
            self.initialize_display()
            self.initialize_stimuli()

            # TODO add scanner trigger/dummy scans

            # Initialize the experimental run
            self.clock.reset()
            self.tracker.start_run()
            self.iti_start = 0

            # Main experimental loop

            for trial_info in self.generate_trials():

                trial_info = self.run_trial(trial_info)
                self.iti_start = self.clock.getTime()

                self.trial_data.append(trial_info)
                self.sync_remote_trials(trial_info)

                self.sync_remote_params()

                self.check_quit()

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
        ``serialize_trial_info`` and ``save_data`` methods knows how to handle.

        It is easiest for this to be a pandas Series, so that those methods do
        not need to be overloaded, but this is not strictly required to allow
        for more complicated designs.

        """
        raise NotImplementedError

    def serialize_trial_info(self, trial_info):
        """Serialze the trial results so they can be be sent to the remote.

        If the object returned by ``run_trial`` is a pandas Series, it's not
        necessary to overload this function. However, it can be defined for
        each study to allow for more complicated data structures.

        """
        return trial_info.to_json()

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

        """
        TODO let's make sure this is the right organization of things.
        Should we parse the main command line arguments outside of the
        Experiment class and then pass in a params bunch/dict?
        Not sure right now what's cleanest.
        """

        # Define the standard set of command line argument
        parser = commandline.define_parser("visigoth")

        # Add study-specific command line arguments
        self.define_cmdline_params(parser)

        # Parse the commend line args associated with this class instance
        # NOTE this is the part that smells bad
        args = parser.parse_args(self.arglist)

        # Import the params module and extract the params for this run
        import params

        dicts = [v for k, v in vars(params).iteritems()
                 if isinstance(v, dict) and not re.match("__\w+__", k)]

        if len(dicts) == 1:
            param_dict = dicts[0]
        else:
            if args.paramset is None:
                err = "Must specify `-paramset` when multiple are defined"
                raise RuntimeError(err)
            else:
                param_dict = getattr(params, args.paramset)

        # Define the parameters object with information from the params
        # module and from the command line invocation
        p = Bunch(param_dict)
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
        if self.p.save_data and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self.output_stem = output_stem

    def initialize_server(self):
        """Start a server in an independent thread for experiment control."""
        self.cmd_q = queue.Queue()
        self.trial_q = queue.Queue()
        self.param_q = queue.Queue()
        self.screen_q = queue.Queue()

        # TODO enhance robustness later :-/
        self.server = clientserver.SocketServerThread(self)
        self.server.start()

    def initialize_eyetracker(self):
        """Connect to and calibrate eyetracker."""
        if self.p.monitor_eye:

            # Determine the screen background color during calibration
            # Currently I'm not sure how to get iohub to apply gamma correction
            # so we need to do that ourselves here.
            fname = os.path.join(self.p.study_dir, "displays.yaml")
            with open(fname) as fid:
                display_info = yaml.load(fid)
            info = display_info[self.p.display_name]
            ratio = self.p.display_luminance / info["max_luminance"]
            color = int(round(ratio ** (1 / info["gamma"]) * 255))

            # Configure and calibrate the eyetracker
            self.tracker = eyetracker.EyeTracker(self, color)
            self.tracker.run_calibration()

    def initialize_display(self, gamma_correct=True, debug=False):
        """Open the PsychoPy window to begin the experiment."""

        # Extract the relevant display information
        fname = os.path.join(self.p.study_dir, "displays.yaml")
        with open(fname) as fid:
            display_info = yaml.load(fid)
        info = display_info[self.p.display_name]

        # Determine the background color of the display
        color = self.p.display_luminance / info["max_luminance"] * 2 - 1

        # Define information about the monitor
        gamma = info["gamma"] if gamma_correct else None
        monitor = monitors.Monitor(name=self.p.display_name,
                                   width=info["width"],
                                   distance=info["distance"],
                                   gamma=gamma,
                                   autoLog=False)
        monitor.setSizePix(info["resolution"])

        # Open the psychopy window
        res = (800, 600) if debug else info["resolution"]
        self.win = win = visual.Window(units="deg",
                                       screen=0,
                                       fullscr=not debug,
                                       allowGUI=debug,
                                       color=color,
                                       size=res,
                                       monitor=monitor)

        # Test window performance
        win.setRecordFrameIntervals(True)
        frametime, _, _ = visual.getMsPerFrame(win)
        refresh_hz = 1000 / frametime
        refresh_error = abs(info["refresh_hz"] - refresh_hz)
        if refresh_error > .5 and not debug:
            text = "Display refresh rate differs from expected by {:.2} Hz"
            raise RuntimeError(text.format(refresh_error))

        # Assign attributes with helpful information and log in params
        win.frametime = 1 / info["refresh_hz"]
        win.framerate = info["refresh_hz"]
        win.deg_per_pix = tools.monitorunittools.pix2deg(1, monitor)
        win.pix_per_deg = tools.monitorunittools.deg2pix(1, monitor)
        self.p.update(win_frametime=win.frametime,
                      win_framerate=win.framerate,
                      win_deg_per_pix=win.deg_per_pix,
                      win_pix_per_deg=win.pix_per_deg)

        # Initialize the gaze stimulus
        if self.p.monitor_eye and self.p.eye_simulate:
            stimuli.GazeStim(win, self.tracker)

        return win

    def initialize_stimuli(self):
        """Setup stimulus objects."""
        self.s = Bunch(self.create_stimuli())

    # ==== Shutdown functions ====

    def shutdown_server(self):
        """Cleanly close down the experiment server process."""
        # TODO we should send some sort of shutdown signal to the
        # remote client so it can handle things well (currently just crashes)
        if self.server is not None:
            self.server.join(timeout=2)

    def shutdown_eyetracker(self):
        """End Eyetracker recording and save eyetracker log files."""
        if self.tracker is not None:
            self.tracker.shutdown()

    def shutdown_display(self):
        """Cleanly exit out of the psychopy window."""
        if self.win is not None:
            self.win.close()

    # === Networking functions (communication with remote)

    # TODO Need to figure out how to handle non eye-tracking centrally

    def sync_remote_screen(self, stims):
        """Send information about what's on the screen to the client."""
        if self.server.connected:
            gaze = self.tracker.read_gaze()
            data = json.dumps(dict(gaze=gaze,
                              stims=stims))
            self.screen_q.put(data)

    def sync_remote_trials(self, trial_info):
        """Send trial information to the remote client for plotting."""
        if self.server.connected:
            self.trial_q.put(self.serialize_trial_info(trial_info))

    def sync_remote_params(self):
        """Update eyetracking params using values from the remote client.

        A note about the scalability of this method: ultimately, we'd like
        to be able to change *any* parameters on the client side. Currently
        we only know how to handle a subset of parametesr that pertain to
        eye-tracking. These are not that cleanly handled anyway, as the
        offsets "belong" to the eyetracker, but the fixation window size
        doesn't. Maybe it should?

        Also worth noting that elsewhere, the "params" are considered to be
        run-specific and are only saved out at the end. Maybe we want to save
        some kind of "params delta" file, as it doesn't seem worthwhile to
        write out the (mostly static) set of params on every trial. Experiment
        code can be written to log parameters in the trial info anyway.

        """
        if self.server.connected:
            self.cmd_q.put(self.server.PARAM_REQUEST)
            try:
                new_params = self.param_q.get(timeout=.5)
            except queue.Empty:
                new_params = ""
            if new_params:
                p = json.loads(new_params)
                self.tracker.offsets = (p.x_offset, p.y_offset)

                # TODO this really needs to be handled better
                # Currently it's not dynamically logged. See notes above.
                self.p.fix_window = p.fix_window

    # === Execution functions

    # Study-specific code will generally only need to interact with these
    # methods; the ones above are mostly called interally (despite not
    # having private names)

    def wait_until(self, func=None, timeout=np.inf, sleep=0, draw=None,
                   args=(), **kwargs):
        """Wait limited by callback and timout, possibly drawing stimuli.

        Parameters
        ----------
        func : callable, optional
            Function to call on each interval. Waiting ends if the value
            returned by this function evaluates to True.
        timeout : float, optional
            Maximum amount of time to wait regardless of ``func`` outcome.
        sleep : float, optional
            Amount of time to wait on each interval. If ``0``, the window is
            drawn after each call to ``func`` and so the interval is controlled
            by the window's framerate.
        draw : string or list of strings, optional
            Name(s) of stimuli to draw in each interval.
        args : tuple
            Positional arguments to `func`.
        kwargs : key, value pairs
            Other keyword arguments are passed through to `func`.

        Returns
        -------
        func_val or None
            If ``func`` returns something that evaluates to True before the
            timeout, it is returned. Otherwise this function returns None.

        """
        # QC input arguments
        stims = [] if draw is None else draw
        if sleep and stims:
            raise ValueError("`sleep` must be `0` to draw stimuli.")

        # Don't include final window refresh in the timeout check
        if not sleep:
            timeout -= self.win.frametime

        # Maximum wait is controlled by timeout value
        clock = core.Clock()
        while clock.getTime() < timeout:

            # Check for a nonzero return from the function
            if func is not None:
                func_val = func(*args, **kwargs)
                if func_val:
                    return func_val

            # Either sleep or draw and wait for the screen refresh
            if sleep:
                core.wait(sleep, sleep)
            else:
                self.draw(stims, flip=True)

    def draw(self, stims, flip=False):
        """Draw each named stimulus in the order provided."""

        # TODO We want to use this central drawing method to send information
        # about what's on the screen to the client in a standardized way.
        # Originally this was conceived as a simple helper function for
        # one-line drawing of a number of stimuli (identified by strings).
        # We want consider whether we want to enforce that *all* drawing must
        # happen in this method, and if we ever want to allow separation of
        # drawing and flipping the scren. Right now we are going to assume
        # code is written that way, but not enforce it (or handle cases where
        # it is not true well)

        if not isinstance(stims, list):
            stims = [stims]
        for stim in stims:
            self.s[stim].draw()

        self.sync_remote_screen(stims)

        if flip:
            self.win.flip()

    def frame_range(self, seconds=None, frames=None, round_func=np.floor):
        """Convenience function for converting to screen refresh units."""
        if seconds is None and frames is None:
            raise ValueError("Must specify `seconds` or `frames`")
        if seconds is not None and frames is not None:
            raise ValueError("Must specify only one of `seconds` or `frames`")

        if seconds is not None:
            frames = int(round_func(seconds * self.win.framerate))

        return range(frames)

    def check_quit(self):
        """Check whether the quit key has been pressed and exit if so."""
        if event.getKeys(["escape"]):
            core.quit()
        return False

    def iti_end(self, iti_duration):
        """Return True if current time is within a flip of the ITI end."""
        now = self.clock.getTime()
        end = self.iti_start + iti_duration
        return (now + self.win.frametime) >= end
