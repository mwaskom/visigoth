"""Definition of the Experiment object that control most things."""
from __future__ import division
import os
import re
import time
import json
import hashlib
import Queue as queue

import yaml
import numpy as np
import pandas as pd

from psychopy import core, tools, visual, event, sound, monitors, logging

from .ext.bunch import Bunch
from . import version, stimuli, eyetracker, commandline, clientserver


class Experiment(object):

    abort_keys = ["escape"]

    def __init__(self, arglist=None):

        self.arglist = [] if arglist is None else arglist

        self.p = None
        self.s = None
        self.win = None
        self.tracker = None
        self.server = None

        self._aborted = False
        self._clean_exit = True

        self.clock = core.Clock()
        logging.defaultClock = self.clock

        # Initialize some related variables about the eye
        # TODO this might be squatting on a good name
        self.eye = Bunch(most_recent_fixation=0,
                         most_recent_blink=0)

        self.trial = 0
        self.trial_data = []

    def run(self):

        # Everything is wrapped in a try block so that errors will exit out
        # properly and not destroy data or leave hanging connections.

        try:

            # -- Experiment initialization

            self.initialize_params()
            self.initialize_data_output()
            self.initialize_sounds()
            self.initialize_eyetracker()
            self.initialize_server()
            self.initialize_display()
            self.initialize_stimuli()

            # Wait for a trigger to start
            if self.p.trigger is not None:
                self.wait_for_trigger()

            # Wait a certain amount of time before starting the run
            # (e.g. for dummy fMRI scans)
            # TODO add a countdown or something nice here
            if self.p.wait_pre_run:
                self.wait_until(self.check_abort,
                                draw=self.p.draw_pre_run,
                                timeout=self.p.wait_pre_run)

            # -- Initialize the trial generator
            trial_generator = self.generate_trials()
            if self.p.initialize_trial_generator:
                next(trial_generator)

            # -- Initialize the experimental run
            self.tracker.start_run()
            self.clock.reset()
            self.iti_start = 0

            # -- Main experimental loop

            for trial_info in trial_generator:

                trial_info = self.run_trial(trial_info)
                self.iti_start = self.clock.getTime()

                self.trial_data.append(trial_info)
                self.sync_remote_trials(trial_info)

                self.sync_remote_params()

                self.check_abort()

            # Wait at the end of the run for exact duration
            if self.p.run_duration is not None:
                timeout = self.p.run_duration - self.clock.getTime()
                self.wait_until(self.check_abort, timeout)

        except:

            # Aborting raises an exception but isn't considered an error
            self._clean_exit = self._aborted
            raise

        finally:

            if self._clean_exit:
                self.show_performance(*self.compute_performance())

            self.save_data()
            self.shutdown_server()
            self.shutdown_eyetracker()

            if self._clean_exit:
                self.wait_for_exit()

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
        """Serialize the trial results so they can be be sent to the remote.

        If the object returned by ``run_trial`` is a pandas Series, it's not
        necessary to overload this function. However, it can be defined for
        each study to allow for more complicated data structures.

        """
        return trial_info.to_json()

    def save_data(self):
        """Write out data files at the end of the run.

        If the object returned by ``run_trial`` is a pandas Series and you
        don't want to do anything special at the end of the experiment, it's
        not necessary to overload this function. However, it can be defined for
        each study to allow for more complicated data structures or exit logic.

        """
        if self.trial_data and self.p.save_data:

            data = pd.DataFrame(self.trial_data)
            out_data_fname = self.output_stem + "_trials.csv"
            data.to_csv(out_data_fname, index=False)

            out_json_fname = self.output_stem + "_params.json"
            with open(out_json_fname, "w") as fid:
                json.dump(self.p, fid, sort_keys=True, indent=4)

    def compute_performance(self):
        """Extract performance metrics from trial data log.

        If the object returned by ``run_trial`` is a pandas Series with fields
        ``correct`` and ``rt``, and if the ``show_performance`` method expects
        to get an arglist that has ``mean_acc, mean_rt``, then it is not
        necessary to overload this function.

        """
        mean_acc, mean_rt = None, None
        if self.trial_data:
            data = pd.DataFrame(self.trial_data)
            if "correct" in data:
                mean_acc = data["correct"].astype(float).mean()
            if "rt" in data:
                mean_rt = data["rt"].astype(float).mean()
        return mean_acc, mean_rt

    def show_performance(self, mean_acc, mean_rt):
        """Show end-of-run feedback to the subject about performance.

        This method can be overloaded if you want to show something other than
        mean accuracy and mean rt. Whether either metric is reported to the
        subject is controlled by fields in the param file that specify the
        target values for each measure.

        """
        lines = ["End of the run!"]

        null_values = None, np.nan
        if mean_acc in null_values and mean_rt in null_values:
            visual.TextStim(self.win, lines[0],
                            pos=(0, 0), height=.5).draw()
            self.win.flip()
            return

        target_acc = self.p.perform_acc_target
        if mean_acc is not None and target_acc is not None:
            lines.append("")
            lines.append(
                "You were correct on {:.0%} of trials".format(mean_acc)
                )
            if mean_acc >= target_acc:
                lines.append("Great job!")
            else:
                lines.append("Please try to be more accurate!")

        target_rt = self.p.perform_rt_target
        if mean_rt is not None and target_rt is not None:
            lines.append("")
            lines.append(
                "You took {:.1f} seconds to respond on average".format(mean_rt)
                )
            if mean_rt <= target_rt:
                lines.append("Great job!")
            else:
                lines.append("Please try to respond faster!")

        if lines:
            n = len(lines)
            height = .5
            heights = (np.arange(n)[::-1] - (n / 2 - .5)) * height
            for line, y in zip(lines, heights):
                visual.TextStim(self.win, line,
                                pos=(0, y), height=height).draw()
            self.win.flip()

    # ==== Initialization functions ====

    def initialize_params(self):
        """Determine parameters for this run of the experiment."""

        # TODO let's make sure this is the right organization of things.
        # Should we parse the main command line arguments outside of the
        # Experiment class and then pass in a params bunch/dict?
        # Not sure right now what's cleanest.

        # Define the standard set of command line argument
        parser = commandline.define_parser("visigoth")

        # Add study-specific command line arguments
        self.define_cmdline_params(parser)

        # Parse the command line args associated with this class instance
        # NOTE this is the part that smells bad
        args = parser.parse_args(self.arglist)

        # Start with the set of default parameters
        param_dict = default_params.copy()

        # Import the params module and extract the params for this run
        import params
        dicts = [v for k, v in vars(params).iteritems()
                 if isinstance(v, dict) and not re.match("__\w+__", k)]

        if len(dicts) == 1:
            param_dict.update(dicts[0])
        else:
            if args.paramset is None:
                err = "Must specify `-paramset` when multiple are defined"
                raise RuntimeError(err)
            else:
                # TODO maybe give paramset a better default name?
                param_dict.update(getattr(params, args.paramset))

        # Define the parameters object with information from the params
        # module and from the command line invocation
        p = Bunch(param_dict)
        p.update(args.__dict__)

        # Timestamp the execution and add to parameters
        timestamp = time.localtime()
        p.date = time.strftime("%Y-%m-%d", timestamp)
        p.time = time.strftime("%H-%M-%S", timestamp)
        p.session = p.date if args.session is None else args.session

        # Create a name for the eyelink file (limited to 6 characeters)
        hash_seed = "_".join([p.subject, p.date, p.time])
        p.eyelink_fname = hashlib.md5(hash_seed).hexdigest()[:6]

        # Save information about software versions
        # TODO add visigoth git commit for pre release
        # TODO also track git commit of study-specific code
        p.visigoth_version = version.__version__

        self.p = p
        self.debug = args.debug

    def initialize_data_output(self):
        """Define stem for output filenames and ensure directory exists."""
        output_stem = self.p.output_template.format(**self.p)

        output_dir = os.path.dirname(output_stem)
        if self.p.save_data and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        self.output_stem = output_stem

    def initialize_sounds(self):
        """Create PsychoPy Sound objects for auditory feedback."""
        # TODO Psychopy 1.85 has improved sound capability
        # need to look into that and whether it requires changes here

        # Locate the sound files
        sound_dir = os.path.join(os.path.dirname(__file__), "sounds")
        sound_names = dict(correct="ding",
                           wrong="signon",
                           nofix="secalert",
                           nochoice="click",
                           fixbreak="click",)

        # Load the sounds and save in a Bunch
        self.sounds = Bunch()
        for result, sound_name in sound_names.items():
            fname = os.path.join(sound_dir, sound_name + ".wav")
            sound_obj = sound.Sound(fname)
            self.sounds[result] = sound_obj

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
        # TODO Need to figure out how to handle non eye-tracking centrally
        if self.p.monitor_eye:

            # Determine the screen background color during calibration
            # Currently I'm not sure how to get iohub to apply gamma correction
            # so we need to do that ourselves here.
            # TODO but this should probably be abstracted as it happens twice
            fname = os.path.join(self.p.study_dir, "displays.yaml")
            with open(fname) as fid:
                display_info = yaml.load(fid)
            info = display_info[self.p.display_name]
            if self.p.display_luminance is None:
                color = 128
            else:
                ratio = self.p.display_luminance / info["max_luminance"]
                color = int(round(ratio ** (1 / info["gamma"]) * 255))

            # Configure and calibrate the eyetracker
            self.tracker = eyetracker.EyeTracker(self, color,
                                                 self.p.eyelink_fname)
            self.tracker.run_calibration()

    def initialize_display(self, gamma_correct=True, debug=False):
        """Open the PsychoPy window to begin the experiment."""

        # Extract the relevant display information
        fname = os.path.join(self.p.study_dir, "displays.yaml")
        with open(fname) as fid:
            display_info = yaml.load(fid)
        info = display_info[self.p.display_name]

        # Determine the background color of the display
        if self.p.display_luminance is None:
            color = 0
        else:
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
        logging.console.setLevel(logging.CRITICAL)
        res = (800, 600) if debug else info["resolution"]
        self.win = win = visual.Window(units="deg",
                                       screen=0,
                                       fullscr=not debug,
                                       allowGUI=debug,
                                       color=color,
                                       size=res,
                                       monitor=monitor,
                                       autoLog=False,
                                       useFBO=True)

        # Test window performance
        win.recordFrameIntervals = True
        frametime, _, _ = visual.getMsPerFrame(win)
        refresh_hz = 1000 / frametime
        refresh_error = abs(info["refresh_hz"] - refresh_hz)
        if refresh_error > .5 and not debug:
            text = "Display refresh rate differs from expected by {:.2} Hz"
            raise RuntimeError(text.format(refresh_error))
        win.recordFrameIntervals = False

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
        stims = self.create_stimuli()

        # Remove the experiment object from the stimuli
        # (allows study code to simply return locals)
        stims = {s: obj for s, obj in stims.items() if obj is not self}

        # Convet to a Bunch to allow getattr access
        self.s = Bunch(stims)

    def wait_for_trigger(self):
        """Wait for a trigger key (or an abort)."""
        trigger_keys = self.p.trigger
        if not isinstance(trigger_keys, (tuple, list)):
            trigger_keys = list(trigger_keys)

        visual.TextStim(self.win, "Waiting for scanner",
                        pos=(0, 0), height=1).draw()
        self.win.flip()

        catch_keys = self.abort_keys + trigger_keys
        keys = event.waitKeys(keyList=catch_keys)

        if set(keys) & set(self.abort_keys):
            self._aborted = True
            core.quit()

    # ==== Shutdown functions ====

    def shutdown_server(self):
        """Cleanly close down the experiment server process."""
        # TODO we should send some sort of shutdown signal to the
        # remote client so it can handle hangups well (currently just crashes)
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

    def sync_remote_screen(self, stims):
        """Send information about what's on the screen to the client."""
        if self.server.connected:

            gaze = self.tracker.read_gaze()

            # Pass stimuli on the screen and their position
            # (if they have a `pos` attribute).
            # Note that we want to find a better way to sync arbitrary
            # Psychopy and matplotlib commands for a richer client view
            stim_data = {}
            for s in stims:
                pos = getattr(self.s[s], "pos", None)
                pos = pos if pos is None else tuple(pos)
                stim_data[s] = pos

            data = json.dumps(dict(gaze=gaze, stims=stim_data))
            self.screen_q.put(data)

    def sync_remote_trials(self, trial_info):
        """Send trial information to the remote client for plotting."""
        if self.server.connected:
            self.trial_q.put(self.serialize_trial_info(trial_info))

    def sync_remote_params(self):
        """Update eyetracking params using values from the remote client.

        A note about the scalability of this method: ultimately, we'd like
        to be able to change *any* parameters on the client side. Currently
        we only know how to handle a subset of parameters that pertain to
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
                self.tracker.offsets = p["x_offset"], p["y_offset"]

                # TODO this really needs to be handled better
                # Currently it's not dynamically logged. See notes above.
                self.p.fix_window = p["fix_window"]

    def wait_for_exit(self):
        """Wait until the experimenter quits."""
        event.waitKeys(["enter", "return"])

    # === Execution functions ===

    # Study-specific code will generally only need to interact with these
    # methods; the ones above are mostly called internally (despite not
    # having private names)

    def trial_count(self, max=None):
        """Generator of trial index."""
        while True:
            self.trial += 1
            if max is not None and self.trial > max:
                raise StopIteration
            yield self.trial

    def trial_info(self, **kwargs):
        """Generate a Series with trial information.

        This function automatically includes a set of generally-relevant
        fields and allows specification of additional study-specific
        fields though keyword arguments.

        Returns
        -------
        t_info : pandas Series
            Trial info with generic fields and study-specific fields,
            which supersede the generic fields if overlapping.

        """
        t_info = dict(

            subject=self.p.subject,
            session=self.p.session,
            run=self.p.run,
            trial=self.trial,

            responded=False,
            result=np.nan,
            response=np.nan,
            correct=np.nan,
            rt=np.nan,

            )

        t_info.update(kwargs)

        return pd.Series(t_info)

    def wait_until(self, func=None, timeout=np.inf, sleep=0, draw=None,
                   args=(), **kwargs):
        """Wait limited by callback and timeout, possibly drawing stimuli.

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

    def draw(self, stims, flip=True):
        """Draw each named stimulus in the order provided."""

        # TODO We want to use this central drawing method to send information
        # about what's on the screen to the client in a standardized way.
        # Originally this was conceived as a simple helper function for
        # one-line drawing of a number of stimuli (identified by strings).
        # We want consider whether we want to enforce that *all* drawing must
        # happen in this method, and if we ever want to allow separation of
        # drawing and flipping the screen. Right now we are going to assume
        # code is written that way, but not enforce it (or handle cases where
        # it is not true well)

        if not isinstance(stims, list):
            stims = [stims]

        for stim in stims:
            self.s[stim].draw()

        self.sync_remote_screen(stims)

        if flip:
            self.win.flip()
            flip_time = self.clock.getTime()
        else:
            flip_time = None

        return flip_time

    def frame_range(self, seconds=None, frames=None, round_func=np.floor,
                    adjust_for_missed=True, yield_skipped=False,
                    expected_offset=None):
        """Generator function for timing events based on screen flips.

        Either ``seconds`` or ``frames``, but not both, are required.

        This function can adjust the number of flips generated in real time
        based on the PsychoPy Window's estimate of its missed flips. This
        assumes you are not resetting the win.nDroppedFrames counter while
        the frame range is active.

        Parameters
        ----------
        seconds : float
            Duration of the event in real time.
        frames : int
            Number of screen flips.
        round_func : callable, optional
            Function used to turn a continuous duration into a integral number
            of screen flips.
        adjust_for_missed : bool, optional
            If True, decrement the number of total frames to generate when
            PsychoPy thinks it has missed a flip.
        yield_skipped : bool, optional
            If True, also return a list of flip indices that were missed
        expected_offset : float, optional
            Expected offset time for the stimulus. If provided, the generator
            will check the experiment clock and end if the next flip will be
            after the expected offset time.

        Yields
        ------
        frame : int
            Index into the frame, possibly discontinuous when adjusting for
            missed flips.
        skipped : list of ints, optional
            Indices of frames that were skipped if frames have been dropped,
            only when ``yield_skipped`` is True.

        """
        if seconds is None and frames is None:
            raise ValueError("Must specify `seconds` or `frames`")
        if seconds is not None and frames is not None:
            raise ValueError("Must specify only one of `seconds` or `frames`")

        if seconds is not None:
            frames = int(round_func(seconds * self.win.framerate))

        if adjust_for_missed:
            self.win.recordFrameIntervals = True
            self.win.nDroppedFrames = dropped_count = 0

        frame = 0
        while frame < frames:

            if adjust_for_missed:
                new_dropped = self.win.nDroppedFrames - dropped_count
                if new_dropped:
                    dropped_count += new_dropped
                    frame += new_dropped
                skipped_frames = list(range(frame, frame + new_dropped))
            else:
                skipped_frames = []

            if expected_offset is not None:
                now = self.clock.getTime()
                if expected_offset < (now + self.win.frametime):
                    raise StopIteration

            if yield_skipped:
                yield frame, skipped_frames
            else:
                yield frame

            frame += 1

        if adjust_for_missed:
            self.win.recordFrameIntervals = False

    def check_fixation(self, allow_blinks=False, fix_pos=None):
        """Enforce fixation but possibly allow blinks."""
        if fix_pos is None:
            fix_pos = self.p.fix_pos
        now = self.clock.getTime()
        if self.tracker.check_fixation(fix_pos, self.p.fix_window):
            # Eye is open and in fixation window
            self.eye.most_recent_fixation = self.clock.getTime()
            return True

        if allow_blinks:

            if self.tracker.check_eye_open(new_sample=False):
                # Eye is outside of fixation, maybe at start or end of blink
                last_fix = self.eye.most_recent_fixation
                last_blink = self.eye.most_recent_blink
                if (now - last_fix) < self.p.eye_fixbreak_timeout:
                    return True
                elif (now - last_blink) < self.p.eye_fixbreak_timeout:
                    return True

            else:
                # Eye is closed (or otherwise not providing valid data)
                self.eye.most_recent_blink = now
                blink_duration = now - self.eye.most_recent_fixation
                if blink_duration < self.p.eye_blink_timeout:
                    return True

        # Either we are outside of fixation or eye has closed for too long
        return False

    def show_feedback(self, stim, result, idx=None):
        """Change the color of a stimulus to show feedback."""
        color_choices = dict(correct=(-.8, .5, -.8), wrong=(1, -.7, -.6))
        color = color_choices.get(result, None)

        if idx is None or np.isnan(idx):
            stim_color = color
        else:
            stim_color = [color if i == idx else None
                          for i, _ in enumerate(self.s[stim].color)]

        self.s[stim].color = stim_color

    def flicker(self, stim, duration=.4, rate=10, other_stims=None):
        """Repeatedly turn a stimulus off and on."""
        if other_stims is None:
            other_stims = []

        draw = False
        for i in self.frame_range(duration):
            if not i % int(self.win.framerate / rate):
                draw = not draw
            if draw:
                self.draw([stim] + other_stims)
            else:
                self.draw(other_stims)

    def check_abort(self):
        """Check whether the quit key has been pressed and exit if so."""
        if event.getKeys(self.abort_keys):
            self._aborted = True
            core.quit()
        return False

    def iti_end(self, iti_duration, check_abort=True):
        """Return True if current time is within a flip of the ITI end."""
        if check_abort:
            self.check_abort()
        now = self.clock.getTime()
        end = self.iti_start + iti_duration
        return (now + self.win.frametime) >= end


default_params = dict(

    display_luminance=None,

    initialize_trial_generator=False,

    fix_pos=(0, 0),
    fix_radius=.15,
    fix_window=2,
    fix_color=(.8, .6, -.8),
    fix_ready_color=(.8, .6, -.8),
    fix_trial_color=(.8, .6, -.8),
    fix_iti_color=None,

    target_pos=[],
    target_radius=.25,
    target_window=5,
    target_color=(.8, .6, -.8),

    monitor_key=False,
    monitor_eye=False,

    key_fixation=False,
    key_response=False,

    eye_fixation=False,
    eye_response=False,

    # TODO use fixbreak timeout exclusively for allowing blinks
    # or more generally allow small deviations from fix window?
    eye_fixbreak_timeout=.25,
    eye_blink_timeout=.5,

    eye_target_wait=.2,
    eye_target_hold=.3,

    wait_pre_run=0,
    draw_pre_run=None,

    wait_iti=1,
    wait_fix=5,
    wait_resp=5,
    wait_feedback=.5,

    perform_acc_target=None,
    perform_rt_target=None,

    trigger=None,

    run_duration=None,

    output_template="data/{subject}/{session}/{time}",

)
