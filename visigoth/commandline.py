import argparse


def define_parser(script):

    if script == "visigoth":
        return define_experiment_parser()
    elif script == "visigoth-remote":
        return define_remote_parser()


def define_experiment_parser():

    parser = argparse.ArgumentParser()

    parser.add_argument("study_dir", default=".", nargs="?")
    parser.add_argument("-p", "--paramset")
    parser.add_argument("-s", "--subject", default="test")
    parser.add_argument("--session")
    parser.add_argument("--mouse", action="store_true", dest="eye_simulate")
    parser.add_argument("-r", "--run", type=int, default=1)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--display_name")
    parser.add_argument("--nosave", action="store_false", dest="save_data")

    return parser


def define_remote_parser():

    parser = argparse.ArgumentParser()

    parser.add_argument("study_dir", default=".", nargs="?")
    parser.add_argument("--host", default="192.168.100.1")
    parser.add_argument("--localhost", action="store_true")

    return parser
