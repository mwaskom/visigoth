import numpy as np
import pandas as pd

from visigoth.utils import flexible_values
from visigoth.stimuli import Point, Points, GratingStim


def create_stimuli(exp):

    fix = Point(exp.win, exp.p.fix_radius)
    targets = Points(exp.win, exp.p.target_pos, exp.p.target_radius)
    grating = GratingStim(exp.win,
                          sf=exp.p.stim_sf,
                          tex=exp.p.stim_tex,
                          mask=exp.p.stim_mask,
                          size=exp.p.stim_size,
                          contrast=exp.p.stim_contrast,
                          pos=(0, 0),
                          ori=0,
                          autoLog=False)

    return dict(fix=fix, targets=targets, grating=grating)


def generate_trials(exp):

    for t in range(1, exp.p.n_trials + 1):

        now = exp.clock.getTime()
        iti = flexible_values(exp.p.iti_dur)
        trial_time = now + iti

        motion = flexible_values([-1, 1])
        target = int(motion > 1)

        trial_info = dict(

            subject=exp.p.subject,
            session=exp.p.date,
            run=exp.p.run,
            trial=t,

            iti=iti,
            trial_time=trial_time,

            motion=motion,
            target=target,

            responded=False,
            response=np.nan,
            correct=np.nan,
            rt=np.nan,
            result=np.nan,

        )

        return pd.Series(trial_info, dtype=np.object)

def run_trial(exp, trial_info):

    pass
