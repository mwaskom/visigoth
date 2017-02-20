import time
import json
import numpy as np
from visigoth import experiment
from visigoth.ext.bunch import Bunch


if __name__ == "__main__":

    exp = experiment.Experiment()
    exp.initialize_server()
    exp.p = Bunch(x_offset=0, y_offset=0, fix_window=3)

    try:

        print ("Simulating eye data")
        xy = (0, 0)
        while True:

            if exp.server.connected:
                xy += np.random.randn(2) / 3
                signs = np.sign(xy)
                oob = np.abs(xy) > 5
                xy[oob] = (signs * 5)[oob]
                data = dict(gaze=tuple(xy),
                            stims=["fix"])
                exp.screen_q.put(json.dumps(data))
            time.sleep(.016)

    finally:
        exp.shutdown_server()
