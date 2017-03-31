"""PyQT GUI offering remote monitoring and control of experiment execution."""
import json
import socket
import Queue as queue

import numpy as np
import pandas as pd
import matplotlib as mpl
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (QMainWindow, QWidget,
                             QSlider, QPushButton, QLabel,
                             QVBoxLayout, QHBoxLayout)

from . import clientserver
from .ext.bunch import Bunch


class RemoteApp(QMainWindow):

    def __init__(self, host):

        QMainWindow.__init__(self, None)
        self.setWindowTitle("Visigoth Remote")

        self.screen_q = queue.Queue()
        self.param_q = queue.Queue()
        self.trial_q = queue.Queue()
        self.cmd_q = queue.Queue()

        self.poll_dur = 20

        self.host = host
        self.client = None

        # Intialize the parameters and eyeopts
        # This is just one example of how this division is unclear
        # but it gets more obvious later
        self.p = Bunch()
        self.eyeopt = Bunch(x_offset=0, y_offset=0, fix_window=3)
        self.local_eyeopt = Bunch(x_offset=0, y_offset=0, fix_window=3)

        self.main_frame = QWidget()
        self.gaze_app = GazeApp(self)
        self.trial_app = TrialApp(self)
        self.initialize_layout()
        self.initialize_timers()

    def poll(self):

        # Ensure connection to the server
        if self.client is None:
            self.initialize_client()

        # Get the most recent gaze position
        # Previously we showed a "trail" of gaze positions rather
        # than just one, which looked pretty and is more informative.
        # It is a bit tricker so I am skipping for the moment to get things
        # running, but worth revisiting.
        screen_data = None
        while True:
            try:
                screen_data = json.loads(self.screen_q.get(block=False))
            except queue.Empty:
                break
        if screen_data is not None:
            self.gaze_app.update_screen(screen_data)

        try:
            trial_data = self.trial_q.get(block=False)
            self.trial_app.update_figure(trial_data)
        except queue.Empty:
            pass

        # Update the GazeApp GUI elementes
        self.gaze_app.update_gui()

    def initialize_client(self):

        try:

            # Boot up the client thread
            self.client = clientserver.SocketClientThread(self)
            self.client.start()

            # Ask the server for the params it is currently using
            self.cmd_q.put(self.client.PARAM_REQUEST)
            params = json.loads(self.param_q.get())
            self.p.update(params)

            # Update our understanding of the fix window size
            self.eyeopt["fix_window"] = self.p.fix_window
            self.local_eyeopt["fix_window"] = self.p.fix_window
            self.gaze_app.sliders["fix_window"].value = self.p.fix_window

            # Initialize the stimulus artists in the gaze window
            # This had to be deferred util we knew the active params
            self.gaze_app.initialize_stim_artists()

        except socket.error:
            pass

    def initialize_layout(self):

        main_hbox = QHBoxLayout()
        main_hbox.addLayout(self.gaze_app.layout)
        main_hbox.addLayout(self.trial_app.layout)

        self.main_frame.setLayout(main_hbox)
        self.setCentralWidget(self.main_frame)

    def initialize_timers(self):

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.poll)
        self.timer.start(self.poll_dur)


