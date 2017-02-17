import time
import json
import Queue as queue
import numpy as np
from visigoth import experiment, clientserver


if __name__ == "__main__":

    exp = experiment.Experiment()
    exp.initialize_server()

    while True:

        x, y = np.random.randn(2)
        data = dict(gaze=(x, y),
                    stims=[])
        exp.screen_q.put(json.dumps(data))
        time.sleep(1)
