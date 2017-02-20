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
        while True:

            x, y = np.random.randn(2)
            data = dict(gaze=(x, y),
                        stims=["fix"])
            exp.screen_q.put(json.dumps(data))
            time.sleep(1)


    finally:
        exp.shutdown_server()
