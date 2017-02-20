
import json
import socket
import Queue as queue

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.colors import rgb2hex

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from PyQt4.QtCore import Qt, QTimer
from PyQt4.QtGui import (QMainWindow, QWidget,
                         QSlider, QPushButton, QLabel,
                         QVBoxLayout, QHBoxLayout)

from . import clientserver
from .ext.bunch import Bunch


class RemoteApp(QMainWindow):

    def __init__(self, parent=None):

        QMainWindow.__init__(self, parent)
        self.setWindowTitle("Visigoth Remote")

        self.screen_q = queue.Queue()
        self.param_q = queue.Queue()
        self.trial_q = queue.Queue()
        self.cmd_q = queue.Queue()

        self.poll_dur = 20
        self.client = None

        self.p = Bunch(x_offset=0, y_offset=0, fix_window=2)

        self.main_frame = QWidget()
        self.gaze_app = GazeApp(self)
        self.trial_app = TrialApp(self)
        self.initialize_layout()
        self.initialize_timers()

    def poll(self):

        if self.client is None:
            self.initialize_client()

        # TODO previously we showed a "trail" of gaze positions rather
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

    def initialize_client(self):

        try:

            # Boot up the client thread
            self.client = clientserver.SocketClientThread(self)
            self.client.start()

            # Ask the server for the params it is currently using
            self.cmd_q.put(self.client.PARAM_REQUEST)
            params = json.loads(self.param_q.get())
            self.p.update(params)

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

    def __init__(self, remote_app):

        self.remote_app = remote_app
        self.p = remote_app.p

        fig, ax = self.initialize_figure()
        self.fig = fig
        self.ax = ax
        self.screen_canvas = FigureCanvasQTAgg(fig)
        self.screen_canvas.setParent(remote_app.main_frame)

        update_button = QPushButton("Update")
        update_button.clicked.connect(self.update_params)
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_params)

        self.buttons = Bunch(
            update=update_button,
            reset=reset_button
            )

        self.sliders = Bunch(
            x_offset=ParamSlider("x offset", self.p.x_offset, (-4, 4)),
            y_offset=ParamSlider("y offset", self.p.y_offset, (-4, 4)),
            fix_window=ParamSlider("fix window", self.p.fix_window, (0, 6))
            )

        self.initialize_layout()

    def initialize_figure(self):

        fig = Figure((5, 5), dpi=100, facecolor="white")

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

        self.plot_objects = Bunch(
            fix=plt.Circle((0, 0),
                           radius=.2,
                           facecolor="k",
                           linewidth=0,
                           animated=True),
            fix_window=plt.Circle((0, 0),
                                  radius=3,
                                  facecolor="none",
                                  linestyle="dashed",
                                  edgecolor=".3",
                                  animated=True),
            gaze=plt.Circle((0, 0),
                            radius=.3,
                            facecolor="b",
                            linewidth=0,
                            animated=True)
            )

        # TODO add study-specific stimulus artist definition here

        self.axes_background = None

        for _, stim in self.plot_objects.items():
            ax.add_artist(stim)

        return fig, ax

    def initialize_layout(self):

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

    def update_screen(self, screen_data):

        if self.axes_background is None:
            self.fig.canvas.draw()
            ax_bg = self.fig.canvas.copy_from_bbox(self.ax.bbox)
            self.axes_background = ax_bg

        # Update gaze position
        self.plot_objects.gaze.center = screen_data["gaze"]

        # Update fix window size
        self.plot_objects.fix_window.radius = self.sliders.fix_window.value

        # Draw stimuli on the screen
        self.fig.canvas.restore_region(self.axes_background)

        self.ax.draw_artist(self.plot_objects["gaze"])
        for stim in screen_data["stims"]:
            if stim in self.plot_objects:
                self.ax.draw_artist(self.plot_objects[stim])
        if "fix" in screen_data["stims"]:
            self.ax.draw_artist(self.plot_objects["fix_window"])

        self.screen_canvas.blit(self.ax.bbox)

    def update_params(self):

        gaze_params = ["x_offset", "y_offset", "fix_window"]
        new_params = {k: self.p[k] for k in gaze_params}
        self.remote_app.param_q.put(json.dumps(new_params))

    def reset_params(self):

        for name, obj in self.sliders.items():
            obj.slider.setValue(self.p[name] / obj.res)


class TrialApp(object):

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

    def initialize_figure(self):

        # TODO this is a method that it should be able to overlaod
        # in a study-specific remote.py file

        fig = Figure((5, 5), dpi=100, facecolor="white")
        axes = [fig.add_subplot(3, 1, i) for i in range(1, 4)]

        axes[0].set(ylim=(-.1, 1.1),
                    yticks=[0, 1],
                    yticklabels=["Yes", "No"],
                    ylabel="Responded")

        axes[1].set(ylim=(-.1, 1.1),
                    yticks=[0, 1],
                    yticklabels=["Yes", "No"],
                    ylabel="Correct")

        axes[2].set(ylim=(0, None),
                    xlabel="RT (s)")

        fig.subplots_adjust(.15, .125, .95, .95)

        return fig, axes

    def update_figure(self, trial_data):

        # TODO this is a method that it should be able to overlaod
        # in a study-specific remote.py file

        # TODO note that we need to handle deserialization here
        trial_data = pd.read_json(trial_data, typ="series")

        self.trial_data.append(trial_data)

        trial_df = pd.DataFrame(self.trial_data)

        resp_ax, cor_ax, rt_ax = self.axes

        resp_line, = resp_ax.plot(trial_df.trial, trial_df.responded, "ko")
        resp_ax.set(xlim=(.5, trial_df.trial.max() + .5))

        cor_line, = cor_ax.plot(trial_df.trial, trial_df.correct, "ko")
        cor_ax.set(xlim=(.5, trial_df.trial.max() + .5))

        bins = np.arange(0, 5.2, .2)
        heights, bins = np.histogram(trial_data.rt, bins)
        rt_bars = rt_ax.bar(bins[:-1], heights, .2)

        self.fig_canvas.draw()

        resp_line.remove()
        cor_line.remove()
        rt_bars.remove()

class ParamSlider(object):

    def __init__(self, name, start_val, range, res=.1, fmt="{:.1f}"):

        self.res = res
        self.fmt = fmt
        self.label_template = name + ": " + fmt

        self.label = QLabel(self.label_template.format(start_val))
        self.slider = slider = QSlider(Qt.Horizontal)

        slider_range = range[0] / res, range[1] / res
        slider.setRange(*slider_range)
        slider.setTickPosition(QSlider.TicksBelow)
        slider.setTracking(True)
        slider.setValue(int(start_val / res))

        slider.valueChanged.connect(self.update)

    def update(self):

        # TODO find best place to handle colors indicating changed values
        value = self.slider.value() * self.res
        self.label.setText(self.label_template.format(value))

    @property
    def value(self):
        return self.slider.value() * self.res
