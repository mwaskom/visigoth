

class Experiment(object):

    def __init__(self):

        self.trial_data = [] 

        # TODO maybe don't do this all in the constructor?
        try:

            self.load_params()
            self.initialize_server()
            self.initialize_eyetracker()
            self.open_window()
            self.create_stimuli()
            self.run()

        finally:

            self.save_data()
            self.shutdown_server()
            self.shutdown_eyetracker()
            self.close_window()

    def run(self):

        # TODO handle clocks, eyetracker, etc.

        for trial_info in self.generate_trials():

            trial_info = self.run_trial(trial_info)
            self.trial_data.append(trial_info)
            self.update_client(trial_info)

    def create_stimuli(self):
        """Initialize study-specific stimulus objects.

        This method must be defined for each study.

        It should return a dictionary that maps stimulus names to the objects
        themselves. The objects can be anything that follow the basic stimulus
        API--namely, they need to define a ``draw`` method. They will end up
        in the Experiment.s namespace. Some stimuli (e.g. the fixation point)
        have default objects but can be overloaded here.

        """
        raise NotImplementedError

    def generate_trials(self):
        """Generator that yields data for each trial.

        This method must be defined for each study.

        It should be written as a generator, which allows flexibility as to
        whether the trial information will be fully defined before the run
        or on the fly.

        It should yield an object that provides trial-specific parameters.
        This will typically be a Pandas Series, but other datatypes are fine
        as long as the ``run_trial`` method knows how to handle it.

        The generator is iterated between each trial, so if it is going to do
        substantial computation, you will need to be mindful to specify a
        sufficient ITI distribution.

        """
        raise NotImplementedError

    def run_trial(self, trial_info):
        """Execute an individual trial of the experiment.

        This method must be defined for each study.

        It should accept a trial_info argument and return the object, possibly
        with updated values or additional data. This can be any type of object
        but it should be coordinated with the other methods. Specifically, the
        handling of the input should correspond with what is yielded by the
        ``generate_trials`` method, and the output should be something that the
        ``update_client`` and ``save_data`` methods knows how to handle. It is
        easiest for this to be a pandas Series, so that those methods to not
        need to be overloaded, but this is not strictly required to allow for
        more complicated designs.

        """
        raise NotImplementedError

    def update_client(self, trial_info):

        raise NotImplementedError

    def save_data(self):

        raise NotImplementedError
