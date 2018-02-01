import itertools
import Queue
import numpy as np
import pandas as pd
from scipy.spatial import distance
from psychopy import visual, event
from psychopy.tools.monitorunittools import pix2deg

try:
    import pylink
    from pylink import EyeLinkCustomDisplay
    have_pylink = True
except ImportError:
    have_pylink = False
    pylink = None
    EyeLinkCustomDisplay = object

from .stimuli import Point


class EyeTracker(object):
    """Interface to EyeLink eyetracker.

    The main reason for the additional layer of complexity is to allow simple
    eyetracker simulation with the mouse in a way that is transparent to the
    experiment code. This object also has some helpful interface functions,
    allows for dynamic offset values, and it maintains a log of samples.

    """
    def __init__(self, exp, edf_stem="eyedat"):

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
        """Connect to the EyeLink box at given host address and run setup."""
        if self.simulate:
            self.tracker = event.Mouse(visible=False, win=self.exp.win)

        else:

            if not have_pylink:
                raise ImportError("No module named pylink")

            # Connect to the eyetracker
            self.tracker = pylink.EyeLink(self.host_address)

            # Send configuration commands
            # TODO how to control which eye to track?
            # (we need flexibility for psychophys and scanner)
            self.tracker.disableAutoCalibration()
            self.tracker.setCalibrationType("HV9")
            self.tracker.setPupilSizeDiameter("NO")
            self.tracker.setRecordingParseType("GAZE")
            self.tracker.setSaccadeVelocityThreshold(30)
            self.tracker.setAccelerationThreshold(9500)
            self.tracker.setMotionThreshold(0.15)
            self.tracker.setPursuitFixup(60)
            self.tracker.setUpdateInterval(0)

            file_events = "LEFT RIGHT FIXATION SACCADE BLINK MESSAGE BUTTON"
            self.tracker.setFileEventFilter(file_events)

            link_events = "LEFT RIGHT FIXATION SACCADE BLINK BUTTON"
            self.tracker.setLinkEventFilter(link_events)

            file_data = "GAZE GAZERES HREF PUPIL AREA STATUS BUTTON INPUT"
            self.tracker.setFileSampleFilter(file_data)

            link_data = "GAZE GAZERES AREA"
            self.tracker.setLinkSampleFilter(link_data)

    def run_calibration(self):
        """Execute the eyetracker setup (principally calibration) procedure."""
        if not self.simulate:
            pylink.openGraphicsEx(Calibrator(self.exp.win,
                                             self.exp.p.fix_color))
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

        # Allow simulation using the mouse
        if self.simulate:

            if any(self.tracker.getPressed()):
                # Simulate blinks with button down
                gaze = np.nan, np.nan
            else:
                gaze = self.tracker.getPos()

        else:

            # Use the correct method for an eyetracker camera
            sample = self.tracker.getNewestSample()

            if sample is None:
                gaze = np.nan, np.nan

            else:
                if sample.isLeftSample():
                    gaze_eyelink = np.array(sample.getLeftEye().getGaze())
                elif sample.isRightSample():
                    gaze_eyelink = np.array(sample.getRightEye().getGaze())
                else:
                    raise RuntimeError("Must do monocular tracking!")

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


class Calibrator(EyeLinkCustomDisplay):

    def __init__(self, win, target_color):

        self.win = win
        self.target = CalibrationTarget(win, target_color)
        self.eye_image_size = 384, 320

    def get_input_key(self):
        # TODO This will let things run but experiment keyboard won't
        # work properly for controlling calibration. Not a problem as the
        # experimenter always does things on the Eyelink host.
        # TODO As one option we could also make it so we can control
        # Pupil/CR from the scanner buttonbox, to facilitate setup.
        # This is a good idea!
        return None

    def play_beep(self, *args):
        # TODO No sounds yet
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

    def setup_image_display(self, width, height):

        # TODO This stuff can just happen in the constructor since we
        # are making hard assumptions about the width and height for now

        self.eye_image = visual.ImageStim(
            self.win,
            size=self.eye_image_size,
            units="pix",
        )

        self.eye_image_title = visual.TextStim(
            self.win,
            pos=(0, self.eye_image_size[1] * .7),
            color="white",
            units="pix",
            height=20,
        )

        # Note differences from numpy convention in terms of rows/cols
        # Also may not generalize to other eyetracker models.
        self.rgb_index_array = np.zeros((height / 2, width / 2), np.uint8)

        # TODO test width/height against the hardcoded values and make
        # it more obvious when we are trying to set up on an Eyelink model
        # that our assumptions do not extend do

    def image_title(self, text):

        self.eye_image_title.text = text

    def exit_image_display(self):

        self.win.flip()

    def draw_image_line(self, width, line, total_lines, buff):

        # Note that Eyelink increases the index as you move down the screen,
        # opposite to the convention in PsychoPy. We could also flip the array.
        self.rgb_index_array[-line] = np.asarray(buff)

        if line == total_lines:

            image = self.rgb_palette[self.rgb_index_array]
            self.eye_image.image = image

            self.eye_image.draw()
            self.eye_image_title.draw()
            self.draw_cross_hair()

            self.win.flip()

    def draw_line(self, x1, y1, x2, y2, colorindex):

        xadj, yadj = np.divide(self.eye_image_size, 2)
        start = x1 - xadj, -y1 + yadj
        end = x2 - xadj, -y2 + yadj
        line = visual.Line(self.win, start, end,
                           units="pix", lineColor="white")
        line.draw()

    def set_image_palette(self, r, g, b):

        rgb = np.column_stack([r, g, b]).astype(np.float)
        self.rgb_palette = rgb / 255


class CalibrationTarget(object):

    def __init__(self, win, color):

        self.win = win
        self.monitor = win.monitor
        self.center = np.divide(win.size, 2.0)
        self.stims = [
            Point(win, pos=(0, 0), radius=.4, color=color),
            Point(win, pos=(0, 0), radius=.05, color=win.color),
        ]

    def set_pos_pixels(self, pos):

        pos = pix2deg(np.subtract(pos, self.center), self.monitor)
        for stim in self.stims:
            stim.dot.pos = pos

    def draw(self):
        for stim in self.stims:
            stim.draw()
