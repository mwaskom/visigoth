
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

        self.poll_dur = 50

        self.client = None

        self.initialize_main_frame()

    def initialize_client(self):

        try:
            self.client = clientserver.SocketClientThread(self)
        except socket.error:
            pass

    def initialize_main_frame(self):

        self.main_frame = QWidget()

        gaze_app = GazeApp(self)

        trial_fig = self.initialize_trial_figure()
        trial_canvas = FigureCanvasQTAgg(trial_fig)
        trial_canvas.setParent(self.main_frame)

        trial_vbox = QVBoxLayout()
        trial_vbox.addWidget(trial_canvas)

        main_hbox = QHBoxLayout()
        main_hbox.addLayout(gaze_app.layout)
        main_hbox.addLayout(trial_vbox)

        self.main_frame.setLayout(main_hbox)
        self.setCentralWidget(self.main_frame)

    def initialize_trial_figure(self):

        fig = Figure((5, 5), dpi=100, facecolor="white")
        ax = fig.add_subplot(111)
        return fig


class GazeApp(object):

    def __init__(self, remote_app):

        self.remote_app = remote_app

        fig, ax = self.initialize_figure()
        self.fig_canvas = FigureCanvasQTAgg(fig)
        self.fig_canvas.setParent(remote_app.main_frame)

        update_button = QPushButton("Update")
        update_button.clicked.connect(self.update_params)
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_params)

        self.buttons = Bunch(update=update_button,
                             reset=reset_button)

        self.sliders = Bunch(
            x_offset=ParamSlider("x offset", 0, (-4, 4)),
            y_offset=ParamSlider("y offset", 0, (-4, 4)),
            fix_window=ParamSlider("fix window", 2.5, (0, 5))
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
        vbox.addWidget(self.fig_canvas)
        vbox.addLayout(controls)

        self.layout = vbox

    def update_params(self):

        pass

    def reset_params(self):

        pass


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
        value = self.slider.value * self.res
        self.label.setText(self.label_template.format(value))
