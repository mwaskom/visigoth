import argparse


def define_parser(script):

    if script == "visigoth":
        return define_experiment_parser()
    elif script == "visigoth-remote":
        return define_remote_parser()


def define_experiment_parser():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "study_dir", default=".", nargs="?",
        help="path to directory containing experiment and params modules"
    )
    parser.add_argument(
        "-p", "--paramset", help="name of params dictionary to load"
    )
    parser.add_argument(
        "-s", "--subject", default="test", help="identifier for subject",
    )
    parser.add_argument(
        "--session", help="identifier for experimental session",
    )
    parser.add_argument(
        "-r", "--run", type=int, default=1,
        help="identifier for run (block) within the session",
    )
    parser.add_argument(
        "--mouse", action="store_true", dest="eye_simulate",
        help="simulate eye position using mouse",
    )
    parser.add_argument(
        "--demo", action="store_true", help="run experiment in demo mode",
    )
    parser.add_argument(
        "--refresh_error", default=.5, type=float,
        help="maximum tolerable refresh rate error, in Hz",
    )
    parser.add_argument(
        "--display_name",
        help="load parameters for this display, overriding params module",
    )
    parser.add_argument(
        "--debug", action="store_true", help="activate global debugging mode",
    )
    parser.add_argument(
        "--nosave", action="store_false", dest="save_data",
        help="don't create any data record (for testing)",
    )

    return parser


def define_remote_parser():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "study_dir", default=".", nargs="?",
        help="path to directory containing remote module",
    )
    parser.add_argument(
        "--host", default="192.168.100.1", help="experiment server IP address"
    )
    parser.add_argument(
        "--localhost", action="store_true",
        help="connect to server at localhost",
    )
    parser.add_argument(
        "--notrials", action="store_false", dest="trial_app",
        help="only show eye-tracking panel, not trial information",
    )

    return parser