class GazeApp(object):
    """Component of the Remote GUI that monitors/controls eyetracking."""
    def __init__(self, remote_app):

        self.remote_app = remote_app
        self.p = remote_app.p
        self.eyeopt = remote_app.eyeopt
        self.local_eyeopt = remote_app.local_eyeopt

        fig, ax = self.initialize_figure()
        self.fig = fig
        self.ax = ax
        self.screen_canvas = FigureCanvasQTAgg(fig)
        self.screen_canvas.setParent(remote_app.main_frame)

        update_button = QPushButton("Update")
        update_button.clicked.connect(self.update_eyeopt)
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_eyeopt)

        self.buttons = Bunch(
            update=update_button,
            reset=reset_button
            )

        self.sliders = Bunch(
            x_offset=ParamSlider(self, "x offset", (-4, 4)),
            y_offset=ParamSlider(self, "y offset", (-4, 4)),
            fix_window=ParamSlider(self, "fix window", (0, 6))
            )

        self.initialize_layout()

    # ---- Initialization methods

    def initialize_figure(self):
        """Set up the basic aspects of the matplotlib screen figure."""
        fig = mpl.figure.Figure((5, 5), dpi=100, facecolor="white")

        ax = fig.add_subplot(111)
        ax.set(xlim=(-10, 10),
               ylim=(-10, 10),
               aspect="equal")

        ticks = np.linspace(-10, 10, 21)
        ax.set_xticks(ticks, minor=True)
        ax.set_yticks(ticks, minor=True)

        grid_kws = dict(which="minor", lw=.5, ls="-", c=".8")
        ax.xaxis.grid(True, **grid_kws)
        ax.yaxis.grid(True, **grid_kws)

        self.axes_background = None

        return fig, ax

    def initialize_stim_artists(self):
        """Set up the artists that represent stimuli and gaze location."""
        gaze = mpl.patches.Circle((0, 0),
                                  radius=.3,
                                  facecolor="b",
                                  linewidth=0,
                                  animated=True)

        fix = Bunch(
            point=mpl.patches.Circle((0, 0),
                                     radius=.15,
                                     facecolor="k",
                                     linewidth=0,
                                     animated=True),
            window=mpl.patches.Circle((0, 0),
                                      radius=self.eyeopt.fix_window,
                                      facecolor="none",
                                      linestyle="dashed",
                                      edgecolor=".3",
                                      animated=True)
            )

        targets = []
        if "target_pos" in self.p:
            for pos in self.p.target_pos:
                point = mpl.patches.Circle(pos,
                                           .3,
                                           facecolor="k",
                                           linewidth=0,
                                           animated=True)
                window = mpl.patches.Circle(pos,
                                            self.p.target_window,
                                            facecolor="none",
                                            linestyle="dashed",
                                            edgecolor=".3",
                                            animated=True)
                targets.extend([point, window])

        self.plot_objects = Bunch(fix=fix, gaze=gaze, targets=targets)
        self.plot_objects.update(self.create_stim_artists())

        for _, stim in self.plot_objects.items():
            self.add_artist(self.ax, stim)

    def initialize_layout(self):
        """Set up the basic layout of the PyQT GUI."""
        controls = QHBoxLayout()

        for key in ["x_offset", "y_offset", "fix_window"]:

            s = self.sliders[key]
            vbox = QVBoxLayout()
            vbox.addWidget(s.label)
            vbox.addWidget(s.slider)
            vbox.setAlignment(s.slider, Qt.AlignVCenter)
            controls.addLayout(vbox)

        vbox = QVBoxLayout()
        vbox.addWidget(self.buttons["update"])
        vbox.addWidget(self.buttons["reset"])
        controls.addLayout(vbox)

        vbox = QVBoxLayout()
        vbox.addWidget(self.screen_canvas)
        vbox.addLayout(controls)

        self.layout = vbox

    # ----- Study-specific functions

    def create_stim_artists(self):
        """Define additional matplotlib artists to represent stimuli.

        Returns
        -------
        stims : dict
            The keys in this dictionary should correspond to the server-side
            stimulus names (i.e. what you define in `create_stimuli`.
            The values should be either a single matplotlib artist, a list
            of artists, or a dict mapping arbitrary artist subcomponent
            names to artists.

        """
        return dict()

    # ----- Live GUI methods

    def add_artist(self, ax, obj):
        """Add either each artist in an iterable or a single artist."""
        if isinstance(obj, list):
            for artist in obj:
                ax.add_artist(artist)
        elif isinstance(obj, dict):
            for _, artist in obj.items():
                ax.add_artist(artist)
        else:
            ax.add_artist(obj)

    def draw_artist(self, ax, obj):
        """Draw either each artist in an iterable or a single artist."""
        if isinstance(obj, list):
            for artist in obj:
                ax.draw_artist(artist)
        elif isinstance(obj, dict):
            for _, artist in obj.items():
                ax.draw_artist(artist)
        else:
            ax.draw_artist(obj)

    def update_screen(self, screen_data):
        """Re-draw the figure to show current gaze and what's on the screen."""
        if self.axes_background is None:
            self.fig.canvas.draw()
            ax_bg = self.fig.canvas.copy_from_bbox(self.ax.bbox)
            self.axes_background = ax_bg

        # Update gaze position
        gaze = np.array(screen_data["gaze"])
        offsets = np.array([self.local_eyeopt["x_offset"],
                            self.local_eyeopt["y_offset"]])
        gaze += offsets
        self.plot_objects.gaze.center = gaze

        # Update fix window size
        self.plot_objects.fix.window.radius = self.local_eyeopt["fix_window"]

        # Draw stimuli on the screen
        self.fig.canvas.restore_region(self.axes_background)

        self.ax.draw_artist(self.plot_objects["gaze"])
        for stim, pos in screen_data["stims"].items():
            if stim in self.plot_objects:

                # TODO This lets us move stimulus objects around in the gaze
                # app, but it's limited to Psychopy objects with a `pos`
                # attribute and matplotlib objects with a `center` attribute.
                # It would be nice if this were more flexible, but it's not
                # trivial to link arbitrary psychopy attributes to arbitrary
                # matplotlib attributes. Maybe this mapping could be defined
                # somehow on our versions of the Psychopy objects?
                # Punting on this for now -- it seems to work ok and the
                # GazeApp display is intended to be pretty minimal anyway.
                if pos is not None:
                    self.plot_objects[stim].center = pos

                self.draw_artist(self.ax, self.plot_objects[stim])

        self.screen_canvas.blit(self.ax.bbox)

    def update_gui(self):
        """Sync the GUI elements with the current values."""
        for name, slider in self.sliders.items():
            if self.local_eyeopt[name] != self.eyeopt[name]:
                slider.label.setStyleSheet("color: red")
            else:
                slider.label.setStyleSheet("color: black")

    def update_eyeopt(self):
        """Method to trigger a parameter upload; triggered by a button."""
        self.remote_app.param_q.put(json.dumps(self.local_eyeopt))
        self.eyeopt.update(self.local_eyeopt)

    def reset_eyeopt(self):
        """Method to reset sliders to original value without uploading."""
        for name, obj in self.sliders.items():
            obj.value = self.eyeopt[name]
        self.local_eyeopt.update(self.eyeopt)


