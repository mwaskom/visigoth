import os
import time
import itertools
import warnings
import Queue
import numpy as np
import pandas as pd
from scipy.spatial import distance
from psychopy import event
from psychopy.tools.monitorunittools import pix2deg
import pylink
from .stimuli import Point


class EyeTracker(object):
    """Interface to EyeLink eyetracker.

    The main reason for the additional layer of complexity is to allow simple
    eyetracker simulation with the mouse in a way that is transparent to the
    experiment code. This object also has some helpful interface functions,
    allows for dynamic offset values, and it maintains a log of samples.

    """
    def __init__(self, exp, calibration_screen_color=128, edf_stem="eyedat"):

        self.exp = exp

        # Extract relevant parameters
        self.host_address = exp.p.eye_host_address
        self.simulate = exp.p.eye_simulate
        self.save_data = exp.p.save_data
        self.fix_window_radius = exp.p.fix_radius

        self.monitor = exp.win.monitor
        self.center = np.divide(exp.win.size, 2.0)

        # Initialize the offsets with default values
        self.offsets = (0, 0)

        # Set up a base for log file names
        self.host_edf = edf_stem + ".EDF"
        self.save_edf = self.exp.output_stem + "_eyedat.edf"

        # Initialize lists for the logged data
        self.log_timestamps = []
        self.log_positions = []
        self.log_offsets = []

        # Initialize the connection to the EyeLink box
        self.setup_eyelink()

    def setup_eyelink(self):
        """Connect to the EyeLink box at given host address."""
        if self.simulate:
            self.tracker = event.Mouse(visible=False, win=self.exp.win)
        else:
            self.tracker = pylink.EyeLink(self.host_address)

    def run_calibration(self):
        """Execute the eyetracker setup (principally calibration) procedure."""
        if not self.simulate:
            pylink.openGraphicsEx(Calibrator(self.exp.win))
            self.tracker.doTrackerSetup()

    def start_run(self):
        """Turn on recording mode and sync with the eyelink log."""
        if not self.simulate:
            self.tracker.openDataFile(self.host_edf)
            self.tracker.startRecording(1, 1, 1, 1)
            self.send_message("SYNCTIME")

    def send_message(self, msg):
        """Send a message to the eyetracker, or no-op in simulation mode."""
        if not self.simulate:
            self.tracker.sendMessage(msg)

    def read_gaze(self, log=True, apply_offsets=True):
        """Return the position of gaze in degrees, subject to offsets."""
        timestamp = self.exp.clock.getTime()

        if self.simulate:

            # Use the correct method for a mouse "tracker"
            if any(self.tracker.getPressed()):
                # Simualte blinks with button down
                gaze = None
            else:
                gaze = self.tracker.getPos()

        else:

            # Use the correct method for an eyetracker camera
            sample = self.tracker.getNewestSample()
            gaze_eyelink = np.array(sample.getLeftEye().getGaze())

            # TODO check that this is what bad gaze is
            if any(gaze_eyelink == pylink.MISSING_DATA):
                gaze = np.nan, np.nan
            else:
                gaze_pix = np.subtract(gaze_eyelink, self.center)
                gaze = tuple(pix2deg(gaze_pix, self.monitor))

        # Add to the low-resolution log
        if log:
            self.log_timestamps.append(timestamp)
            self.log_positions.append(gaze)
            self.log_offsets.append(self.offsets)

        # Apply the offsets
        if apply_offsets:
            gaze = tuple(np.add(self.offsets, gaze))

        return gaze

    def check_fixation(self, pos=(0, 0), radius=None,
                       new_sample=True, log=True):
        """Return True if eye is in the fixation window."""
        if new_sample:
            gaze = self.read_gaze(log=log)
        else:
            gaze = np.array(self.log_positions[-1]) + self.log_offsets[-1]
        if radius is None:
            radius = self.fix_window_radius
        if np.isfinite(gaze).all():
            fix_distance = distance.euclidean(pos, gaze)
            if fix_distance < radius:
                return True
        return False

    def check_eye_open(self, new_sample=True, log=True):
        """Return True if we get a valid sample of the eye position."""
        if new_sample:
            gaze = self.read_gaze(log=log)
        else:
            gaze = self.log_positions[-1]
        return np.isfinite(gaze).all()

    def last_valid_sample(self, apply_offsets=True):
        """Return the timestamp and position of the last valid gaze sample."""
        samples = itertools.izip(reversed(self.log_timestamps),
                                 reversed(self.log_positions),
                                 reversed(self.log_offsets))
        for timestamp, gaze, offsets in samples:
            if np.isfinite(gaze).all():
                if apply_offsets:
                    gaze = gaze + offsets
                return timestamp, gaze

    def update_params(self):
        """Update params by reading data from client."""
        self.cmd_q.put("_")
        try:
            params = self.param_q.get(timeout=.15)
            self.fix_window_radius = params[0]
            self.offsets = tuple(params[1:])
        except Queue.Empty:
            pass

    def close_connection(self):
        """Close down the connection to Eyelink and save the eye data."""
        if not self.simulate:
            self.tracker.stopRecording()
            self.tracker.setOfflineMode()
            pylink.msecDelay(500)
            self.tracker.closeDataFile()
            if self.save_data:
                self.tracker.receiveDataFile(self.host_edf, self.save_edf)
            self.tracker.close()

    def write_log_data(self):
        """Save the low temporal resolution eye tracking data."""
        if self.log_timestamps:
            log_df = pd.DataFrame(np.c_[self.log_positions, self.log_offsets],
                                  index=self.log_timestamps,
                                  columns=["x", "y", "x_offset", "y_offset"])

            log_fname = self.exp.output_stem + "_eyedat.csv"
            log_df.to_csv(log_fname)

    def shutdown(self):
        """Handle all of the things that need to happen when ending a run."""
        self.close_connection()
        if self.save_data:
            self.write_log_data()


class Calibrator(pylink.EyeLinkCustomDisplay):

    def __init__(self, win):

        self.win = win
        self.target = CalibrationTarget(win)

    def get_input_key(self):
        # TODO This will let things run but experiment keyboard won't
        # work properly for controlling calibration. Not a problem as the
        # experimenter always does things on the Eyelink host.
        # Need to translate some keys into pylink constants, I think.
        return event.getKeys()

    def play_beep(self, *args):
        # No sounds
        pass

    def draw_cal_target(self, *pos):

        self.target.set_pos_pixels(pos)
        self.target.draw()
        self.win.flip()

    def erase_cal_target(self):
        self.win.flip()

    def setup_cal_display(self):
        self.win.flip()

    def clear_cal_display(self):
        self.win.flip()

    def exit_cal_display(self):
        self.win.flip()


class CalibrationTarget(object):

    def __init__(self, win):

        self.win = win
        self.monitor = win.monitor
        self.center = np.divide(win.size, 2.0)
        self.stims = [
            Point(win, pos=(0, 0), radius=.4, color=(.8, .6, -.8)),
            Point(win, pos=(0, 0), radius=.05, color=win.color),
        ]

    def set_pos_pixels(self, pos):

        pos = pix2deg(np.subtract(pos, self.center), self.monitor)
        for stim in self.stims:
            stim.dot.pos = pos

    def draw(self):
        for stim in self.stims:
            stim.draw()
