base = dict(

    # Key for display parameters (in displays.yaml)
    display_name="mlw-mbpro",

    # Brightness of the background
    display_luminance=0,

    # Use eye tracking
    monitor_eye=True,

    # Require fixation to initiate trial
    eye_fixation=True,

    # Collect responses based on eye position
    eye_response=True,

    # Position of the two saccade targets
    target_pos=[(-10, 5), (10, 5)],

    # Unique dot coherence values
    dot_coh=[0, .016, .032, .064, .128, .256, .512],

    # Unique dot direction values (0 is rightward)
    dot_dir=[180, 0],

    # Central position of the dot aperture
    aperture_pos=(0, 5),

    # Size (in degrees) of the dot aperture
    aperture_size=10,

    # Duration to wait before showing the dots
    wait_dots=("truncexpon", (.5 - .2) / .1, .2, .1),

    # (Minimal) duration to wait between trial
    wait_iti=2,

    # Total number of trials to perform
    n_trials=50,

    # Goal value for choice accuracy
    perform_acc_target=.8,

    # Goal value for reaction time
    perform_rt_target=1,

)
