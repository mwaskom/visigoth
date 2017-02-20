
import json
import socket
import Queue as queue

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.colors import rgb2hex

import numpy as np
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

        self.poll_dur = 50
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

        try:
            screen_data = json.loads(self.screen_q.get(block=False))
            self.gaze_app.update_screen(screen_data)
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
                                  #linestyle="--",
                                  edgecolor=".3",
                                  animated=True),
            gaze=plt.Circle((0, 0),
                            radius=.3,
                            facecolor="b",
                            linewidth=0,
                            animated=True)
            )

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
        # TODO

        # Draw stimuli on the screen
        self.fig.canvas.restore_region(self.axes_background)

        self.ax.draw_artist(self.plot_objects["gaze"])
        for stim in screen_data["stims"]:
            self.ax.draw_artist(self.plot_objects[stim])
        if "fix" in screen_data["stims"]:
            self.ax.draw_artist(self.plot_objects["fix_window"])

        self.screen_canvas.blit(self.ax.bbox)

    def update_params(self):

        pass

    def reset_params(self):

        pass


class TrialApp(object):

    def __init__(self, remote_app):

        self.remote_app = remote_app

        fig, axes = self.initialize_figure()
        fig_canvas = FigureCanvasQTAgg(fig)
        fig_canvas.setParent(remote_app.main_frame)

        vbox = QVBoxLayout()
        vbox.addWidget(fig_canvas)

        self.layout = vbox

    def initialize_figure(self):

        fig = Figure((5, 5), dpi=100, facecolor="white")
        axes = [fig.add_subplot(3, 1, i) for i in range(1, 4)]
        return fig, axes


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
