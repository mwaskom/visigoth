"""Simple reaction time random dot motion experiment."""
import pandas as pd
from psychopy import core
from visigoth import AcquireFixation, AcquireTarget, flexible_values
from visigoth.stimuli import RandomDotMotion, Point, Points


def create_stimuli(exp):
    """Initialize the stimulus objects used in the experiment."""
    # Central fixation point
    fix = Point(exp.win,
                exp.p.fix_pos,
                exp.p.fix_radius,
                exp.p.fix_color)

    # Saccade targets
    targets = Points(exp.win,
                     exp.p.target_pos,
                     exp.p.target_radius,
                     exp.p.target_color)

    # Field of moving dots
    dots = RandomDotMotion(exp.win,
                           aperture=exp.p.aperture_size,
                           pos=exp.p.aperture_pos)

    return locals()


def generate_trials(exp):
    """Determine the parameters for each trial."""
    for _ in exp.trial_count(exp.p.n_trials):

        target = flexible_values(range(len(exp.p.dot_dir)))

        t_info = exp.trial_info(

            wait_iti=flexible_values(exp.p.wait_iti),
            wait_dots=flexible_values(exp.p.wait_dots),
            dot_coh=flexible_values(exp.p.dot_coh),
            dot_dir=exp.p.dot_dir[target],
            target=target,

        )

        yield t_info


def run_trial(exp, info):
    """Execute the events on a single trial."""
    # Inter-trial interval
    exp.wait_until(exp.iti_end, iti_duration=info.wait_iti)

    # Wait for trial onset
    res = exp.wait_until(AcquireFixation(exp),
                         timeout=exp.p.wait_fix,
                         draw="fix")

    if res is None:
        info["result"] = "nofix"
        exp.sounds.nofix.play()
        return info

    # Wait before showing the dots
    exp.wait_until(timeout=info.wait_dots, draw=["fix", "targets"])

    # Initialize a clock to get RT
    rt_clock = core.Clock()

    # Draw each frame of the stimulus
    for i in exp.frame_range(seconds=exp.p.wait_resp):

        # Displace the dots with specified coherent motion
        exp.s.dots.update(info.dot_dir, info.dot_coh)

        # Draw the dots on the screen
        exp.draw(["fix", "targets", "dots"])

        if not exp.check_fixation():

            # Use time of first fixation loss as rough estimate of RT
            rt = rt_clock.getTime()

            # Determine which target was chosen, if any
            res = exp.wait_until(AcquireTarget(exp, info.target),
                                 draw="targets")

            # End the dot epoch
            break

    else:
        # Dot stimulus timed out without broken fixation
        res = None

    # Handle the response
    if res is None:
        info["result"] = "fixbreak"
    else:
        info.update(pd.Series(res))

    # Inject the estimated RT into the results structure
    if info.responded:
        info["rt"] = rt

    # Give auditory and visual feedback
    exp.sounds[info.result].play()
    exp.show_feedback("targets", info.result, info.response)
    exp.wait_until(timeout=exp.p.wait_feedback, draw=["targets"])
    exp.s.targets.color = exp.p.target_color

    return info
