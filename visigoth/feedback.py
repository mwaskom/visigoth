# TODO Psychopy 1.85 has improved sound capability -- need to look into that
import os
from psychopy import sound


class AuditoryFeedback(object):

    def __init__(self, play_sounds=True, correct="ding", wrong="signon",
                 nochoice="click", fixbreak="click", nofix="secalert"):

        self.play_sounds = play_sounds
        if not play_sounds:
            return
        sound_dir = os.path.join(os.path.dirname(__file__), "sounds")

        sound_name_dict = dict(correct=correct,
                               wrong=wrong,
                               nochoice=nochoice,
                               fixbreak=fixbreak,
                               nofix=nofix)
        sound_dict = {}
        for event, sound_type in sound_name_dict.items():
            if sound is None:
                sound_dict[event] = None
            else:
                fname = os.path.join(sound_dir, sound_type + ".wav")
                sound_obj = sound.Sound(fname)
                sound_dict[event] = sound_obj
        self.sound_dict = sound_dict

    def __call__(self, event):

        if self.play_sounds:
            sound_obj = self.sound_dict[event]
            if sound_obj is not None:
                sound_obj.play()
