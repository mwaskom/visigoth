import os
import time
import itertools
import warnings
import Queue
import numpy as np
import pandas as pd
from scipy.spatial import distance
from psychopy import iohub
from psychopy.tools.monitorunittools import pix2deg


class EyeTracker(object):
    """Interface to the psychopy.iohub Eyelink interface.

    The main reason for the additional layer of complexity is to allow simple
    eyetracker simulation with the mouse in a way that is transparent to the
    experiment code. This object also has some helpful interface functions,
    allows for dynamic offset values, and maintains a log of samples.

    """
    def __init__(self, exp, calibration_screen_color=128, edf_stem="eyedat"):

        self.exp = exp

        # Extract relevant parameters
        self.host_address = exp.p.eye_host_address
        self.simulate = exp.p.eye_simulate
        self.save_data = exp.p.save_data
        self.fix_window_radius = exp.p.fix_radius

        # Initialize the offsets with default values
        self.offsets = (0, 0)

        # Set up a base for log file names
        self.edf_stem = edf_stem
        self.output_stem = exp.output_stem + "_eyedat"

        # Initialize lists for the logged data
        self.log_timestamps = []
        self.log_positions = []
        self.log_offsets = []

        # Configure iohub to communicate
        self.setup_iohub(calibration_screen_color)

    def setup_iohub(self, screen_color=128):
        """Initialize iohub with relevant configuration details.

        Some of these things should be made configurable either through our
        parameters system or the iohub yaml config system but I am hardcoding
        values in the object for now.

        """
        # Define relevant eyetracking parameters
        eye_config = dict()
        eye_config["name"] = "tracker"
        eye_config["model_name"] = "EYELINK 1000 DESKTOP"
        eye_config["default_native_data_file_name"] = self.edf_stem
        eye_config["network_settings"] = self.host_address

        bg_color = [int(screen_color)] * 3
        cal_config = dict(auto_pace=False,
                          type="NINE_POINTS",
                          screen_background_color=bg_color,
                          target_type="CIRCLE_TARGET",
                          target_attributes=dict(outer_diameter=33,
                                                 inner_diameter=6,
                                                 outer_color=[255, 255, 255],
                                                 inner_color=[0, 0, 0]))
        eye_config["calibration"] = cal_config
        eye_config["runtime_settings"] = dict(sampling_rate=1000,
                                              track_eyes="LEFT")

        tracker_class = "eyetracker.hw.sr_research.eyelink.EyeTracker"

        # Initialize iohub to track eyes or mouse if in simulation mode
        if self.simulate:
            self.io = iohub.launchHubServer()
            self.tracker = self.io.devices.mouse
        else:
            iohub_config = {tracker_class: eye_config}
            self.io = iohub.launchHubServer(**iohub_config)
            self.tracker = self.io.devices.tracker

    def run_calibration(self):
        """Execute the eyetracker setup (principally calibration) procedure."""
        if not self.simulate:
            self.tracker.runSetupProcedure()

    def start_run(self):
        """Turn on recording mode and sync with the eyelink log."""
        if not self.simulate:
            self.tracker.setRecordingState(True)
            self.send_message("SYNCTIME")

    def send_message(self, msg):
        """Send a message to the eyetracker, or no-op in simulation mode."""
        if not self.simulate:
            self.tracker.sendMessage(msg)

    def read_gaze(self, in_degrees=True, log=True, apply_offsets=True):
        """Read a sample of gaze position and convert coordinates."""
        timestamp = self.exp.clock.getTime()

        if self.simulate:
            # Use the correct method for a mouse "tracker"
            if any(self.tracker.getCurrentButtonStates()):
                # Simualte blinks with button down
                gaze = None
            else:
                gaze = self.tracker.getPosition()
        else:
            # Use the correct method for an eyetracker camera
            gaze = self.tracker.getLastGazePosition()

        # Use a standard form for invalid sample
        if not isinstance(gaze, (tuple, list)):
            gaze = (np.nan, np.nan)

        # Convert to degrees of visual angle using monitor information
        if in_degrees:
            gaze = tuple(pix2deg(np.array(gaze), self.exp.win.monitor))

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
            self.tracker.setRecordingState(False)
            self.tracker.setConnectionState(False)

    def move_edf_file(self):
        """Move the Eyelink edf data to the right location."""
        edf_src_fname = self.edf_stem + ".EDF"
        edf_trg_fname = self.exp.output_stem + "_eyedat.edf"

        if os.path.exists(edf_src_fname):
            edf_mtime = os.stat(edf_src_fname).st_mtime
            age = time.time() - edf_mtime
            if age > 10:
                w = ("\n"
                    "########################################################\n"
                    "Timestamp on Eyelink data file in this directory is old;\n"
                    "this may indicate problems and should be investigated.\n"
                    "########################################################\n"
                    )
                warnings.warn(w)
            os.rename(edf_src_fname, edf_trg_fname)
        elif not self.simulate:
            w = (
                "\n"
                "#########################################################\n"
                "Eyelink data file was not present in this directory after\n"
                "closing the connection to the eyetracker.\n"
                "#########################################################\n"
                )
            warnings.warn(w)

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
            self.move_edf_file()
            self.write_log_data()
        iohub.ioHubConnection.getActiveConnection().quit()
