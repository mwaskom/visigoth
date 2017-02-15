
base = dict(

    display_name="laptop",
    display_luminance=50,

    fix_radius=.15,
    fix_window=2,

    fix_iti_color=None,
    fix_ready_color=1,
    fix_trial_color=1,

    target_pos=[(-10, 0), (10, 0)],
    target_radius=.25,
    target_window=3,

    stim_pos=[(-5, 0), (5, 0)],
    stim_sf=3,
    stim_tex="sin",
    stim_mask="raisedCos",
    stim_size=6,
    stim_pattern_n=8,

    pattern_contrast=[0, .02, .04, .08, .16, .32],
    noise_contrast=[0, .1, .2, .4],
    noise_opacity=.5,
    noise_resolution=20,
    noise_hz=5,

    monitor_eye=True,
    eye_simulate=True,

    eye_fixation=True,
    eye_response=True,

    eye_fix_radius=2,
    eye_target_wait=.5,
    eye_target_hold=.3,

    n_trials=200,

    wait_iti=1,
    wait_fix=5,
    wait_prestim=.5,
    wait_stim=1,
    wait_resp=2,

)
