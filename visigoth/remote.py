
import socket
import Queue as queue

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.colors import rgb2hex

import numpy as np
import matplotlib.pyplot as plt

from PyQt4.QtCore import Qt, QTimer
from PyQt4.QtGui import (QApplication, QMainWindow,
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

        gaze_fig = self.initialize_gaze_figure()
        trial_fig = self.initialize_trial_figure()

        gaze_canvas = FigureCanvasQTAgg(gaze_fig)
        trial_canvas = FigureCanvasQTAgg(trial_fig)

        gaze_canvas.setParent(self.main_frame)
        trial_canvas.setParent(self.main_frame)

        gaze_vbox = QVBoxLayout()
        gaze_vbox.addWidget(gaze_canvas)

        trial_vbox = QVBoxLayout()
        trial_vbox.addWidget(trial_canvas)

        main_hbox = QHBoxLayout()
        main_hbox.addLayout(gaze_vbox)
        main_hbox.addLayout(trial_vbox)

        self.main_frame.setLayout(main_hbox)
        self.setCentralWidget(self.main_frame)


    def initialize_gaze_figure(self):

        fig = Figure((5, 6))
        ax = fig.add_subplot(111)
        ax.set_aspect("equal")
        print fig.axes
        return fig

    def initialize_trial_figure(self):

        fig = Figure((6, 5))
        ax = fig.add_subplot(111)
        return fig
