import numpy as np
import pandas as pd

from visigoth.tools import AcquireFixation, AcquireTarget, flexible_values
from visigoth.stimuli import Point, Points, Pattern, GaussianNoise 


def create_stimuli(exp):

    # Fixation point
    fix = Point(exp.win, exp.p.fix_radius)

    # Saccade targets
    targets = Points(exp.win, exp.p.target_pos, exp.p.target_radius)

    # Gaussian noise fields
    noise_kws = dict(mask="circle",
                     size=exp.p.stim_size,
                     pix_per_deg=exp.p.noise_resolution)

    noise_l = GaussianNoise(exp.win,
                            pos=exp.p.stim_pos[0],
                            **noise_kws)

    noise_r = GaussianNoise(exp.win,
                            pos=exp.p.stim_pos[1],
                            **noise_kws)

    # Average of multiple sinusoidal grating stimulus
    pattern = Pattern(exp.win,
                      n=exp.p.stim_pattern_n,
                      elementTex=exp.p.stim_tex,
                      elementMask=exp.p.stim_mask,
                      sizes=exp.p.stim_size,
                      sfs=exp.p.stim_sf,
                      pos=(0, 0)
                      )

    return dict(fix=fix, targets=targets, pattern=pattern,
                noise_l=noise_l, noise_r=noise_r)


def generate_trials(exp):

    for t in range(1, exp.p.n_trials + 1):

        iti = flexible_values(exp.p.wait_iti)

        pattern_contrast = flexible_values(exp.p.pattern_contrast)
        pattern_side = flexible_values([0, 1])

        noise_frames = exp.p.noise_hz / exp.p.wait_stim
        pattern_frame = flexible_values(range(1, noise_frames + 1))

        noise_contrast = flexible_values(exp.p.noise_contrast)
        noise_opacity = flexible_values(exp.p.noise_opacity)

        trial_info = dict(

            subject=exp.p.subject,
            session=exp.p.date,
            run=exp.p.run,
            trial=t,

            iti=iti,

            noise_contrast=noise_contrast,
            noise_opacity=noise_opacity,

            pattern_contrast=pattern_contrast,
            pattern_side=pattern_side,
            pattern_frame=pattern_frame,

            target=pattern_side,

            responded=False,
            response=np.nan,
            correct=np.nan,
            rt=np.nan,
            result=np.nan,

        )

        yield pd.Series(trial_info, dtype=np.object)


def run_trial(exp, info):

    # Update stimuli to trial values
    exp.s.pattern.pos = exp.p.stim_pos[info.pattern_side]
    exp.s.pattern.contrast = info.pattern_contrast
    exp.s.pattern.randomize_phases()

    exp.s.noise_l.contrast = info.noise_contrast
    exp.s.noise_r.contrast = info.noise_contrast
    exp.s.noise_l.opacity = info.noise_opacity
    exp.s.noise_r.opacity = info.noise_opacity
    exp.s.noise_l.update()
    exp.s.noise_r.update()

    # Inter-trial interval
    exp.s.fix.color = exp.p.fix_iti_color
    exp.wait_until(exp.iti_end, draw="fix", iti_duration=info.iti)

    # Beginning of trial
    exp.s.fix.color = exp.p.fix_ready_color
    res = exp.wait_until(AcquireFixation(exp),
                         timeout=exp.p.wait_fix,
                         draw="fix")

    if res is None:
        info["result"] = "nofix"
        exp.auditory_feedback("nofix")
        return info

    # Pre-stimulus fixation
    exp.s.fix.color = exp.p.fix_trial_color
    exp.wait_until(timeout=exp.p.wait_prestim, draw=["fix", "targets"])

    # Stimulus event
    noise_frame = 0
    for i in exp.frame_range(seconds=exp.p.wait_stim):
        if not i % (exp.win.framerate / exp.p.noise_hz):
            exp.s.noise_l.update()
            exp.s.noise_r.update()
            noise_frame += 1
        stims = ["noise_l", "noise_r", "fix", "targets"]
        if noise_frame == info.pattern_frame:
            stims = ["pattern"] + stims
        exp.draw(stims, flip=True)

    # Collect eye response
    res = exp.wait_until(AcquireTarget(exp),
                         exp.p.wait_resp,
                         draw="targets")

    # TODO all of this logic should happen somewhere else
    if res is None:
        result = "nochoice"
    else:
        _, response = res
        if isinstance(response, int):
            correct = response == info.target
            result = "correct" if correct else "wrong"
            info["correct"] = correct
            info["response"] = response
            info["responded"] = True
        else:
            result = "nochoice"

    exp.auditory_feedback(result)
    info["result"] = result

    # Perpate for inter-trial interval
    exp.s.fix.color = exp.p.fix_iti_color
    exp.draw("fix", flip=True)

    return info
