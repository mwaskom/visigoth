import numpy as np
import pandas as pd

from psychopy import core

from visigoth.tools import AcquireFixation, AcquireTarget, flexible_values
from visigoth.stimuli import Point, Points, Grating, Pattern


def create_stimuli(exp):

    fix = Point(exp.win, exp.p.fix_radius)
    targets = Points(exp.win, exp.p.target_pos, exp.p.target_radius)

    grating = Grating(exp.win,
                      sf=exp.p.stim_sf,
                      tex=exp.p.stim_tex,
                      mask=exp.p.stim_mask,
                      size=exp.p.stim_size,
                      pos=(0, 0),
                      ori=0
                      )

    pattern = Pattern(exp.win,
                      n=exp.p.stim_pattern_n,
                      elementTex=exp.p.stim_tex,
                      elementMask=exp.p.stim_mask,
                      sizes=exp.p.stim_size,
                      sfs=exp.p.stim_sf,
                      pos=(0, 0)
                      )

    return dict(fix=fix, targets=targets, grating=grating, pattern=pattern)


def generate_trials(exp):

    for t in range(1, exp.p.n_trials + 1):

        now = exp.clock.getTime()
        iti = flexible_values(exp.p.wait_iti)
        trial_time = now + iti

        g_side, p_side = np.random.permutation([0, 1])
        g_c, p_c = flexible_values(exp.p.contrast_gen, 2)
        target = g_side if g_c > p_c else p_side

        trial_info = dict(

            subject=exp.p.subject,
            session=exp.p.date,
            run=exp.p.run,
            trial=t,

            iti=iti,
            trial_time=trial_time,

            grating_side=g_side,
            pattern_side=p_side,

            grating_contrast=g_c,
            pattern_contrast=p_c,

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
    exp.draw("fix", flip=True)
    core.wait(info.iti)

    exp.s.fix.color = exp.p.fix_ready_color
    res = exp.wait_until(AcquireFixation(exp), timeout=5, draw="fix")
    if res is None:
        info["result"] = "nofix"
        return info

    exp.s.fix.color = exp.p.fix_trial_color
    exp.draw(["fix", "targets"], flip=True)
    exp.win.flip()

    exp.s.grating.pos = exp.p.stim_pos[info.grating_side]
    exp.s.pattern.pos = exp.p.stim_pos[info.pattern_side]

    exp.s.grating.contrast = info.grating_contrast
    exp.s.pattern.contrast = info.pattern_contrast

    for _ in exp.frame_range(seconds=exp.p.wait_stim):

        exp.draw(["grating", "pattern", "fix", "targets"], flip=True)

    exp.draw("targets")
    _, response = exp.wait_until(AcquireTarget(exp),
                                 exp.p.wait_resp,
                                 draw="targets")

    exp.s.fix.color = exp.p.fix_iti_color
    exp.draw("fix", flip=True)

    return info