class TrialApp(object):
    """Component of the Remote GUI that shows data from each trial."""
    def __init__(self, remote_app):

        self.remote_app = remote_app

        fig, axes = self.initialize_figure()
        fig_canvas = FigureCanvasQTAgg(fig)
        fig_canvas.setParent(remote_app.main_frame)

        self.fig = fig
        self.axes = axes
        self.fig_canvas = fig_canvas

        self.trial_data = []

        vbox = QVBoxLayout()
        vbox.addWidget(fig_canvas)

        self.layout = vbox

    # ---- Study-specific methods

    # Both of these methods can be overloaded by defining a remote.py
    # module in your study directory. The default is to show a simple
    # summary of when the subject responded, their accuracy, and their RT.

    # However, note that the remote.py file should define
    # `initialize_trial_figure` and `update_trial_figure`, not the names here.

    def initialize_figure(self):
        """Set up the figure and axes for trial data.

        This method can be overloaded in a study-specific remote.py file
        if you want a more complicated figure than this basic example.

        """
        # Note that we do not use the matplotlib.pyplot function, but
        # rather create the Figure object directly.
        fig = mpl.figure.Figure((5, 5), dpi=100, facecolor="white")
        axes = [fig.add_subplot(3, 1, i) for i in range(1, 4)]

        axes[0].set(ylim=(-.1, 1.1),
                    yticks=[0, 1],
                    yticklabels=["No", "Yes"],
                    ylabel="Responded")

        axes[1].set(ylim=(-.1, 1.1),
                    yticks=[0, 1],
                    yticklabels=["No", "Yes"],
                    ylabel="Correct")

        axes[2].set(ylim=(0, None),
                    xlabel="RT (s)")

        fig.subplots_adjust(.15, .125, .95, .95)

        return fig, axes

    def update_figure(self, trial_data):
        """Change the trial data figure with data from a new trial.

        This method can be overloaded in a study-specific remote.py file
        if you want a more complicated figure than this basic example.

        Parameters
        ----------
        trial_data : serialized object
            The data has whatever format is defined in the server-side
            `Experiment.serialize_trial_info` method. By default this is
            a pandas.Series in json, but it can be made study specific
            if you need a more complex representation of each trial's data.

        """
        # Note that we need to handle deserialization here
        # This allows support for study-specific formats of trial_data.
        # The easiest thing to do is to have it be a Pandas Series.
        trial_data = pd.read_json(trial_data, typ="series")

        # Create a new full dataset
        self.trial_data.append(trial_data)
        trial_df = pd.DataFrame(self.trial_data)

        # Get direct references to the different axes
        # Note dependence on how the figure is specified in the
        # `initialize_figure` method.
        resp_ax, cor_ax, rt_ax = self.axes

        # We are taking the approach of creating new artists on each trial,
        # drawing them, then removing them before adding the next trial's data.
        # Another approach would be to keep around references to the artists
        # and update their data using the appropriate matplotlib methods.

        # Draw valid and invalid responses
        resp_line, = resp_ax.plot(trial_df.trial, trial_df.responded, "ko")
        resp_ax.set(xlim=(.5, trial_df.trial.max() + .5))

        # Draw correct and incorrect responses
        cor_line, = cor_ax.plot(trial_df.trial, trial_df.correct, "ko")
        cor_ax.set(xlim=(.5, trial_df.trial.max() + .5))

        # Draw a histogram of RTs
        bins = np.arange(0, 5.2, .2)
        heights, bins = np.histogram(trial_df.rt.dropna(), bins)
        rt_bars = rt_ax.bar(bins[:-1], heights, .2)
        rt_ax.set(ylim=(0, heights.max() + 1))

        # Draw the canvas to show the new data
        self.fig_canvas.draw()

        # By removing the stimulus artists after drawing the canvas,
        # we are in effect clearing before drawing the new data on
        # the *next* trial.
        resp_line.remove()
        cor_line.remove()
        rt_bars.remove()


class ParamSlider(object):
    """Simple wrapper around a PyQT slider object, since we have a few."""
    def __init__(self, gaze_app, name, range,
                 res=.1, label_fmt="{:.1f}"):

        self.gaze_app = gaze_app
        self.name = name
        self.key = name.replace(" ", "_")

        self.res = res
        self.label_template = name + ": " + label_fmt

        start_val = gaze_app.local_eyeopt[self.key]

        self.label = QLabel(self.label_template.format(start_val))
        self.slider = slider = QSlider(Qt.Horizontal)

        slider_range = range[0] / res, range[1] / res
        slider.setRange(*slider_range)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTracking(True)
        slider.setValue(int(start_val / res))

        slider.valueChanged.connect(self.update)

    def update(self):
        """React to a change in slider position."""
        value = self.slider.value() * self.res
        self.label.setText(self.label_template.format(value))
        self.gaze_app.local_eyeopt[self.key] = value

    @property
    def value(self):
        return self.slider.value() * self.res

    @value.setter
    def value(self, val):
        self.slider.setValue(int(val / self.res))
        self.label.setText(self.label_template.format(val))
