import numpy as np
import pandas as pd

from psychopy import core

from visigoth.tools import AcquireFixation, AcquireTarget, flexible_values
from visigoth.stimuli import Point, Points, Grating


def create_stimuli(exp):

    fix = Point(exp.win, exp.p.fix_pos, exp.p.fix_radius)
    targets = Points(exp.win, exp.p.target_pos, exp.p.target_radius)
    grating = Grating(exp.win,
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
        iti = flexible_values(exp.p.wait_iti)
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

        yield pd.Series(trial_info, dtype=np.object)


def run_trial(exp, info):

    exp.s.fix.color = exp.p.fix_iti_color
    exp.draw("fix")
    exp.win.flip()
    core.wait(info.iti)

    exp.s.fix.color = exp.p.fix_ready_color
    res = exp.wait_until(AcquireFixation(exp), timeout=5, draw="fix")
    if res is None:
        info["result"] = "nofix"
        return info

    exp.s.fix.color = exp.p.fix_trial_color
    exp.draw(["fix", "targets"])
    exp.win.flip()
    core.wait(exp.p.wait_prestim)

    phase_shift = info.motion * exp.p.stim_speed / exp.win.framerate
    for _ in exp.frame_range(seconds=exp.p.wait_stim):

        exp.s.grating.phase += phase_shift
        exp.draw(["grating", "fix", "targets"])
        exp.win.flip()

    exp.draw("targets")
    exp.wait_until(AcquireTarget(exp), draw="targets")

    exp.s.fix.color = exp.p.fix_iti_color
    exp.draw("fix")
    exp.win.flip()

    return info
