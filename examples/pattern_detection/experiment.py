import numpy as np
import pandas as pd

from visigoth.tools import AcquireFixation, AcquireTarget, flexible_values
from visigoth.stimuli import Point, Points, Pattern, GaussianNoise


def create_stimuli(exp):

    # Fixation point
    fix = Point(exp.win,
                exp.p.fix_radius,
                exp.p.fix_iti_color)

    # Saccade targets
    targets = Points(exp.win,
                     exp.p.target_pos,
                     exp.p.target_radius,
                     exp.p.target_color)

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

        # TODO let's define a central way to generate fields we
        # usually/always wany in the trial info

        trial_info = dict(

            subject=exp.p.subject,
            session=exp.p.session,
            date=exp.p.date,
            run=exp.p.run,
            trial=t,

            iti=iti,

            noise_contrast=noise_contrast,

            pattern_contrast=pattern_contrast,
            pattern_side=pattern_side,
            pattern_frame=pattern_frame,

            target=pattern_side,

            dropped_frames=np.nan,

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
        exp.sounds.nofix.play()
        return info

    # Pre-stimulus fixation
    exp.s.fix.color = exp.p.fix_trial_color
    exp.wait_until(timeout=exp.p.wait_prestim, draw=["fix", "targets"])

    # Stimulus event
    noise_frame = 0
    noise_modulus = exp.win.framerate / exp.p.noise_hz
    frame_generator = exp.frame_range(seconds=exp.p.wait_stim,
                                      yield_skipped=True)

    for i, skipped in frame_generator:
        update_noise = (not i % noise_modulus
                        or not np.mod(skipped, noise_modulus).all())
        if update_noise:
            exp.s.noise_l.update()
            exp.s.noise_r.update()
            noise_frame += 1
        stims = ["noise_l", "noise_r", "fix", "targets"]
        if noise_frame == info.pattern_frame:
            stims = ["pattern"] + stims
        if not exp.check_fixation(allow_blinks=True):
            # TODO write a function to do this
            exp.sounds.fixbreak.play()
            exp.flicker("fix")
            info["result"] = "fixbreak"
            return info
        exp.draw(stims)

    info["dropped_frames"] = exp.win.nDroppedFrames

    # Collect eye response
    res = exp.wait_until(AcquireTarget(exp, info.target),
                         exp.p.wait_resp,
                         draw="targets")

    # Handle eye response
    if res is None:
        # TODO wouldn't need to do this if not responding fast enough
        # was handled within `AcquireTarget` instead of `wait_until`
        # shoudld reconsider that...
        info["result"] = "nochoice"
    else:
        info.update(pd.Series(res))

    # Give feedback
    exp.sounds[info.result].play()
    exp.show_feedback("targets", info.result, info.response)
    exp.wait_until(timeout=exp.p.wait_feedback, draw=["targets"])
    exp.s.targets.color = exp.p.target_color

    # Prepare for inter-trial interval
    exp.s.fix.color = exp.p.fix_iti_color
    exp.draw("fix")

    return info
