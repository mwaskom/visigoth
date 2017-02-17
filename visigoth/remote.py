
import socket
import Queue as queue

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.colors import rgb2hex

import numpy as np
import matplotlib.pyplot as plt

from PyQt4.QtCore import Qt, QTimer
from PyQt4.QtGui import (QApplication, QMainWindow, QDialog,
                         QWidget, QSlider, QPushButton, QLabel,
                         QVBoxLayout, QHBoxLayout)

from . import clientserver


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

        self.canvas = FigureCanvasQTAgg(fig)
        self.canvas.setParent(remote_app.main_frame)

        self.fix_label = QLabel("Fix window: 2.0")
        self.fix_slider = QSlider(Qt.Horizontal)
        self.fix_slider.setRange(0, 50)
        #self.fix_slider.setValue(int(self.current_params["fix_radius"] * 10))
        self.fix_slider.setTickPosition(QSlider.TicksBelow)
        self.fix_slider.setTracking(True)
        #self.fix_slider.valueChanged.connect(self.update_fix_radius)

        self.x_label = QLabel("x offset: 0.0")
        self.x_slider = QSlider(Qt.Horizontal)
        self.x_slider.setRange(-40, 40)
        #self.x_slider.setValue(int(self.current_params["x_offset"] * 10))
        self.x_slider.setTickPosition(QSlider.TicksBelow)
        self.x_slider.setTracking(True)
        #self.x_slider.valueChanged.connect(self.update_x_offset)

        self.y_label = QLabel("y offset: 0.0")
        self.y_slider = QSlider(Qt.Horizontal)
        self.y_slider.setRange(-40, 40)
        #self.y_slider.setValue(int(self.current_params["y_offset"] * 10))
        self.y_slider.setTickPosition(QSlider.TicksBelow)
        self.y_slider.setTracking(True)
        #self.y_slider.valueChanged.connect(self.update_y_offset)

        self.update_button = QPushButton("Update")
        #self.update_button.clicked.connect(self.update_params)

        self.reset_button = QPushButton("Reset")
        #self.reset_button.clicked.connect(self.reset_params)

        controls = QHBoxLayout()

        for (l, w) in [(self.fix_label, self.fix_slider),
                       (self.x_label, self.x_slider),
                       (self.y_label, self.y_slider)]:

            vbox = QVBoxLayout()
            vbox.addWidget(l)
            vbox.addWidget(w)
            vbox.setAlignment(w, Qt.AlignVCenter)
            controls.addLayout(vbox)

        vbox = QVBoxLayout()
        vbox.addWidget(self.update_button)
        vbox.addWidget(self.reset_button)
        controls.addLayout(vbox)

        vbox = QVBoxLayout()
        vbox.addWidget(self.canvas)
        vbox.addLayout(controls)

        self.layout = vbox
