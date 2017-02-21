import argparse


def define_parser(script):

    if script == "visigoth":
        return define_experiment_parser()
    elif script == "visigoth-remote":
        return define_remote_parser()


def define_experiment_parser():

    parser = argparse.ArgumentParser()

    parser.add_argument("study_dir", default=".", nargs="?")
    parser.add_argument("-paramset")
    parser.add_argument("-subject", default="test")
    parser.add_argument("-run", type=int, default=1)
    parser.add_argument("-nosave", action="store_false", dest="save_data")
    parser.add_argument("-debug", action="store_true")

    return parser


def define_remote_parser():

    parser = argparse.ArgumentParser()

    parser.add_argument("study_dir", default=".", nargs="?")

    return parser
