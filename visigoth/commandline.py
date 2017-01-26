import argparse

def define_parser(script):

    if script == "visigoth":
        return define_visigoth_parser()


def define_visigoth_parser():

    parser = argparse.ArgumentParser()

    parser.add_argument("study_dir", default=".")
    parser.add_argument("-paramset")
    parser.add_argument("-subject", default="test")
    parser.add_argument("-run", type=int, default=1)
    parser.add_argument("-nosave", action="store_false", dest="save_data")
    parser.add_argument("-debug", action="store_true")

    return parser
