
base = dict(

    display_name="macbook-air",
    display_luminance=50,

    fix_radius=.15,
    fix_window=2,

    fix_iti_color=None,

    target_pos=[(-10, 0), (10, 0)],
    target_radius=.25,
    target_window=3,

    stim_pos=[(-5, 0), (5, 0)],
    stim_sf=3,
    stim_tex="sin",
    stim_mask="raisedCos",
    stim_size=6,
    stim_pattern_n=8,

    contrast_gen=[.04, .07, .09, .10, .11, .13, .16],

    monitor_eye=True,

    eye_fixation=True,
    eye_response=True,

    eye_fix_radius=2,
    eye_target_wait=.5,
    eye_target_hold=.3,

    n_trials=200,

    wait_iti=1,
    wait_fix=5,
    wait_prestim=.5,
    wait_stim=.2,
    wait_resp=2,
    wait_feedback=.5,

)
